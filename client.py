import socket
import threading
import pika #RabbitMQ

class Client:
    def __init__(self, server_host="localhost", server_port=5000, fav_artist_list = None):
        #self.song = "song name"
        self.subscription = [] # list of fav artists client is subscribed to
        self.server_host = server_host
        self.server_port = server_port
        self.connection = None
        self.channel = None

    def song_request(self, input_song):
        """
        send a song request to the server using TCP sockets (IPC)
        """
        # create TCP pocket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((self.server_host, self.server_port)) # connect to the server as localhost:5000
                s.sendall(input_song.encode("utf-8")) # send the song name
                response = s.recv(1024).decode("utf-8") # wait for the server to respond
                print(f"server response: {response}")

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
            

    def close(self):
        """close open connections"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
