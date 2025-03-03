import datetime
import Globals
#import asyncio

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
            "list": self.ListActiveClients,
            "pm": self.handlePrivateMessage
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
    
    async def handlePrivateMessage(self, command, writer, clientName):
        parts = command.split(' ', 2)
        if len(parts) < 3:
            response = "Usage: !pm <username> <message>"
        else:
            targetUser, privateMessage = parts[1], parts[2]
            async with Globals.lock:
                if targetUser in Globals.ConnectedClients:
                    targetWriter = Globals.ConnectedClients[targetUser]
                    response = f"{self.SignalColor}Private message from {clientName}:{self.resetColor} {privateMessage}"
                    targetWriter.write(response.encode())
                    await targetWriter.drain()
                    response = "Private message sent."
                else:
                    response = "User not found."
        writer.write(response.encode())
        await writer.drain()