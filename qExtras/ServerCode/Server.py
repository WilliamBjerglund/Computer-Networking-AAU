import asyncio
import random
import socket
import Globals
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

async def HandleClient(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info('peername')
    # Ask the client for their name
    writer.write("Enter your name: ".encode())
    await writer.drain()
    data = await reader.read(1024)
    clientName = data.decode().strip()

    # Validate the client's name (with asynchronous locking)
    while True:
        async with Globals.lock:
            if not clientName:
                while True:
                    randomName = f"Client{random.randint(1, 1000)}"
                    if randomName not in Globals.ConnectedClients:
                        clientName = randomName
                        break
            while clientName in Globals.ConnectedClients:
                writer.write("Name already taken. Please enter a different name: ".encode())
                await writer.drain()
                data = await reader.read(1024)
                clientName = data.decode().strip()
                if not clientName:
                    while True:
                        randomName = f"Client{random.randint(1, 1000)}"
                        if randomName not in Globals.ConnectedClients:
                            clientName = randomName
                            break
            if clientName not in Globals.ConnectedClients:
                break

    async with Globals.lock:
        Globals.ConnectedClients[clientName] = writer
        Globals.ClientCount += 1

    print(f"[{cmdHandler.Timestamp()}] New connection from {addr}")

    try:
        while True:
            data = await reader.read(1024)
            if not data:
                break
            message = data.decode().strip()
            print(f"[{cmdHandler.Timestamp()}] Client ({addr}): {message}")

            # Check for commands (messages starting with "!")
            if message.startswith("!"):
                command = message[1:].lower()
                if command == "broadcast":
                    response = "Access Denied: Only the server can broadcast messages."
                elif command in cmdHandler.CommandDict:
                    if command == "whoami":
                        response = cmdHandler.CommandDict[command](clientName, addr)
                    else:
                        response = cmdHandler.CommandDict[command](clientName)
                else:
                    response = "Invalid command. for help type !help"
                writer.write(response.encode())
                await writer.drain()
            else:
                # Regular message; broadcast to all clients
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
    except Exception as e:
        print(f"[{cmdHandler.Timestamp()}] Error: {e}")

    # Remove client on disconnect
    async with Globals.lock:
        if clientName in Globals.ConnectedClients:
            del Globals.ConnectedClients[clientName]
            Globals.ClientCount -= 1

    print(f"[{cmdHandler.Timestamp()}] Connection closed: {addr}")
    writer.close()
    await writer.waitClosed()

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
        command = command.strip().lower()
        if command.startswith("!broadcast"):
            message = command[len("!broadcast"):].strip()
            if message:
                await Broadcast(message)
                print(f"[{cmdHandler.Timestamp()}] Broadcast sent: {message}")
            else:
                print("Usage: !broadcast <message>")
        elif command == "!exit":
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

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    try:
        asyncio.run(Main())
    except asyncio.CancelledError:
        print(f"[{cmdHandler.Timestamp()}] Server shutting down gracefully.")