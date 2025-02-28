import threading

# first we need our dictionary to store the connected clients
ConnectedClients = {} # stores names of connected clients

# Now we need a counter to keep track of the number of clients connected
ClientCount = 0

# we should also prevent race conditions when modifying the ConnectedClients dictionary using a lock.
lock = threading.Lock()
