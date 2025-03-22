import re
import asyncio
import random
import socket
import Globals
import time
import Database
from Commands import Commands

cmdHandler = Commands()

async def GetLocalIP():
    """
    Returns the local IP address by connecting to a public DNS.
    Falls back to 127.0.0.1 or localhost if the connection fails.

    Returns:
    str: The local IP address of the server.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))  # Google's public DNS
        LocalIP = s.getsockname()[0]
    except Exception:
        LocalIP = "127.0.0.1"
    finally:
        s.close()
    return LocalIP

# Server Configuration
HOST = "0.0.0.0"
PORT = 12345

# Parameters for rate limiting messages (spam prevention)
RATELIMIT = 5
TIMEWINDOW = 8
# Dictionary to track message timestamps for each client (rate limiting)
clientMessageTimestamps = {}

# Heartbeat configuration
HeartbeatInterval = 30  # Interval to check heartbeats (seconds)
HeartbeatTimeout = 61  # Maximum allowed time without a heartbeat (seconds)


async def HandleClient(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    This function is the main handler for client connections.
    - Registers the client with a unique name.
    - Handles client messages and commands.
    - Unregisters the client when the connection is closed.
    
    Args:
        reader (asyncio.StreamReader): Stream reader object for client data.
        writer (asyncio.StreamWriter): Stream writer object for delivering data to the client.
    """
    addr = writer.get_extra_info('peername')
    clientName = await getClientName(reader, writer)
    await registerClient(clientName, writer)
    print(f"[{cmdHandler.Timestamp()}] New connection from {addr}")

    try:
        await handleClientMessages(reader, writer, clientName, addr)
    except Exception as e:
        print(f"[{cmdHandler.Timestamp()}] Error: {e}")
    finally:
        await unregisterClient(clientName)
        print(f"[{cmdHandler.Timestamp()}] Connection closed: {addr}")
        writer.close()
        await writer.wait_closed()


async def getClientName(reader, writer):
    """
    This function prompts the client to enter a name and validates it.
    If the name is already taken, the client is prompted to enter a different name and assigns a random name if none is provided.

    Args:
        reader (asyncio.StreamReader): Client's stream reader object.
        writer (asyncio.StreamWriter): Client's stream writer object.

    Returns:
        str: The unique name of the client.
    """
    writer.write("Enter your name: ".encode())
    await writer.drain()
    data = await reader.read(1024)
    clientName = data.decode().strip()
    while True:
        async with Globals.lock:
            if not clientName:
                clientName = await generateRandomName()
            while clientName in Globals.ConnectedClients:
                writer.write("Name already taken. Please enter a different name: ".encode())
                await writer.drain()
                data = await reader.read(1024)
                clientName = data.decode().strip()
                if not clientName:
                    clientName = await generateRandomName()
            if clientName not in Globals.ConnectedClients:
                break
    return clientName


async def generateRandomName():
    """
    Simple function to generate a random name for the client provided the name is not already taken and they did not provide a name.

    Returns:
        str: A random name for the client.
    """
    while True:
        randomName = f"Client{random.randint(1, 1000)}"
        if randomName not in Globals.ConnectedClients:
            return randomName


async def registerClient(clientName, writer):
    """
    Registers a new client with the global list of connected clients.

    Args:
        clientName (str): The unique name of the client.
        writer (asyncio.StreamWriter): The stream writer object for the client.
    """
    async with Globals.lock:
        Globals.ConnectedClients[clientName] = writer
        Globals.ClientCount += 1
        Globals.LastClientHeartbeat[clientName] = time.time()


async def unregisterClient(clientName):
    """
    Removes a client from the global list of connected clients.

    Args:
        clientName (str): The unique name of the client to unregister.
    """
    async with Globals.lock:
        if clientName in Globals.ConnectedClients:
            del Globals.ConnectedClients[clientName]
            Globals.ClientCount -= 1
            del Globals.LastClientHeartbeat[clientName]


async def CheckHeartbeat():
    """
    This function will do periodic checks to see if any clients have disconnected due to a heartbeat timeout.
    If a client fails to send heartbeats within the given timeout period, they will be disconnected.
    """
    while True:
        CurrentTime = time.time()
        await asyncio.sleep(HeartbeatInterval)
        async with Globals.lock:
            for clientName, LastHeartbeat in list(Globals.LastClientHeartbeat.items()):
                if CurrentTime - LastHeartbeat > HeartbeatTimeout:
                    print(f"[{cmdHandler.Timestamp()}] Client {clientName} disconnected due to heartbeat timeout.")
                    writer = Globals.ConnectedClients[clientName]
                    writer.close()
                    await writer.wait_closed()
                    await unregisterClient(clientName)


async def handleClientMessages(reader, writer, clientName, addr, RateLimit=RATELIMIT, TimeWindow=TIMEWINDOW):
    """
    Handles any incoming messages from the client.

    Args:
        reader (asyncio.StreamReader): Client's stream reader object to receive messages.
        writer (asyncio.StreamWriter): Client's stream writer object to send responses.
        clientName (str): The unique name of the client.
        addr (tuple): The IP address and port of the client.
        RateLimit (int): The maximum number of messages allowed within the TimeWindow.
        TimeWindow (int): The time window in seconds for the RateLimit before a heartbeat disconnect.
    """
    while True:
        data = await reader.read(1024)
        if not data:
            break
        message = data.decode().strip()
        print(f"[{cmdHandler.Timestamp()}] Client ({addr}): {message}")

        # Confirm Heartbeat
        if message == "heartbeat":
            async with Globals.lock:
                Globals.LastClientHeartbeat[clientName] = time.time()
            continue
        
        # Track time
        currentTime = time.time()
        
        # Check for flagged words
        if clientName in Globals.MutedClients:
            if currentTime < Globals.MutedClients[clientName]:
                remaingTime = int(Globals.MutedClients[clientName] - currentTime)
                WarningMessage = f"You used innaproppriate language. You are muted for {remaingTime} seconds."
                writer.write(WarningMessage.encode())
                await writer.drain()
                continue
            else:
                del Globals.MutedClients[clientName]
            
        # Check for rate limiting
        if clientName not in clientMessageTimestamps:
            clientMessageTimestamps[clientName] = []
        clientMessageTimestamps[clientName] = [timestamp for timestamp in clientMessageTimestamps[clientName] if currentTime - timestamp < TimeWindow]
        if len(clientMessageTimestamps[clientName]) >= RateLimit:
            response = "Rate limit exceeded. Please wait before sending more messages."
            writer.write(response.encode())
            await writer.drain()
            continue
        clientMessageTimestamps[clientName].append(currentTime)

        # If not a command, check for flagged words
        if not message.startswith("!"):
            flaggedFound = False
            for flagged in Globals.FlaggedWords:
                pattern = re.compile(rf"\b{re.escape(flagged)}\b", re.IGNORECASE)
                if pattern.search(message):
                    flaggedFound = True
                    # Log the flagged message
                    Database.InsertFlaggedMessage(clientName, addr[0], message, flagged)
                    # Mute the client for 300 seconds (5 minutes)
                    Globals.MutedClients[clientName] = currentTime + 300
                    WarningMessage = f"You are using innapropriate language and have been muted for 5 minutes."
                    writer.write(WarningMessage.encode())
                    await writer.drain()
                    break
            if flaggedFound:
                continue

        # Process commands or broadcast message
        if message.startswith("!"):
            await handleCommand(message, writer, clientName, addr)
        else:
            await broadcastMessage(clientName, message)


async def handleCommand(message, writer, clientName, addr):
    """
    Simple command handler for client commands.

    Args:
        message (str): The message containing the command.
        writer (asyncio.StreamWriter): The stream writer object responding to the client.
        clientName (str): The unique name of the client sending the command.
        addr (tuple): The IP address and port of the client.
    """
    parts = message[1:].split(' ', 1)
    commandKey = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    if commandKey in cmdHandler.CommandDict:
        CommandFunction = cmdHandler.CommandDict[commandKey]
        # if the command is "pm", we call its signature
        if commandKey == "pm":
            await CommandFunction(message, writer, clientName)
            return # handles its own response
        elif commandKey == "whoami":
            response = CommandFunction(clientName, addr)
        else:
            response = CommandFunction(clientName)
    else:
        response = "Invalid command. for help type !help"
    writer.write(response.encode())
    await writer.drain()


async def broadcastMessage(clientName, message):
    """
    Sends a broadcasted message to all connected clients.
    Think of it as a global information message to clients.

    Args:
        clientName (str): The unique name of the client sending the message.
        message (str): The message to broadcast.
    """
    signalColor = "\033[93m" # Yellow color for terminal output
    resetColor = "\033[0m" # Reset color to default terminal
    response = f"{signalColor}[{cmdHandler.Timestamp()}]{resetColor} {clientName}: {message}"
    async with Globals.lock:
        for clientWriter in Globals.ConnectedClients.values():
            try:
                clientWriter.write(response.encode())
                await clientWriter.drain()
            except Exception as e:
                print(f"[{cmdHandler.Timestamp()}] Error broadcasting to a client: {e}")


async def Broadcast(message):
    """
    Broadcasts a message to all connected clients.

    Args:
        message (str): The message to be broadcasted to all clients.
    """
    signalColor = "\033[93m" # Yellow color for terminal output
    resetColor = "\033[0m" # Reset color to default terminal
    messageFormat = f"{signalColor}[BROADCAST]{resetColor} {message}"
    async with Globals.lock:
        for writer in Globals.ConnectedClients.values():
            try:
                writer.write(messageFormat.encode())
                await writer.drain()
            except Exception:
                pass # Ignore exceptions for now


async def ServerCommandCheck():
    """
    Checks the server for admin commands via console input.

    - '!broadcast <message>': Broadcasts a message to all connected clients.
    - '!exit': Shuts down the server and disconnects all clients.

    Runs in a background task to avoid blocking the event loop.
    """
    loop = asyncio.get_event_loop()
    while True:
        # Run input() in a thread so as not to block the event loop
        command = await loop.run_in_executor(None, input, "Server Command: ")
        command = command.strip()
        if command.lower().startswith("!broadcast"):
            message = command[len("!broadcast"):].strip()
            if message:
                await Broadcast(message)
                print(f"[{cmdHandler.Timestamp()}] Broadcast sent: {message}")
            else:
                print("Usage: !broadcast <message>")
        elif command.lower() == "!exit":
            print("Shutting down server...")
            for task in asyncio.all_tasks():
                task.cancel()
            break
        else:
            print("Unknown server command.")


async def Main():
    """
    Main entry point of the server. Starts the server and background tasks.
    """
    # Initialize the flagged messages database
    Database.InitDB()

    SERVER_IP = await GetLocalIP()
    print(f"[{cmdHandler.Timestamp()}] Server detected IP: {SERVER_IP}")

    server = await asyncio.start_server(HandleClient, HOST, PORT)
    print(f"[{cmdHandler.Timestamp()}] Server started on {SERVER_IP}:{PORT}")

    # Start the server command check as a background task
    asyncio.create_task(ServerCommandCheck())
    # Start the heartbeat check as a background task
    asyncio.create_task(CheckHeartbeat())

    async with server:
        await server.serve_forever()



if __name__ == "__main__":
    try:
        asyncio.run(Main())
    except asyncio.CancelledError:
        print(f"[{cmdHandler.Timestamp()}] Server shutting down gracefully.")