import datetime
import Globals

class Commands:
    def __init__(self):
        # Map command names to methods.
        self.CommandDict = {
            "help": self.commandhelp,
            "whoami": self.whoami,
            "time": self.servertime,
            "list": self.ListActiveClients
        }

    @staticmethod
    def Timestamp():
        """Returns the current time and date."""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def commandhelp(self, addr):
        """
        Returns the list of available commands.
        Args:
            addr (tuple): The client's address.
        """
        return "Available commands: !whoami, !help, !time, !list"

    def servertime(self, addr):
        """
        Returns the current server time.
        Args:
            addr (tuple): The client's address.
        """
        return f"The current server time is: {self.Timestamp()}"

    def whoami(self, ClientName, ClientAddr):
        """
        Returns the client's name and address.
        Args:
            ClientName (str): The client's name.
            ClientAddr (tuple): The client's address.
        """
        return f"Your name is {ClientName} and you are connected from {ClientAddr}"

    def ListActiveClients(self, ClientName):
        """
        Returns a comma-separated list of active clients.
        Args:
            ClientName (str): The name of the requesting client.
        """
        return "Active Clients: " + ", ".join(Globals.ConnectedClients.keys())
