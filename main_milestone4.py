from client import Client
from server import Server
from coordinator_2pc import TwoPhaseCommitCoordinator
from notifications import Notifications
from music_player import MusicPlayer
import pika  # for catching AMQP errors
import threading
import time
import sys


SONGS = {
    "1": {"title": "Cruel Summer", "artist": "Taylor Swift", "file": "songs/cruel_summer.mp3"},
    "2": {"title": "Box Breathing", "artist": "Sorry Ghost", "file": "songs/box_breathing.mp3"},
    "3": {"title": "Lover", "artist": "Taylor Swift", "file": "songs/lover.mp3"},
    "4": {"title": "Golden", "artist": "HUNTRX", "file": "songs/golden.mp3"},
    "5": {"title": "To The Creatures", "artist": "Sorry Ghost", "file": "songs/to_the_creatures.mp3"},
    "6": {"title": "Take Down", "artist": "HUNTRX", "file": "songs/take_down.mp3"},
    "7": {"title": "How It's Done", "artist": "HUNTRX", "file": "songs/how_its_done.mp3"},
}
class MusicApp:
    def __init__(self, client_id):
        self.client_id = client_id
        self.music_player = MusicPlayer()
        self.server = None
        self.client = None
        
    def display_menu(self):
        print("\n" + "="*50)
        print(f"🎵 MUSIC PLAYER - {self.client_id}")
        print("="*50)
        print("MUSIC PLAYBACK:")
        print("1. Play a song")
        print("1.1. Pause a song")
        print("1.2. Resume a song")
        print("1.3. Stop a song")

        print("_"*50)
        print("PLAYLIST MANAGEMENT:")
        print("2. View my playlist")
        print("2.1. Add song to playlist")
        print("2.2. Remove song from playlist")

        print("_"*50)
        print("QUIT:")
        print("3. Quit")
        print("="*50)
        
    def display_songs(self):
        print("\n📀 Available Songs:")
        for key, song in SONGS.items():
            in_playlist = "✓" if key in self.client.playlist else " "
            print(f"[{in_playlist}] {key}. {song['title']} - {song['artist']}")
        
    def play_song(self):
        self.display_songs()
        choice = input("\nEnter song number: ").strip()
        
        song = SONGS[choice]
        song_request = f"{song['title']} - {song['artist']}"
            
        # Send request to server via IPC (with Lamport timestamp)
        if self.client:
            self.client.song_request(song_request)
        
        # Play song
        self.music_player.play_song(song['file'], song['title'], song['artist'])
            

    def add_to_playlist(self):
        self.display_songs()
        choice = input("\nEnter song number to add: ").strip()
        song = SONGS[choice]
        
        self.client.add_song(choice)
            
    def remove_from_playlist(self):
        if not self.client.playlist:
            print("\n⚠️  Your playlist is empty!")
            return
            
        print("\n🎵 Your Playlist:")
        for i, song_id in enumerate(self.client.playlist, 1):
            song = SONGS[song_id]
            print(f"{i}. {song['title']} - {song['artist']}")
            
        choice = input("\nEnter song number to remove: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(self.client.playlist):
            song_id = self.client.playlist[int(choice) - 1]
            song = SONGS[song_id]
            self.client.remove_song(song_id)            
            
    def view_playlist(self):
        if not self.client.playlist:
            print("\n⚠️  Your playlist is empty!")
            return
            
        print(f"\n🎵 {self.client_id}'s Playlist:")
        print("-" * 50)
        for i, song_id in enumerate(self.client.playlist, 1):
            song = SONGS[song_id]
            print(f"{i}. {song['title']} - {song['artist']}")
        print("-" * 50)
        print(f"Total songs: {len(self.client.playlist)}")
        
            
    def initialize_services(self):
        """Initialize server, coordinator, and client"""
        # Only CLIENT_1 starts the server and coordinator
        if self.client_id == "CLIENT_1":
            # Start music server
            self.server = Server(port=5001)
            self.server.start()
            time.sleep(0.5)
            
            # Start 2PC coordinator
            self.coordinator = TwoPhaseCommitCoordinator(port=5002)
            self.coordinator.start()
            time.sleep(0.5)  # Give coordinator time to start
        else:
            # Other clients just wait for server/coordinator to be ready
            time.sleep(1.0)
        
        # Create subscribe artist list based on client_id
        if self.client_id == "CLIENT_1":
            subscribed_artists = ["Taylor Swift", "Sorry Ghost"]
        elif self.client_id == "CLIENT_2":
            subscribed_artists = ["HUNTRX", "Taylor Swift"]
        else:
            subscribed_artists = ["Sorry Ghost"]
        
        # Use node_id for Lamport timestamps
        self.client = Client(
            node_id=self.client_id,  # Use node_id for Lamport compatibility
            server_host="localhost",
            server_port=5001,
            fav_artist_list=subscribed_artists,
            coordinator_host='localhost',
            coordinator_port=5002
        )
        self.client.receive_notification(self.client.subscription)
        
        # Publish notifications to client 
        try:
            time.sleep(0.5)
            notifications = Notifications("localhost")
            print("\n[NOTIFICATIONS] Publishing artist updates...")
            notifications.publish_artist_message("Taylor Swift", "New album 'Midnights' released!")
            time.sleep(0.2)
            notifications.publish_artist_message("Sorry Ghost", "New single 'Echo' out now!")
            time.sleep(0.2)
            notifications.publish_artist_message("HUNTRX", "World tour announced for 2025!")
        except pika.exceptions.AMQPConnectionError:
            pass
            
    def run(self):
        print(f"\n🎵 Welcome to Distributed Music Player - {self.client_id}! 🎵")
        self.initialize_services()
        
        while True:
            self.display_menu()
            choice = input("\nSelect option: ").strip()
            
            if choice == "1":
                self.play_song()
            elif choice == "1.1":
                self.music_player.pause()
            elif choice == "1.2":
                self.music_player.resume()
            elif choice == "1.3":
                self.music_player.stop()
        
            elif choice == "2":
                self.view_playlist()
            elif choice == "2.1":
                self.add_to_playlist()
            elif choice == "2.2":
                self.remove_from_playlist()

            elif choice == "3":
                print(f"\n👋 Goodbye from {self.client_id}!")
                self.music_player.stop()
                self.music_player.cleanup()
                self.client.close()
                if self.coordinator:
                    self.coordinator.stop()
                if self.server:
                    self.server.stop()
                break
            else:
                print("Invalid choice!")


def run_lamport_demo():
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
    
    def client_request(client, song_id, delay=0):
        if delay > 0:
            time.sleep(delay)
        song = SONGS[song_id]
        song_str = f"{song['title']} - {song['artist']}"
        client.song_request(song_str)
    
    # create threads for concurrent requests
    # client 1 requests immediately
    thread1 = threading.Thread(target=client_request, args=(client1, "1", 0))
    
    # client 2 requests after small delay
    thread2 = threading.Thread(target=client_request, args=(client2, "4", 0.05))
    
    # client 3 requests after slightly longer delay
    thread3 = threading.Thread(target=client_request, args=(client3, "5", 0.1))
    
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
    
    thread4 = threading.Thread(target=client_request, args=(client3, "2", 0))
    thread5 = threading.Thread(target=client_request, args=(client1, "3", 0.02))
    thread6 = threading.Thread(target=client_request, args=(client2, "6", 0.08))
    
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


def main():    
    # User picks to run the Lamport demo or menu 
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        run_lamport_demo()
    else:
        # Menu options
        client_id = sys.argv[1] if len(sys.argv) > 1 else "CLIENT_1"
        app = MusicApp(client_id)
        app.run()

if __name__ == "__main__":
    main()