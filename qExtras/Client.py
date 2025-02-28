import socket
import threading

def receive_messages(sock):
    """
    Continuously listens for incoming messages from the server.
    """
    while True:
        try:
            message = sock.recv(1024).decode()
            if message:
                print(message)
            else:
                # No message means the connection was closed.
                break
        except Exception as e:
            print("Error receiving message:", e)
            break

def main():
    # Change these as needed. If you're testing locally, "127.0.0.1" works.
    SERVER_IP = "127.0.0.1"  
    SERVER_PORT = 12345

    # Create a TCP/IP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((SERVER_IP, SERVER_PORT))
    except Exception as e:
        print("Unable to connect to server:", e)
        return

    # Start a thread to continuously listen for messages from the server
    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()

    # Main loop: get user input and send it to the server
    while True:
        try:
            message = input()
            if message.lower() == "exit":
                break  # exit the client
            client_socket.send(message.encode())
        except Exception as e:
            print("Error sending message:", e)
            break

    client_socket.close()
    print("Disconnected from server.")

if __name__ == "__main__":
    main()
