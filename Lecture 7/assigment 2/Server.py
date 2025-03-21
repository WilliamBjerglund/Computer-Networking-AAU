import socket
import sqlite3
import os
import threading

# Configuration
DATABASE = 'file_storage.db'
FILE_STORAGE_DIR = 'files'
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 9000

def init_db():
    """Initialize the database and create the file metadata table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_length INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            client_ip TEXT,
            client_port INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def handle_client(client_socket, client_address):
    try:
        # Wrap the socket in a file-like object for easier line-based reading
        fileobj = client_socket.makefile('rwb')
        command = fileobj.readline().decode().strip()
        print(f"DEBUG: Received command: {repr(command)} from {client_address}")
        if command == 'SEND_FILE':
            receive_file(fileobj, client_socket, client_address)
        elif command == 'LIST_FILES':
            send_file_list(client_socket)
        elif command.startswith('SEARCH:'):
            search_query = command.split('SEARCH:')[1].strip()
            search_files(client_socket, search_query)
        else:
            client_socket.sendall(b'Unknown command.\n')
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()

def receive_file(fileobj, client_socket, client_address):
    """
    Receives a file from the client, saves it, and stores metadata in the database.
    Expected sequence (each message ends with a newline):
      1. Filename.
      2. File size as a string.
      3. File data (raw bytes, read based on file size).
    """
    # Receive the filename
    filename = fileobj.readline().decode().strip()
    if not filename:
        client_socket.sendall(b'Filename not provided.\n')
        return

    # Receive file size and convert to integer
    file_size_data = fileobj.readline().decode().strip()
    try:
        file_size = int(file_size_data)
    except ValueError:
        client_socket.sendall(b'Invalid file size.\n')
        return

    # Ensure the file storage directory exists
    if not os.path.exists(FILE_STORAGE_DIR):
        os.makedirs(FILE_STORAGE_DIR)
    file_path = os.path.join(FILE_STORAGE_DIR, filename)

    # Receive file data (raw bytes) exactly file_size bytes
    bytes_received = 0
    with open(file_path, 'wb') as f:
        while bytes_received < file_size:
            # Calculate how many bytes are left to read
            to_read = min(4096, file_size - bytes_received)
            chunk = fileobj.read(to_read)
            if not chunk:
                break
            f.write(chunk)
            bytes_received += len(chunk)

    # Verify file size and insert metadata into the database
    actual_file_length = os.path.getsize(file_path)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO file_metadata (filename, file_path, file_length, client_ip, client_port)
        VALUES (?, ?, ?, ?, ?)
    ''', (filename, file_path, actual_file_length, client_address[0], client_address[1]))
    conn.commit()
    conn.close()

    client_socket.sendall(b'File received and metadata stored.\n')

def send_file_list(client_socket):
    """Queries the database for all file records and sends the list back to the client."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM file_metadata')
    rows = cursor.fetchall()
    conn.close()

    response = "Stored Files:\n"
    for row in rows:
        response += (f"ID: {row[0]}, Filename: {row[1]}, Path: {row[2]}, "
                     f"Length: {row[3]}, Timestamp: {row[4]}, "
                     f"Client: {row[5]}:{row[6]}\n")
    client_socket.sendall(response.encode())

def search_files(client_socket, query):
    """Searches the database for files with filenames matching the query and sends the results."""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM file_metadata WHERE filename LIKE ?', ('%' + query + '%',))
    rows = cursor.fetchall()
    conn.close()

    response = "Search Results:\n"
    for row in rows:
        response += (f"ID: {row[0]}, Filename: {row[1]}, Path: {row[2]}, "
                     f"Length: {row[3]}, Timestamp: {row[4]}, "
                     f"Client: {row[5]}:{row[6]}\n")
    client_socket.sendall(response.encode())

def main():
    init_db()
    if not os.path.exists(FILE_STORAGE_DIR):
        os.makedirs(FILE_STORAGE_DIR)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    print(f"Server listening on {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        # Handle each client connection in a new thread
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

if __name__ == '__main__':
    main()
