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
                break
        except Exception as e:
            print("Error receiving message:", e)
            break

def main():
    SERVER_IP = "127.0.0.1"  
    SERVER_PORT = 12345

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        client_socket.connect((SERVER_IP, SERVER_PORT))
    except Exception as e:
        print("Unable to connect to server:", e)
        return

    # Handshake: receive the prompt, then send the name.
    initial_prompt = client_socket.recv(1024).decode()
    name = input(initial_prompt)
    client_socket.send(name.encode())

    # Now start the thread to continuously receive messages.
    threading.Thread(target=receive_messages, args=(client_socket,), daemon=True).start()

    # Main loop to send messages
    while True:
        try:
            message = input()
            if message.lower() == "exit":
                break
            client_socket.send(message.encode())
        except Exception as e:
            print("Error sending message:", e)
            break

    client_socket.close()
    print("Disconnected from server.")

if __name__ == "__main__":
    main()
