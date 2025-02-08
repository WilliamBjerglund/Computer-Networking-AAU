import datetime

# Helper function to get the current time and date as per the server.
def Timestamp():
    """
    This function returns the current time and date.
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Here we define the functions that will be called when a command is received.
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

def whoami(ClientName, ClientAddr):
    """
    Returns the client's assigned name and address.

    Args:
    ClientName (str): The name of the client.
    ClientAddr (tuple): The address of the client.
    """
    return f"Your name is {ClientName} and you are connected from {ClientAddr}"



# Command Dictionary to easily add more commands
CommandDict = {
    "whoami": whoami,
    "help": commandhelp,
    "time": servertime

}