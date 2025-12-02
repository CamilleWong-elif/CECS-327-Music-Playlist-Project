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
6. milestone 4: python main_milestone4.py
   - User menu mode: ```python main_milestone4.py CLIENT_1``` 
     - note: Default is CLIENT_1. To login using a different user, use CLIENT_2 or CLIENT_3 
   - Lamport demo: ```python main_milestone4.py --demo``` 
