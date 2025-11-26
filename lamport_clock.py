import threading

class LamportClock:
    def __init__(self, node_id):
        self.node_id = node_id  # unique identifier for this node
        self.clock = 0
        self.lock = threading.Lock()  # thread-safe operations
    
    def increment(self):
        with self.lock:
            self.clock += 1
            return self.clock
    
    def get_time(self):
        with self.lock:
            return self.clock
    
    def update(self, received_timestamp):
        with self.lock:
            self.clock = max(self.clock, received_timestamp) + 1
            return self.clock
    
    def get_timestamp_with_id(self):
        with self.lock:
            return (self.clock, self.node_id) # return a tuple (timestamp, node_id) for total ordering
            # if timestamps are equal, node_id breaks the tie
    
    def __str__(self):
        return f"node[{self.node_id}] time: {self.clock}"