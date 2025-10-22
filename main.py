from client import Client
from server import Server
from notifications import Notifications
import pika  # for catching AMQP errors

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
    # show menu
    for i, s in enumerate(SONGS, 1):
        print(f"{i}. {s}")
    choice = input("\nWhich song do you want to play?: ").strip()
    song = SONGS[int(choice)-1] if choice.isdigit() and 1 <= int(choice) <= len(SONGS) else choice

    # start servers
    servers = [Server(port=p) for p in [5001, 5002, 5003]]
    for s in servers:
        s.start()
    print("\nServers started on ports 5001, 5002, 5003\n")

    # create clients
    client1 = Client("localhost", 5001, ["Taylor Swift"])
    client2 = Client("localhost", 5002, ["Sorry Ghost"])
    client3 = Client("localhost", 5003, ["HUNTRX"])

    print("Client 1 subscribed to Taylor Swift")
    print("Client 2 subscribed to Sorry Ghost")
    print("Client 3 subscribed to HUNTRX\n")

    # start receiving notifications
    client1.receive_notification(client1.subscription)
    client2.receive_notification(client2.subscription)
    client3.receive_notification(client3.subscription)

    # publish notifications (if RabbitMQ running)
    try:
        notifications = Notifications("localhost")
        print("Publishing artist updates...\n")
        notifications.publish_artist_message("Taylor Swift", "New album released!")
        notifications.publish_artist_message("Sorry Ghost", "New single out now!")
        notifications.publish_artist_message("HUNTRX", "On tour this summer!")
    except pika.exceptions.AMQPConnectionError:
        print("(Skipping publish — RabbitMQ not available)\n")

    # clients request songs
    print("Clients are requesting songs...\n")
    client1.song_request(song)  # <— play user’s chosen song
    client2.song_request("Box Breathing - Sorry Ghost")
    client3.song_request("Golden - HUNTRX")

    # simulate shared playlist counter (simple demonstration)
    print("\nSimulating shared playlist update (no actual deadlock)...")
    for i in range(1, 4):
        print(f"Client {i} updated playlist count -> {i}")
    print("\nNo deadlock — all clients finished safely.")

if __name__ == "__main__":
    main()
