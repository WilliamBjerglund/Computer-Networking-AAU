import asyncio

# first we need our dictionary to store the connected clients
ConnectedClients = {} # stores names of connected clients

# Now we need a counter to keep track of the number of clients connected
ClientCount = 0

# we should also prevent race conditions when modifying the ConnectedClients dictionary using a lock.
lock = asyncio.Lock()

# Dictionary to track Heartbeat timestamps for each client (last entry)
LastClientHeartbeat = {}

# Dictionary to track the Clients that are currently Muted for using flagged words
MutedClients = {}

# List of flagged words
FlaggedWords = ["Faggot", "Paki", "Retard", "Cocksucker", "Whore", "Cracker"]