# CECS-327-Music-Playlist-Project

## How to run the code
1. python -m venv venv
2. pip install -r requirements.txt
3. IDE Terminal:
   - Mac:
     1. brew install rabbitmq
     2. brew services start rabbitmq
   - Windows:
     1. choco install erlang -y
     2. choco install rabbitmq -y
     3. net start RabbitMQ
4. milestone 2: python main.py
5. milestone 3: python main_milestone3.py
6. milestone 4: 
   - User menu mode: ```python main_milestone4.py CLIENT_1``` 
     - note: Default is CLIENT_1. To login using a different user, use CLIENT_2 or CLIENT_3 
   - Lamport demo: ```python main_milestone4.py --demo``` 

## Output after running:
CECS-327-Music-Playlist-Project % python main.py
1. Cruel Summer - Taylor Swift
2. Box Breathing - Sorry Ghost
3. Lover - Taylor Swift
4. Golden - HUNTRX
5. To The Creatures - Sorry Ghost
6. Take Down - HUNTRX
7. How It's Done - HUNTRX

Which song do you want to play?: Golden
[Server] Listening on localhost:5001

[CLIENT] subscribed to updates from: ['Taylor Swift', 'Sorry Ghost'] 

[CLIENT] waiting for notifs...
Publishing artist updates...
 [x] Sent 'artist.Taylor Swift':'New album released!'
 [x] Sent 'artist.Sorry Ghost':'New single out now!'
 [x] Sent 'artist.HUNTRX':'On tour this summer!'

🎵 [NOTIFICATION]: {"type": "artist_update", "artist": "Taylor Swift", "message": "New album released!", "timestamp_utc": "2025-10-14T15:57:52.979700+00:00"}
Connected by ('127.0.0.1', 65225)

🎵 [NOTIFICATION]: {"type": "artist_update", "artist": "Sorry Ghost", "message": "New single out now!", "timestamp_utc": "2025-10-14T15:57:52.980058+00:00"}
Received song request: Golden - HUNTRX
server response: Playing song: Golden - HUNTRX
