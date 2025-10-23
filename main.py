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
    # menu
    for i, s in enumerate(SONGS, 1):
        print(f"{i}. {s}")
    choice = input("\nWhich song do you want to play?: ").strip()
    song = SONGS[int(choice)-1] if choice.isdigit() and 1 <= int(choice) <= len(SONGS) else choice

    # start server
    server = Server(port=5001)
    server.start()

    # create client + start consuming first (so we can see the published events)
    subscribed_artists = ["Taylor Swift", "Sorry Ghost"]
    client = Client(server_host="localhost", server_port=5001, fav_artist_list=subscribed_artists)
    client.receive_notification(client.subscription)

    # try to publish artist updates (skip if RabbitMQ not running)
    try:
        notifications = Notifications("localhost")
        print("Publishing artist updates...")
        notifications.publish_artist_message("Taylor Swift", "New album released!")
        notifications.publish_artist_message("Sorry Ghost", "New single out now!")
        notifications.publish_artist_message("HUNTRX", "On tour this summer!")
    except pika.exceptions.AMQPConnectionError as e:
        print(f"(Skipping publish — RabbitMQ not available: {e})")

    # send the actual song request via IPC socket
    client.song_request(song)

if __name__ == "__main__":
    main()
