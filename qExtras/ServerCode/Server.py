import socket
import threading
import random
from Commands import CommandDict, Timestamp

def GetLocalIP():
    """
    This function returns the local IP address of the server.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to public DNS to trick the best local network interface to be used
        s.connect(("8.8.8.8", 80)) # Google's public DNS
        LocalIP = s.getsockname()[0]
    except Exception:
        LocalIP = "127.0.0.1" # Fallback to localhost
    finally:
        s.close()
    return LocalIP


# Server Config
HOST = "0.0.0.0" # Currently binds to all network interfaces should change to the Hotspot or pref Host Server IP
PORT = 12345 # change to pref port number
SERVER_IP = GetLocalIP() # Get the local IP address of the server automatically
print(f"[{Timestamp()}] Server detected IP: {SERVER_IP}")

    # This part of config sets the server up so people can have identities on their.
ConnectedClients = {} # stores names of connected clients
ClientCount = 0
lock = threading.Lock() # Prevents race conditions when modifying the ConnectedClients dictionary


# Server code
def HandleClient(ClientSocket, addr):
    """
    This function connects to one client and handle its communication.
    """
    global ClientCount

    #Ask the client for their persona / username
    ClientSocket.send("Enter your name: ".encode())
    ClientName = ClientSocket.recv(1024).decode().strip()
    if not ClientName: # Assign a random name if the client doesn't provide one
        ClientName = f"Client{random.randint(1, 1000)}"

    # Now we want to store the client's name in the dictionary
    with lock:
        ConnectedClients[ClientName] = ClientSocket
        ClientCount += 1

    print(f"[{Timestamp()}] New connection from {addr}")

    
    while True:
        try:
            # Attempt to receive a message from the client.
            message = ClientSocket.recv(1024).decode()
            if not message:
                break
            print(f"[{Timestamp()}] Client ({addr}): {message}")

            # Check if the message is meant to be a command
            if message.startswith("!"):
                command = message[1:].lower()

                # Prevent clients from executing the !broadcast command
                if command == "broadcast":
                    response = "Access Denied: Only the server can broadcast messages."

                # Check if the command exists in the dictionary
                elif command in CommandDict:
                    if command == "whoami":
                        response = CommandDict[command](ClientName, addr) # Pass the client's name and address to the function
                    else:
                        response = CommandDict[command](ClientName)
                else:
                    response = "Invalid command. for help type !help"
            else:
                # If the Message is a regular normal message do nothing
                response = f"[{Timestamp()}] Server received: {message}"
            
            # Send the response back to the client
            ClientSocket.send(response.encode())

        except Exception as e:
            print(f"[{Timestamp()}] Error: {e}")
            break
    
    # Remove client from list on disconnect
    with lock:
        del ConnectedClients[ClientName]
        ClientCount -= 1
    
    # Close the connection
    print(f"[{Timestamp()}] Connection closed: {addr}")
    ClientSocket.close()


# Command only for the server to broadcast a message to all clients
def Broadcast(message):
    """
    Sends a message to all connected clients and ensures only server can do it.
    (Currently technically excessive as normal messages is seen by everyone will maybe change later and make multiple chat rooms and stuff.)
    """
    SignalColor = "\033[93m" # Yellow
    resetColor = "\033[0m" # Reset color

    MessageFormat = f"{SignalColor}[BROADCAST]{resetColor} {message}"

    with lock: 
        for client in ConnectedClients.values():
            try:
                client.send(MessageFormat.encode())
            except:
                pass # Ignore errors if the client is not reachable or disconnected

def ServerCommandCheck():
    """
    This function listen and checks for server-side commands ensuring they are done only by server.
    """
    while True:
        command = input("Server Command: ").strip()
        if command.startswith("!broadcast"):
            message = command[len("!broadcast"):].strip()
            if message:
                Broadcast(message)
                print(f"[{Timestamp()}] Broadcast sent: {message}")
            else:
                print("Usage: !broadcast <message>")
        elif command == "!exit":
            print("Shutting down server...")
            break
        else:
            print("Unknown server command.")


# Now we want to initialize our simple server.
ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    ServerSocket.bind((HOST, PORT))
    ServerSocket.listen(5)
    print(f"[{Timestamp()}] Server started on {SERVER_IP}:{PORT}")

    threading.Thread(target=ServerCommandCheck, daemon=True).start()

    while True:
        ClientSocket, addr = ServerSocket.accept()
        ClientThread = threading.Thread(target=HandleClient, args=(ClientSocket, addr), daemon=True)
        ClientThread.start()
except Exception as e:
    print(f"[{Timestamp()}] Server Error: {e}")
finally:
    ServerSocket.close()
    print(f"[{Timestamp()}] Server closed")
