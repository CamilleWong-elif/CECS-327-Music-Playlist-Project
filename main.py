from client import Client

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
    input(print("Which song do you want to play?: ", play_song))

    Client(play_song, subscribed_artists)
    
