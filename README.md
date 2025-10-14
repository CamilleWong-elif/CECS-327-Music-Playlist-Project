# CECS-327-Music-Playlist-Project

## How to run the code
1. python -m venv venv
2. pip install -r requirements.txt
3. python main.py

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
  
