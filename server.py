import socket 


class Server:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (self.host, self.port)
    
    def start(self):
    # Binding the socket to the specificed address
        self.server_socket.bind(self.server_address)
    # Server is listening for client connections
        self.server_socket.listen(5)
        while True: 
            client_socket, client_address = self.server_socket.accept()
            with client_socket:
                print("Connected by", client_address)
                data = client_socket.recv(1024).decode("utf-8")
                if not data:
                    continue
                print(f"Received song request: {data}")
                response = f"Playing song: {data}"
                client_socket.sendall(response.encode("utf-8"))