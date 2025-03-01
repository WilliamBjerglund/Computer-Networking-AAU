import asyncio
import random
import socket
import Globals
import time
from Commands import Commands

cmdHandler = Commands()

async def GetLocalIP():
    """
    Returns the local IP address by connecting to a public DNS.
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

HOST = "0.0.0.0"
PORT = 12345

# Parameters for rate limiting messages
RATELIMIT = 5
TIMEWINDOW = 8
# Dictionary to track message timestamps for each client
clientMessageTimestamps = {}
# Heartbeat timeout in seconds
# Heartbeat parameters
HeartbeatInterval = 30  # seconds
HeartbeatTimeout = 60  # seconds

async def HandleClient(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    parem: RateLimit: 5
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
    while True:
        randomName = f"Client{random.randint(1, 1000)}"
        if randomName not in Globals.ConnectedClients:
            return randomName

async def registerClient(clientName, writer):
    async with Globals.lock:
        Globals.ConnectedClients[clientName] = writer
        Globals.ClientCount += 1
        Globals.LastClientHeartbeat[clientName] = time.time()

async def unregisterClient(clientName):
    async with Globals.lock:
        if clientName in Globals.ConnectedClients:
            del Globals.ConnectedClients[clientName]
            Globals.ClientCount -= 1
            del Globals.LastClientHeartbeat[clientName]

async def CheckHeartbeat():
    """
    This Function checks for heartbeat messages from clients.
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
        # Check for rate limiting
        currentTime = time.time()
        if clientName not in clientMessageTimestamps:
            clientMessageTimestamps[clientName] = []
        clientMessageTimestamps[clientName] = [timestamp for timestamp in clientMessageTimestamps[clientName] if currentTime - timestamp < TimeWindow]
        if len(clientMessageTimestamps[clientName]) >= RateLimit:
            response = "Rate limit exceeded. Please wait before sending more messages."
            writer.write(response.encode())
            await writer.drain()
            continue
        clientMessageTimestamps[clientName].append(currentTime)
        if message.startswith("!"):
            await handleCommand(message, writer, clientName, addr)
        else:
            await broadcastMessage(clientName, message)

async def handleCommand(message, writer, clientName, addr):
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
    signalColor = "\033[93m"
    resetColor = "\033[0m"
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
    """
    signalColor = "\033[93m"
    resetColor = "\033[0m"
    messageFormat = f"{signalColor}[BROADCAST]{resetColor} {message}"
    async with Globals.lock:
        for writer in Globals.ConnectedClients.values():
            try:
                writer.write(messageFormat.encode())
                await writer.drain()
            except Exception:
                pass

async def ServerCommandCheck():
    """
    Checks for server-side commands (run in a background task).
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