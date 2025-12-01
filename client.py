import socket
import threading
import pika #RabbitMQ
import json  # timestamp msgs
from lamport_clock import LamportClock  # lamport clock

class Client:
    # M4: added node_id parameter
    def __init__(self, node_id, server_host="localhost", server_port=5001, fav_artist_list = None, broker_host = "localhost"):
        #self.song = "song name"
        self.node_id = node_id  # M4: unique client identifier
        self.playlist = []
        self.lamport_clock = LamportClock(node_id)  # M4: added lamport clock
        self.subscription = [] # list of fav artists client is subscribed to
        self.server_host = server_host
        self.server_port = server_port
        self.connection = None
        self.channel = None
        for artist in fav_artist_list:
            self.subscription.append(artist) 

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

    def add_song(self, song_id):
        """add a song to the client's playlist"""
        self.playlist.append(song_id)

    def remove_song(self, song_id):
        """remove a song from the client's playlist"""
        if song_id in self.playlist:
            self.playlist.remove(song_id)

    def close(self):
        """close open connections"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()