import socket
import threading
import datetime

# Server code
def Timestamp():
    """
    This function returns the current time and date.
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def HandleClient(ClientSocket, addr):
    """
    This function connects to one client and handle its communication.
    """
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

                # Check if the command exists in the dictionary
                if command in CommandDict:
                    response = CommandDict[command](addr)
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
    print(f"[{Timestamp()}] Connection closed: {addr}")
    ClientSocket.close()


# defining command functions
def whoami(addr):
    """
    this function returns the address of the client.

    Args:
    addr (tuple): the address of the client
    """
    return f"you are connected from {addr}"

def commandhelp(addr):
    """
    this function returns the list of commands available.

    Args:
    addr (tuple): the address of the client
    """
    return "Available commands: !whoami, !help, !time"

def servertime(addr):
    """
    this function returns the current time and date.

    Args:
    addr (tuple): the address of the client
    """
    return f"The current server time is: {Timestamp()}"


# Command Dictionary to easily add more commands
CommandDict = {
    "whoami": whoami,
    "help": commandhelp,
    "time": servertime

}

# Now we want to setup the server
ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the server to the HotSpot
