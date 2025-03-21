import sqlite3

# Define the database name
DB_NAME = "mydatabase.db"

# Connect to the SQLite database (or create it if it doesn't exist)
con = sqlite3.connect(DB_NAME)

# Create a cursor object to interact with the database
cur = con.cursor()

# Execute SQL script to create and populate the Cars table
cur.executescript("""
    DROP TABLE IF EXISTS Cars;
    CREATE TABLE Cars(Id INT, Name TEXT, Price INT);
    INSERT INTO Cars VALUES(1,'Audi',52642);
    INSERT INTO Cars VALUES(2,'Mercedes',57127);
    INSERT INTO Cars VALUES(3,'Skoda',9000);
    INSERT INTO Cars VALUES(4,'Volvo',29000);
    INSERT INTO Cars VALUES(5,'Bentley',350000);
    INSERT INTO Cars VALUES(6,'Citroen',21000);
    INSERT INTO Cars VALUES(7,'Hummer',41400);
    INSERT INTO Cars VALUES(8,'Volkswagen',21600);
""")

# Commit the changes to the database
con.commit()

# Execute SQL query to fetch all Volvo cars
cur.execute("SELECT * FROM Cars WHERE Name = 'Volvo';")
volvo_cars = cur.fetchall()

# Print the output of the Volvo query
print("\nAll Volvo cars in the database:")
for car in volvo_cars:
    print(car)

# Close the database connection
con.close()
