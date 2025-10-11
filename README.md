# CECS-327-Music-Playlist-Project

## Summary of Changes Made by Helen & Ren
### Port Notes: 
- We changed the port from 5000 to 5001 for client and server since that port was already taken on our local machine and we couldn't fully kill it. 
- Feel free to change it back to port 5000 though!  
  
### Server.py
- Edited server.py so we can work on notifications.py
  - Feel free to change!
  
### Client.py
- Appended each artist in fav_artist_list to self.subscription 
- Changed 'fanout' to topic exchange type 'topic'

### Notifications.py
- Implemented Notifications class

### Main.py
- Called Notifications to publish multiple artist updates

## Output after running:
1. Cruel Summer - Taylor Swift
2. Box Breathing - Sorry Ghost
3. Lover - Taylor Swift
4. Golden - HUNTRX
5. To The Creatures - Sorry Ghost
6. Take Down - HUNTRX
7. How It's Done - HUNTRX

Which song do you want to play?: Cruel Summer
[Server] Listening on localhost:5001

Subscribed to artist updates: ['Taylor Swift', 'Sorry Ghost', 'Taylor Swift', 'Sorry Ghost'] 

Publishing artist updates...
 - [x] Sent 'artist.Taylor Swift':'New album released!'
 - [x] Sent 'artist.Sorry Ghost':'New single out now!'
 - [x] Sent 'artist.HUNTRX':'On tour this summer!'

Connected by ('127.0.0.1', 52125). 

Received song request: Cruel Summer

🎵 notification: {"type": "artist_update", "artist": "Taylor Swift", "message": "New album released!", "timestamp_utc": "2025-10-11T21:12:02.602802+00:00"}

🎵 notification: {"type": "artist_update", "artist": "Sorry Ghost", "message": "New single out now!", "timestamp_utc": "2025-10-11T21:12:02.603560+00:00"}
server response: Playing song: Cruel Summer
  