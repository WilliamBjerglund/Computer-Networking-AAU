# Database.py
import sqlite3
import datetime

def InitDB():
    """
    Initializes the flagged_messages database and creates the table if it doesn't exist.
    """
    conn = sqlite3.connect("flagged_messages.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flagged_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ClientName TEXT,
            IPAddress TEXT,
            Message TEXT,
            Timestamp TEXT,
            FlaggedWord TEXT
        )
    ''')
    conn.commit()
    conn.close()

def InsertFlaggedMessage(clientName, ipAddress, message, flaggedWord):
    """
    Inserts a flagged message into the database.
    
    Args:
        clientName (str): The client's name.
        ipAddress (str): The client's IP address.
        message (str): The flagged message content.
        flaggedWord (str): The keyword that triggered the flag.
    """
    conn = sqlite3.connect("flagged_messages.db")
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO flagged_messages (ClientName, IPAddress, Message, Timestamp, FlaggedWord)
        VALUES (?, ?, ?, ?, ?)
    ''', (clientName, ipAddress, message, timestamp, flaggedWord))
    conn.commit()
    conn.close()
