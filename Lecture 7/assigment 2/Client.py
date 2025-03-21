import socket
import os
import argparse

# Server configuration
SERVER_IP = '127.0.0.1'  # Change this if your server is on another host
SERVER_PORT = 9000

def send_file(filename):
    if not os.path.exists(filename):
        print("File not found!")
        return
    file_size = os.path.getsize(filename)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, SERVER_PORT))
        # Indicate that we are sending a file, followed by newline
        s.sendall(b'SEND_FILE\n')
        # Send the filename and file size with newlines
        s.sendall((filename + "\n").encode())
        s.sendall((str(file_size) + "\n").encode())
        # Send the file content in chunks (raw bytes)
        with open(filename, 'rb') as f:
            while True:
                data = f.read(4096)
                if not data:
                    break
                s.sendall(data)
        # Receive server response
        response = s.recv(4096)
        print(response.decode())

def list_files():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, SERVER_PORT))
        s.sendall(b'LIST_FILES\n')
        response = s.recv(4096)
        print(response.decode())

def search_files(query):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((SERVER_IP, SERVER_PORT))
        command = f'SEARCH:{query}\n'
        s.sendall(command.encode())
        response = s.recv(4096)
        print(response.decode())

def main():
    parser = argparse.ArgumentParser(
        description="Client for file server: send files, list stored files, or search for files."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subparser for sending files
    send_parser = subparsers.add_parser("send", help="Send a file to the server")
    send_parser.add_argument("filename", help="Path to the file to be sent")

    # Subparser for listing files
    list_parser = subparsers.add_parser("list", help="List all stored files on the server")

    # Subparser for searching files
    search_parser = subparsers.add_parser("search", help="Search for a file by filename")
    search_parser.add_argument("query", help="Search query for filename")

    args = parser.parse_args()

    if args.command == "send":
        send_file(args.filename)
    elif args.command == "list":
        list_files()
    elif args.command == "search":
        search_files(args.query)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
