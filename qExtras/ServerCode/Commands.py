import datetime
import Globals

class Commands:
    # Command Color
    SignalColor = "\033[93m" # Yellow
    resetColor = "\033[0m" # Reset color


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
        """
        return f"{self.SignalColor}Available commands: !whoami, !help, !time, !list{self.resetColor}"

    def servertime(self, addr):
        """
        Returns the current server time.
        """
        return f"{self.SignalColor}The current server time is: {self.Timestamp()}{self.resetColor}"

    def whoami(self, ClientName, ClientAddr):
        """
        Returns the client's name and address.
        Args:
            ClientName (str): The client's name.
            ClientAddr (tuple): The client's address.
        """
        return f"{self.SignalColor}Your name is {ClientName} and you are connected from {ClientAddr}{self.resetColor}"

    def ListActiveClients(self, ClientName):
        """
        Returns a comma-separated list of active clients.
        Args:
            ClientName (str): The name of the requesting client.
        """
        return f"{self.SignalColor}Active Clients: {', '.join(Globals.ConnectedClients.keys())}{self.resetColor}"
