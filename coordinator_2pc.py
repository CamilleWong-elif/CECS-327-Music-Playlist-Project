import socket
import threading
import json
import time
from enum import Enum
from lamport_clock import LamportClock

class TransactionState(Enum):
    PREPARING = "preparing"
    COMMITTED = "committed"
    ABORTED = "aborted"

class TwoPhaseCommitCoordinator:
    def __init__(self, host='localhost', port=5002):
        self.host = host
        self.port = port
        self.participants = {}  # {client_id: (host, port)}
        self.transactions = {}  # {transaction_id: transaction_data}
        self.transaction_counter = 0
        self.lock = threading.Lock()
        self.server_socket = None
        self._stop = threading.Event()
        self.lamport_clock = LamportClock("COORDINATOR")
        
    def start(self):
        """Start the coordinator server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        print(f"[COORDINATOR] Running on {self.host}:{self.port}")
        
        def accept_loop():
            while not self._stop.is_set():
                try:
                    conn, addr = self.server_socket.accept()
                    threading.Thread(
                        target=self._handle_request,
                        args=(conn, addr),
                        daemon=True
                    ).start()
                except OSError:
                    break
                    
        threading.Thread(target=accept_loop, daemon=True).start()
        
    def register_participant(self, client_id, host, port):
        """Register a client as a participant in 2PC"""
        with self.lock:
            self.participants[client_id] = (host, port)
            print(f"[COORDINATOR] Registered participant: {client_id} at {host}:{port}")
            
    def _handle_request(self, conn, addr):
        """Handle incoming requests from clients"""
        with conn:
            data = conn.recv(4096).decode('utf-8')
            
            request = json.loads(data)
            request_type = request.get('type')
            
            # Update Lamport clock on receive
            if 'timestamp' in request:
                self.lamport_clock.update(request['timestamp'])
            
            if request_type == 'register':
                client_id = request['client_id']
                client_host = request['host']
                client_port = request['port']
                self.register_participant(client_id, client_host, client_port)
                
                timestamp = self.lamport_clock.increment()
                response = {'status': 'registered', 'timestamp': timestamp}
                
            elif request_type == 'transaction':
                # Start a new distributed transaction
                response = self._execute_transaction(request)
                
            else:
                timestamp = self.lamport_clock.increment()
                response = {'status': 'error', 'message': 'Unknown request type', 'timestamp': timestamp}
                
            conn.sendall(json.dumps(response).encode('utf-8'))
                
                    
    def _execute_transaction(self, request):
        """Execute a 2PC transaction with BEGIN, PREPARE, COMMIT/ABORT phases"""
        with self.lock:
            self.transaction_counter += 1
            transaction_id = f"txn_{self.transaction_counter}"
            
        operation = request['operation']  # 'add' or 'remove'
        song_id = request['song_id']
        initiator = request['client_id']
        
        # Increment clock for transaction start
        txn_timestamp = self.lamport_clock.increment()
        
        print(f"\n[COORDINATOR T={txn_timestamp}] ===== BEGIN TRANSACTION {transaction_id} =====")
        print(f"[COORDINATOR] Operation: {operation} song {song_id}")
        print(f"[COORDINATOR] Initiator: {initiator}")
        
        # Store transaction info
        self.transactions[transaction_id] = {
            'operation': operation,
            'song_id': song_id,
            'initiator': initiator,
            'timestamp': txn_timestamp,
            'state': TransactionState.PREPARING
        }
        
        # Get all participants (including initiator for consistency)
        with self.lock:
            participants = [
                (cid, host, port) 
                for cid, (host, port) in self.participants.items()
            ]
            
        if not participants:
            print(f"[COORDINATOR] No participants registered")
            timestamp = self.lamport_clock.increment()
            return {'status': 'aborted', 'transaction_id': transaction_id, 
                    'reason': 'no_participants', 'timestamp': timestamp}
            
        # PHASE 1: PREPARE (ask all nodes if they can commit)
        print(f"\n[COORDINATOR] ===== PHASE 1: PREPARE =====")
        prepare_votes = self._phase1_prepare(transaction_id, operation, song_id, participants)
        
        # Check if all voted YES
        all_yes = all(vote == 'yes' for vote in prepare_votes.values())
        
        if all_yes:
            # PHASE 2: COMMIT
            print(f"\n[COORDINATOR] All votes YES - ===== PHASE 2: COMMIT =====")
            self.transactions[transaction_id]['state'] = TransactionState.COMMITTED
            self._phase2_commit(transaction_id, operation, song_id, participants)
            
            timestamp = self.lamport_clock.increment()
            print(f"\n[COORDINATOR T={timestamp}] ===== TRANSACTION {transaction_id} COMMITTED =====\n")
            
            return {
                'status': 'committed',
                'transaction_id': transaction_id,
                'participants': list(prepare_votes.keys()),
                'timestamp': timestamp
            }
        else:
            # PHASE 2: ABORT
            print(f"\n[COORDINATOR] Some votes NO - ===== PHASE 2: ABORT =====")
            self.transactions[transaction_id]['state'] = TransactionState.ABORTED
            self._phase2_abort(transaction_id, participants)
            
            timestamp = self.lamport_clock.increment()
            print(f"\n[COORDINATOR T={timestamp}] ===== TRANSACTION {transaction_id} ABORTED =====\n")
            
            return {
                'status': 'aborted',
                'transaction_id': transaction_id,
                'votes': prepare_votes,
                'timestamp': timestamp
            }
            
    def _phase1_prepare(self, transaction_id, operation, song_id, participants):
        """Phase 1: Send PREPARE to all participants and collect votes"""
        votes = {}
        timestamp = self.lamport_clock.increment()
        
        for client_id, host, port in participants:
            try:
                vote = self._send_prepare(client_id, host, port, transaction_id, 
                                         operation, song_id, timestamp)
                votes[client_id] = vote
                print(f"[COORDINATOR] {client_id} voted: {vote}")
            except Exception as e:
                print(f"[COORDINATOR] {client_id} failed to respond: {e}")
                votes[client_id] = 'no'  # Failed response = NO vote
                
        return votes
        
    def _send_prepare(self, client_id, host, port, transaction_id, operation, song_id, timestamp):
        """Send PREPARE message to a participant"""
        message = {
            'phase': 'prepare',
            'transaction_id': transaction_id,
            'operation': operation,
            'song_id': song_id,
            'timestamp': timestamp
        }
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((host, port))
            s.sendall(json.dumps(message).encode('utf-8'))
            response = s.recv(1024).decode('utf-8')
            result = json.loads(response)
            
            # Update clock with response
            if 'timestamp' in result:
                self.lamport_clock.update(result['timestamp'])
                
            return result.get('vote', 'no')
            
    def _phase2_commit(self, transaction_id, operation, song_id, participants):
        """Phase 2: Send COMMIT to all participants"""
        timestamp = self.lamport_clock.increment()
        
        for client_id, host, port in participants:
            self._send_commit(client_id, host, port, transaction_id, 
                                operation, song_id, timestamp)
            print(f"[COORDINATOR] {client_id} committed")
                
    def _send_commit(self, client_id, host, port, transaction_id, operation, song_id, timestamp):
        """Send COMMIT message to a participant"""
        message = {
            'phase': 'commit',
            'transaction_id': transaction_id,
            'operation': operation,
            'song_id': song_id,
            'timestamp': timestamp
        }
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((host, port))
            s.sendall(json.dumps(message).encode('utf-8'))
            response = s.recv(1024).decode('utf-8')
            result = json.loads(response)
            
            # Update clock
            if 'timestamp' in result:
                self.lamport_clock.update(result['timestamp'])
            
    def _phase2_abort(self, transaction_id, participants):
        """Phase 2: Send ABORT to all participants"""
        timestamp = self.lamport_clock.increment()
        
        for client_id, host, port in participants:
            self._send_abort(client_id, host, port, transaction_id, timestamp)
            print(f"[COORDINATOR] {client_id} aborted")
        
                
    def _send_abort(self, client_id, host, port, transaction_id, timestamp):
        """Send ABORT message to a participant"""
        message = {
            'phase': 'abort',
            'transaction_id': transaction_id,
            'timestamp': timestamp
        }
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((host, port))
            s.sendall(json.dumps(message).encode('utf-8'))
            response = s.recv(1024).decode('utf-8')
            result = json.loads(response)
            
            # Update clock
            if 'timestamp' in result:
                self.lamport_clock.update(result['timestamp'])
            
    def stop(self):
        """Stop the coordinator"""
        self._stop.set()
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass