# Get the simple server and client up and running locally. Test if it works.


# Solution:

# Server code
import socket

# We now want to create a socket object in python
ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Now we want to create a connection to localhost
ServerSocket.bind(('127.0.0.1', 12345))

# Now we want to listen for incoming connections
ServerSocket.listen(1)
print('Listening for connections at port 12345')

# Now we want to accept the incoming connections
ClientSocket, addr = ServerSocket.accept()
print('Connected to: ', addr)

# Now we want to receive data from the client
data = ClientSocket.recv(1024).decode()
print('Received data from client: ', data)

# Now we send data back
ClientSocket.send("Hello from the server".encode())

# Finally we close the connection
ClientSocket.close()
ServerSocket.close()

