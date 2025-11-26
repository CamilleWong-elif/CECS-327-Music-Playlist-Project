from client import Client
from server import Server
from notifications import Notifications
import pika  # for catching AMQP errors
import threading
import time

SONGS = [
    "Cruel Summer - Taylor Swift",
    "Box Breathing - Sorry Ghost",
    "Lover - Taylor Swift",
    "Golden - HUNTRX",
    "To The Creatures - Sorry Ghost",
    "Take Down - HUNTRX",
    "How It's Done - HUNTRX",
]

def main():
    print("=" * 70)
    print("DISTRIBUTED MUSIC SYSTEM - LAMPORT TIMESTAMP DEMO")
    print("=" * 70)
    
    # start server first
    print("\n[SETUP] Starting server...")
    server = Server(port=5001)
    server.start()
    time.sleep(0.5)  # give server time to start
    
    # create multiple clients to demonstrate concurrent requests
    print("\n[SETUP] Creating clients...")
    
    # client 1 - likes Taylor Swift and Sorry Ghost
    client1 = Client(
        node_id="CLIENT_1",
        server_host="localhost",
        server_port=5001,
        fav_artist_list=["Taylor Swift", "Sorry Ghost"]
    )
    
    # client 2 - likes HUNTRX and Taylor Swift
    client2 = Client(
        node_id="CLIENT_2",
        server_host="localhost",
        server_port=5001,
        fav_artist_list=["HUNTRX", "Taylor Swift"]
    )
    
    # client 3 - likes Sorry Ghost
    client3 = Client(
        node_id="CLIENT_3",
        server_host="localhost",
        server_port=5001,
        fav_artist_list=["Sorry Ghost"]
    )
    
    # start notif listeners for all clients
    print("\n[SETUP] starting notification listeners...")
    client1.receive_notification(client1.subscription)
    client2.receive_notification(client2.subscription)
    client3.receive_notification(client3.subscription)
    time.sleep(0.5)
    
    # publish artist updates with timestamps
    print("\n" + "=" * 70)
    print("PHASE 1: PUBLISHING ARTIST UPDATES (with Lamport timestamps)")
    print("=" * 70)
    try:
        notifications = Notifications("localhost")
        notifications.publish_artist_message("Taylor Swift", "New album 'Midnights' released!")
        time.sleep(0.2)
        notifications.publish_artist_message("Sorry Ghost", "New single 'Echo' out now!")
        time.sleep(0.2)
        notifications.publish_artist_message("HUNTRX", "World tour announced for 2025!")
        time.sleep(1)  # Let notifications propagate
    except pika.exceptions.AMQPConnectionError as e:
        print(f"(skipping publish – RabbitMQ not available: {e})")
    
    # demonstrate concurrent song requests with lamport ordering
    print("\n" + "=" * 70)
    print("PHASE 2: CONCURRENT SONG REQUESTS (demonstrates causal ordering)")
    print("=" * 70)
    print("\nThree clients will request songs simultaneously.")
    print("Watch how Lamport timestamps establish causal ordering!\n")
    
    def client_request(client, song, delay=0):
        if delay > 0:
            time.sleep(delay)
        client.song_request(song)
    
    # create threads for concurrent requests
    # client 1 requests immediately
    thread1 = threading.Thread(target=client_request, args=(client1, SONGS[0], 0))
    
    # client 2 requests after small delay
    thread2 = threading.Thread(target=client_request, args=(client2, SONGS[3], 0.05))
    
    # client 3 requests after slightly longer delay
    thread3 = threading.Thread(target=client_request, args=(client3, SONGS[4], 0.1))
    
    # start all threads (simulating concurrent requests)
    print("Starting concurrent requests...\n")
    thread1.start()
    thread2.start()
    thread3.start()
    
    # wait for all requests to complete
    thread1.join()
    thread2.join()
    thread3.join()
    
    time.sleep(0.5)
    
    # demonstrate another round with different timing
    print("\n" + "=" * 70)
    print("PHASE 3: SECOND ROUND OF REQUESTS (different causal order)")
    print("=" * 70 + "\n")
    
    thread4 = threading.Thread(target=client_request, args=(client3, SONGS[1], 0))
    thread5 = threading.Thread(target=client_request, args=(client1, SONGS[2], 0.02))
    thread6 = threading.Thread(target=client_request, args=(client2, SONGS[5], 0.08))
    
    thread4.start()
    thread5.start()
    thread6.start()
    
    thread4.join()
    thread5.join()
    thread6.join()
    
    time.sleep(1)
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print("\nKey observations:")
    print("1. Each event (send/receive) increments the local Lamport clock")
    print("2. On receiving a message, clock = max(local, received) + 1")
    print("3. Server maintains a causally-ordered queue of requests")
    print("4. Timestamps establish 'happened-before' relationships")
    print("\nNote: If two events have the same timestamp, node_id breaks the tie")
    print("for total ordering (not shown explicitly but implemented in code).\n")

if __name__ == "__main__":
    main()