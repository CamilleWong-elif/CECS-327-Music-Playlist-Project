import socket 
import threading
import json  # timestamp msgs
from lamport_clock import LamportClock  # lamport clock
class Server:
    def __init__(self, host='localhost', port=5001):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (self.host, self.port)
        self._stop = threading.Event()
        self._thread = None
        self.lamport_clock = LamportClock("SERVER")  # M4: server's Lamport clock
        self.request_queue = []  # M4: ordered queue of requests
        self.queue_lock = threading.Lock()  # M4: thread-safe queue

    def start(self):
        if self._thread and self._thread.is_alive():
            print("[Server] already running"); return

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[Server] Listening on {self.host}:{self.port}")

        def loop():
            try:
                while not self._stop.is_set():
                    try:
                        conn, addr = self.server_socket.accept()
                    except OSError:
                        break
                    threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()
            finally:
                try: self.server_socket.close()
                except Exception: pass

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def _handle_client(self, conn, addr):
        with conn:
            print("Connected by", addr)
            data = conn.recv(1024)
            if not data:
                return
            
            # M4: parse JSON message with timestamp
            message = json.loads(data.decode("utf-8").strip())
            song = message["song"]
            client_timestamp = message["timestamp"]
            client_id = message["node_id"]
            
            # M4: update server clock on receive
            server_time = self.lamport_clock.update(client_timestamp)
            print(f"Received song request: {song} from {client_id} (client T={client_timestamp}, server T={server_time})")
            
            # M4: add to ordered queue
            with self.queue_lock:
                self.request_queue.append({
                    "timestamp": client_timestamp,
                    "node_id": client_id,
                    "song": song
                })
                self.request_queue.sort(key=lambda x: (x["timestamp"], x["node_id"]))
                print(f"[SERVER] Request queue: {[(r['timestamp'], r['node_id']) for r in self.request_queue]}")
            
            # M4: increment clock before sending response
            response_timestamp = self.lamport_clock.increment()
            response = json.dumps({
                "message": f"Playing song: {song}",
                "timestamp": response_timestamp
            })
            conn.sendall(response.encode("utf-8"))

    def stop(self):
        self._stop.set()
        # poke accept() so the loop exits
        try:
            socket.create_connection((self.host, self.port), timeout=1).close()
        except Exception:
            pass