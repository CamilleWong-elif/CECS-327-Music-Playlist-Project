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
       subscribe to RabbitMQ queue to receive updates
       """
       try:
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()

            channel.exchange_declare(exchange='artist_updates', exchange_type='topic')

            # create a unique queue for this client
            result = channel.queue_declare(queue='', exclusive=True)
            queue_name = result.method.queue

            # bind queue for each artist in list
            for artist in self.fav_artist_list:
                routing_key = f"artist.{artist.replace(' ', '_')}"
                channel.queue_bind(exchange='artist_updates', queue=queue_name, routing_key=routing_key)
                print(f"[CLIENT] subscribed to updates from {artist}")

            # when msg arrives, RabbitMQ uses this function to pass in output
            def callback(ch, method, properties, body):
                print(f"[NOTIFICATION]: {body.decode()}")

            channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
            print("[CLIENT] waiting for notifs...")
            channel.start_consuming()

       except pika.exceptions.AMQPConnectionError:
            print("Error: Could not connect to RabbitMQ. Is it running?")
       except Exception as e:
            print(f"RabbitMQ setup error: {e}")

    def close(self):
        """close open connections"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
