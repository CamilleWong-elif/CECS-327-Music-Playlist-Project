from client import Client 
import pika #RabbitMQ
import json 
from datetime import datetime, timezone

class Notifications:
    EXCHANGE_NAME = "artist_update"
    EXCHANGE_TYPE = "topic"      # topic because the routing key is based on artist name
    
    # Connect to RabbitMQ broker and define exchange 
    def __init__(self, host: str= "localhost"):
        params = pika.ConnectionParameters(host)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=self.EXCHANGE_NAME, exchange_type=self.EXCHANGE_TYPE)

    def publish_artist_message(self, artist: str, message: str):
        '''
        Publish a message to the exchange with routing key based on artist name
        e.g. Routing key: artist.Taylor Swift
        '''
        routing_key = f"artist.{(artist)}"   
        payload = {
            "type": "artist_update",
            "artist": artist,
            "message": message,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        body = json.dumps(payload).encode("utf-8")

        # Sends message to RabbitMQ
        self.channel.basic_publish(
            exchange=self.EXCHANGE_NAME, 
            routing_key=routing_key, 
            body=body,
            properties=pika.BasicProperties(delivery_mode=2)) # make message persistent
        
        print(f" [x] Sent '{routing_key}':'{message}'") 
    
    
    def close_connection(self):
        self.connection.close()