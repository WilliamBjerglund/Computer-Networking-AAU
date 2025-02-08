# Continuation of last exercise


# Solution:
import socket

# Create the socket
ClientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Now we want to connect to the server
ClientSocket.connect(("127.0.0.1", 12345))

# Now we want to send some data to the server
ClientSocket.send("Hello from the client".encode())

# Now we want to receive a response
response = ClientSocket.recv(1024).decode()
print("Received response: ", response)

# now we close the socket
print("Client successfully sent data and received response.")
ClientSocket.close()