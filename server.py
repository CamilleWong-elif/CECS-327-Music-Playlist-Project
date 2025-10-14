import socket 
import threading
class Server:
    def __init__(self, host='localhost', port=5001):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (self.host, self.port)
        self._stop = threading.Event()
        self._thread = None

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
            song = data.decode("utf-8").strip()
            print(f"Received song request: {song}")
            response = f"Playing song: {song}"
            conn.sendall(response.encode("utf-8"))

    def stop(self):
        self._stop.set()
        # poke accept() so the loop exits
        try:
            socket.create_connection((self.host, self.port), timeout=1).close()
        except Exception:
            pass