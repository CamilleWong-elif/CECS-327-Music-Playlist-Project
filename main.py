from client import Client
from server import Server
from notifications import Notifications

def main():
    play_song = "Take Down"
    subscribed_artists = ["Taylor Swift, Sorry Ghost"]

    # print list of songs
    print("1. Cruel Summer - Taylor Swift\n" \
        "2. Box Breathing - Sorry Ghost\n" \
        "3. Lover - Taylor Swift\n" \
        "4. Golden - HUNTRX\n" \
        "5. To The Creatures - Sorry Ghost\n" \
        "6. Take Down - HUNTRX\n" \
        "7. How It's Done - HUNTRX\n")

    # get input song from user
    play_song = input("Which song do you want to play?: ")
    
    # set fav_artist_list parameter for Client class
    subscribed_artists = ["Taylor Swift", "Sorry Ghost"]
    
    #-----connect to server --> claudia and josh
    server = Server(port=5001)
    server.start() #---> replace the name with whatever server start() func yall have

    client = Client(server_port=5001,fav_artist_list=subscribed_artists, broker_host = "localhost")#play_song, subscribed_artists)

    # client receive notifcations of publish-subscribe
    client.receive_notification(subscribed_artists)

    # publish artist updates --> Ren and Helen part
    notifications = Notifications("localhost")
    print("Publishing artist updates...")
    notifications.publish_artist_message("Taylor Swift", "New album released!")
    notifications.publish_artist_message("Sorry Ghost", "New single out now!")
    notifications.publish_artist_message("HUNTRX", "On tour this summer!")

    # send song request
    client.song_request(play_song)

if __name__ == "__main__":
    main()

