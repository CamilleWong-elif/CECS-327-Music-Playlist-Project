# CECS-327-Music-Playlist-Project
### Architecture Layout:  
```
+-----------------------+             TCP (request/response)           +---------------------+
|        Client         |  ----------------------------------------->  |        Server       |
| - song_request(song)  |  <-----------------------------------------  | - start() listen    |
| - receive_notification|               "OK: playing song"             | - handle song req   |
|   (RabbitMQ consumer) |                                               | - (optionally) also |
| - subscription: artists                                               |   publish events    |
+-----------+-----------+                                               +----------+----------+
            |                                                                   |
            |            RabbitMQ (publish/subscribe, async events)             |
            |      bind queue: artist.Taylor_Swift, artist.Sorry_Ghost          |
            |                                                                   |
            v                                                                   v
      +-----+--------------------+         publish routing keys           +------+--------------+
      |  Notifications (publisher)|  ------------------------------->     |  RabbitMQ Exchange |
      |  - publishes events like  |     "artist.Taylor_Swift"             |  (topic: artist_*) |
      |    artist.Taylor_Swift    |                                       +--------------------+
      +---------------------------+
```
- Server handles socket requests (play a song) and may also trigger notification publishing (e.g., “now playing Artist A”).

- Notifications is a producer that publishes messages to RabbitMQ using routing keys per artist.

- Client is a consumer that binds to the artists it cares about and receives events asynchronously.

```
+------------------+           +-------------------+          +------------------+
|   Notifications  |           |                   |          |      Client      |
| (Publisher app)  |  ----->   |   RabbitMQ Broker |  ----->  | (Subscriber app) |
| sends updates on |           |   (Message queue) |          | receives updates |
| topics (artists) |           |                   |          |  it subscribed to|
+------------------+           +-------------------+          +------------------+
                                     ^
                                     |
                                     |
                                 +-----------+
                                 |   Server  |
                                 | (optional)|
                                 +-----------+
```
### Components
#### 1. Publisher (your Notifications class)
- Connects to RabbitMQ.
- Declares an exchange (e.g. artist_updates).
- Publishes messages with a routing key like artist.Taylor_Swift.

#### 2. Broker (RabbitMQ)
- Receives published messages from the Notifications app.
- Checks which queues are bound to the exchange with matching routing keys.
- Sends messages only to those queues.

#### Subscribers (Clients)
- Each client connects to RabbitMQ.
- Declares a temporary queue for itself.
- Binds to the exchange for specific routing keys (artist.Taylor_Swift, artist.Sorry_Ghost)
- RabbitMQ delivers only those messages to the client.

#### Server (optional)
- Handles other synchronous work (e.g., song requests).
- Could also publish to RabbitMQ if something the server does should trigger notifications.



### Pub-Sub Flow
                       PUBLISHER (Notifications)
                       --------------------------------
                       | connects to RabbitMQ         |
                       | exchange: artist_updates     |
                       | type: topic                  |
                       |                              |
        publish("artist.Taylor_Swift", "New album!")  |
                       |                              |
                       v                              |
                +--------------------------------------------+
                |            RabbitMQ BROKER                 |
                |       exchange: artist_updates (topic)     |
                +---------------------+----------------------+
                                      |
                                      | routes by routing key match
         +----------------------------+-----------------------------+
         |                                                          |
         v                                                          v
+---------------------+                                   +----------------------+
|   Queue: q_clientA  |                                   |   Queue: q_clientB   |
|  bindings:                                            | |  bindings:           |
|   - artist.Taylor_Swift                                | |   - artist.HUNTRX    |
|   - artist.Sorry_Ghost                                 | |                      |
+---------------------+                                   +----------------------+
         |                                                          |
         | consume                                                   | consume
         v                                                          v
+---------------------+                                   +----------------------+
|  CLIENT A (Subscriber)                                  |  CLIENT B (Subscriber)|
|  receives: "New album!"                                 |  receives: (nothing)  |
+---------------------+                                   +----------------------+
