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
    client = Client(fav_artist_list=subscribed_artists)#play_song, subscribed_artists)
    
    #-----connect to server --> claudia and josh
    server = Server()
    server.start() #---> replace the name with whatever server start() func yall have

    #----receive notifications --> Ren and Helen part
    notifications = Notifications()
    notifications.publish_update("Taylor Swift", "New album released") #-->parameters: (artist_name, output_notification)

    # send song request
    client.song_request(play_song)

    # client receive notifcations of publish-subscribe
    client.receive_notification(subscribed_artists)

if __name__ == "main":
    main()

