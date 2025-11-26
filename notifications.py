from client import Client 
import pika #RabbitMQ
import json 
from datetime import datetime, timezone
from lamport_clock import LamportClock #lamport clock

class Notifications:
    EXCHANGE_NAME = "artist_update"
    EXCHANGE_TYPE = "topic"      # topic because the routing key is based on artist name
    
    # Connect to RabbitMQ broker and define exchange 
    def __init__(self, host: str= "localhost"):
        params = pika.ConnectionParameters(host)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=self.EXCHANGE_NAME, exchange_type=self.EXCHANGE_TYPE)
        
        # M4: init lamport clock for notification service
        self.lamport_clock = LamportClock("NOTIFICATION_SERVICE")

    def publish_artist_message(self, artist: str, message: str):
        '''
        Publish a message to the exchange with routing key based on artist name
        e.g. Routing key: artist.Taylor Swift
        MODIFIED: Now includes Lamport timestamp in the message payload
        '''
        # M4: increment clock before sending notification (send event)
        lamport_time = self.lamport_clock.increment()
        
        routing_key = f"artist.{(artist)}"   
        payload = {
            "type": "artist_update",
            "artist": artist,
            "message": message,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "lamport_timestamp": lamport_time,  # M4: add lamport timestamp
            "node_id": "NOTIFICATION_SERVICE"   # M4: identify sender
        }
        body = json.dumps(payload).encode("utf-8")

        # Sends message to RabbitMQ
        self.channel.basic_publish(
            exchange=self.EXCHANGE_NAME, 
            routing_key=routing_key, 
            body=body,
            properties=pika.BasicProperties(delivery_mode=2)) # make message persistent
        
        # M4: enhanced logging with lamport timestamp
        print(f" [x] sent at lamport time {lamport_time} - '{routing_key}':'{message}'") 
    
    
    def close_connection(self):
        self.connection.close()