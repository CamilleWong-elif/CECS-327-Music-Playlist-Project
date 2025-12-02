import socket
import threading
import pika #RabbitMQ
import json  # timestamp msgs
from lamport_clock import LamportClock  # lamport clock

class Client:
    # M4: added node_id parameter
    def __init__(self, node_id, server_host="localhost", server_port=5001, 
                 fav_artist_list=None, broker_host="localhost",
                 coordinator_host="localhost", coordinator_port=5002,
                 participant_port=None):
        
        self.node_id = node_id                      # M4: unique client identifier
        self.playlist = []                          # Individual playlist
        self.temp_playlist = None                   # Temporary state during 2PC 
        self.lamport_clock = LamportClock(node_id)  # M4: added lamport clock
        self.subscription = []                      # list of fav artists client is subscribed to
        self.server_host = server_host
        self.server_port = server_port
        self.connection = None
        self.channel = None

        # 2PC coordinator connection 
        self.coordinator_host = coordinator_host
        self.coordinator_port = coordinator_port

        # Participant server for receiving 2PC messages
        self.participant_port = participant_port or (6000 + abs(hash(node_id)) % 1000)
        self.participant_socket = None
        self._stop = threading.Event()
        
        # Transaction log for recovery
        self.transaction_log = []
        self.log_lock = threading.Lock()

        for artist in fav_artist_list:
            self.subscription.append(artist) 

        # Start participant server for 2PC
        self._start_participant_server()
        
        # Register with coordinator
        self._register_with_coordinator()

    def song_request(self, input_song):
        """
        send a song request to the server using TCP sockets (IPC)
        """
        # M4: increment clock and create msg with timestamp
        timestamp = self.lamport_clock.increment()
        message = json.dumps({
            "song": input_song,
            "timestamp": timestamp,
            "node_id": self.node_id
        })
        print(f"[CLIENT {self.node_id}] Sending at T={timestamp}: {input_song}")
        
        # create TCP pocket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((self.server_host, self.server_port)) # connect to the server as localhost:5000
                s.sendall(message.encode("utf-8")) # send the song name
                response = s.recv(1024).decode("utf-8") # wait for the server to respond
                
                # M4: update clock with server's timestamp
                response_data = json.loads(response)
                new_time = self.lamport_clock.update(response_data["timestamp"])
                print(f"[CLIENT {self.node_id}] Response at T={new_time}: {response_data['message']}")

            except ConnectionRefusedError:
                print("ERRROR - could not connect to the server")
            except Exception as e:
                print(f"socket error: {e}")

    def receive_notification(self, fav_artist_list):
       """
       connect to RabbitMQ and subscribe to favorite artist updates
       """
       try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
            self.channel = self.connection.channel()

            # declare a topic exchange for artist notifications
            self.channel.exchange_declare(exchange="artist_update", exchange_type="topic")

            # create a temp queue for this client
            result = self.channel.queue_declare(queue="", exclusive=True)
            queue_name = result.method.queue

            # bind to the exchange for each fav artist
            for artist in self.subscription:
                routing_key = f"artist.{artist}"
                self.channel.queue_bind(exchange="artist_update", queue=queue_name, routing_key=routing_key)

            print(f"\n[CLIENT {self.node_id}] subscribed to updates from:", self.subscription, "\n")

            # start consuming messages
            # M4: update clock when receiving notifications
            def callback(ch, method, properties, body):
                notif = json.loads(body.decode('utf-8'))
                new_time = self.lamport_clock.update(notif.get("lamport_timestamp", 0))
                print(f"🎵 [NOTIFICATION {self.node_id}] T={new_time}: {notif['message']}\n")

            self.channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            print(f"[CLIENT {self.node_id}] waiting for notifs...")
            # run listener on a separate thread so the client can still send requests
            threading.Thread(target=self.channel.start_consuming, daemon=True).start()

       except pika.exceptions.AMQPConnectionError:
            print("Error: Could not connect to RabbitMQ. Is it running?")
       except Exception as e:
            print(f"RabbitMQ setup error: {e}")

    def _start_participant_server(self):
        """Start server to receive 2PC messages from coordinator"""
        def server_loop():
            self.participant_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.participant_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.participant_socket.bind(('localhost', self.participant_port))
            self.participant_socket.listen(5)
            print(f"[{self.node_id}] Participant server on port {self.participant_port}")
            
            while not self._stop.is_set():
                try:
                    conn, addr = self.participant_socket.accept()
                    threading.Thread(
                        target=self._handle_2pc_message,
                        args=(conn,),
                        daemon=True
                    ).start()
                except OSError:
                    break
                    
        threading.Thread(target=server_loop, daemon=True).start()
        
    def _register_with_coordinator(self):
        """Register this client with the 2PC coordinator"""
        try:
            timestamp = self.lamport_clock.increment()
            message = {
                'type': 'register',
                'client_id': self.node_id,
                'host': 'localhost',
                'port': self.participant_port,
                'timestamp': timestamp
            }
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5.0)
                s.connect((self.coordinator_host, self.coordinator_port))
                s.sendall(json.dumps(message).encode('utf-8'))
                response = s.recv(1024).decode('utf-8')
                result = json.loads(response)
                
                # Update clock
                if 'timestamp' in result:
                    self.lamport_clock.update(result['timestamp'])
                    
                print(f"[{self.node_id}] Registered with coordinator: {result['status']}")
        except Exception as e:
            print(f"[{self.node_id}] Failed to register with coordinator: {e}")
            
    def _handle_2pc_message(self, conn):
        """Handle 2PC phase messages from coordinator"""
        with conn:
            try:
                data = conn.recv(4096).decode('utf-8')
                if not data:
                    return
                    
                message = json.loads(data)
                phase = message['phase']
                transaction_id = message['transaction_id']
                
                # Update clock on receive
                if 'timestamp' in message:
                    self.lamport_clock.update(message['timestamp'])
                
                if phase == 'prepare':
                    response = self._handle_prepare(message)
                elif phase == 'commit':
                    response = self._handle_commit(message)
                elif phase == 'abort':
                    response = self._handle_abort(message)
                else:
                    response = {'status': 'error'}
                    
                conn.sendall(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                print(f"[{self.node_id}] Error handling 2PC message: {e}")
                
    def _handle_prepare(self, message):
        """Handle PREPARE phase - validate and prepare the operation"""
        transaction_id = message['transaction_id']
        operation = message['operation']
        song_id = message['song_id']
        
        timestamp = self.lamport_clock.increment()
        print(f"[{self.node_id} T={timestamp}] PREPARE: {operation} song {song_id}")
        
        # Save current state for potential rollback
        self.temp_playlist = self.playlist.copy()
        
        # Validate the operation and check for conflicts
        if operation == 'add':
            if song_id in self.temp_playlist:
                print(f"[{self.node_id}] Vote NO - song already in playlist (conflict)")
                return {'vote': 'no', 'reason': 'duplicate', 'timestamp': timestamp}
            else:
                # Tentatively add to temp state
                self.temp_playlist.append(song_id)
                
                # Log transaction in PREPARING state
                with self.log_lock:
                    self.transaction_log.append({
                        'transaction_id': transaction_id,
                        'state': 'PREPARING',
                        'operation': operation,
                        'song_id': song_id,
                        'timestamp': timestamp
                    })
                
                print(f"[{self.node_id}] Vote YES - ready to add")
                return {'vote': 'yes', 'timestamp': timestamp}
                
        elif operation == 'remove':
            if song_id not in self.temp_playlist:
                print(f"[{self.node_id}] Vote NO - song not in playlist (conflict)")
                return {'vote': 'no', 'reason': 'not_found', 'timestamp': timestamp}
            else:
                # Tentatively remove from temp state
                self.temp_playlist.remove(song_id)
                
                # Log transaction
                with self.log_lock:
                    self.transaction_log.append({
                        'transaction_id': transaction_id,
                        'state': 'PREPARING',
                        'operation': operation,
                        'song_id': song_id,
                        'timestamp': timestamp
                    })
                
                print(f"[{self.node_id}] Vote YES - ready to remove")
                return {'vote': 'yes', 'timestamp': timestamp}
        
        return {'vote': 'no', 'reason': 'invalid_operation', 'timestamp': timestamp}
        
    def _handle_commit(self, message):
        """Handle COMMIT phase - apply the changes"""
        transaction_id = message['transaction_id']
        operation = message['operation']
        song_id = message['song_id']
        
        timestamp = self.lamport_clock.increment()
        print(f"[{self.node_id} T={timestamp}] COMMIT: {operation} song {song_id}")
        
        # Apply the temporary state
        if self.temp_playlist is not None:
            self.playlist = self.temp_playlist
            self.temp_playlist = None
            
            # Update transaction log
            with self.log_lock:
                for txn in self.transaction_log:
                    if txn['transaction_id'] == transaction_id:
                        txn['state'] = 'COMMITTED'
                        break
            
            print(f"[{self.node_id}] ✅ Transaction COMMITTED")
        
        return {'status': 'committed', 'timestamp': timestamp}
        
    def _handle_abort(self, message):
        """Handle ABORT phase - rollback changes"""
        transaction_id = message['transaction_id']
        
        timestamp = self.lamport_clock.increment()
        print(f"[{self.node_id} T={timestamp}] ABORT transaction")
        
        # Discard temporary state (rollback)
        self.temp_playlist = None
        
        # Update transaction log
        with self.log_lock:
            for txn in self.transaction_log:
                if txn['transaction_id'] == transaction_id:
                    txn['state'] = 'ABORTED'
                    break
        
        print(f"[{self.node_id}] ❌ Transaction ABORTED (rolled back)")
        
        return {'status': 'aborted', 'timestamp': timestamp}

    def add_song(self, song_id):
        """Add a song using 2PC to keep all clients in sync"""
        timestamp = self.lamport_clock.increment()
        message = {
            'type': 'transaction',
            'client_id': self.node_id,
            'operation': 'add',
            'song_id': song_id,
            'timestamp': timestamp
        }
        
        print(f"\n[{self.node_id} T={timestamp}] Initiating distributed ADD transaction")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10.0)
            s.connect((self.coordinator_host, self.coordinator_port))
            s.sendall(json.dumps(message).encode('utf-8'))
            response = s.recv(4096).decode('utf-8')
            result = json.loads(response)
            
            # Update clock
            if 'timestamp' in result:
                new_time = self.lamport_clock.update(result['timestamp'])
            
            if result['status'] == 'committed':
                # Also update local playlist if not already updated
                if song_id not in self.playlist:
                    self.playlist.append(song_id)
                print(f"[{self.node_id} T={new_time}] ✅ Song added across all clients")
                return True
            else:
                print(f"[{self.node_id} T={new_time}] ❌ Transaction aborted: {result.get('votes', 'conflict detected')}")
                return False
            
    def remove_song(self, song_id):
        """Remove a song using 2PC to keep all clients in sync"""
        timestamp = self.lamport_clock.increment()
        message = {
            'type': 'transaction',
            'client_id': self.node_id,
            'operation': 'remove',
            'song_id': song_id,
            'timestamp': timestamp
        }
        
        print(f"\n[{self.node_id} T={timestamp}] Initiating distributed REMOVE transaction")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(10.0)
            s.connect((self.coordinator_host, self.coordinator_port))
            s.sendall(json.dumps(message).encode('utf-8'))
            response = s.recv(4096).decode('utf-8')
            result = json.loads(response)
            
            # Update clock
            if 'timestamp' in result:
                new_time = self.lamport_clock.update(result['timestamp'])
            
            if result['status'] == 'committed':
                # Also update local playlist if not already updated
                if song_id in self.playlist:
                    self.playlist.remove(song_id)
                print(f"[{self.node_id} T={new_time}] ✅ Song removed across all clients")
                return True
            else:
                print(f"[{self.node_id} T={new_time}] ❌ Transaction aborted: {result.get('votes', 'conflict detected')}")
                return False
                

    def close(self):
        """close open connections"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()