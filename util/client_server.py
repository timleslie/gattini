"""
L{Client} and L{Server} classes for batch job processing.

The client/server classes are used to have a single queue to keep track of jobs
which need to be processed. Each job is represented by a single string which
contains all the parameters required for the client to process it.

A very simple text based protocol is used over TCP/IP. A server is started on a
given port on localhost. This server can optionally have a list of jobs
pre-initialised. Clients can then connect either from localhost or a remove
machine. Clientsd can either add jobs to the queue or request a job to process
this continues until a client sends a signal to the server telling it to stop
running. 
"""

import socket
import time

def get_socket(host, port, bind=False):
    """
    Return an open socket connection to a given host and port.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if bind:
        s.bind((host, port))
    else:
        s.connect((host, port))
    return s

class Client:
    """
    A job processing client.
    """

    def __init__(self, host, port, fn):
        """
        Create a client which will connect to a server on C{host:port}. The
        processing function C{fn} is used.

        C{fn} must be a single parameter function which take a string as input.
        """
        self.host = host
        self.port = port
        self.fn = fn

    def _get_socket(self):
        return get_socket(self.host, self.port)

    def stop(self):
        """
        Send a STOP signal to the server
        """
        s = self._get_socket()
        s.send("STOP")
        s.close()

    def process(self):
        """
        Retrieve an item from the server and process it.
        """
        s = self._get_socket()
        s.send("GET")
        data = s.recv(1024)
        if data != "EMPTY":
            print "process", data
            self.fn(data)
        s.close()
        return data != "EMPTY"

    def add(self, param):
        """
        Add a param to the server list
        """
        s = self._get_socket()
        s.send("ADD %d" % param)
        s.close()


class Server:
    """
    A job processing queue deamon server.
    """

    def __init__(self, port, queue=None):
        """
        Create a server located on localhost on a given port. Optionally
        initialise the queue.
        """
        self.port = port
        if queue:
            self.queue = queue
        else:
            self.queue = []

    def run(self):
        """
        Run the main loop of the server.
        """
        self.s = get_socket('', self.port, True)

        while self.s is not None:
            t0 = time.time()
            self.s.listen(1)
            conn, addr = self.s.accept()
            data = conn.recv(1024)
            cmd, param = data.split()[0], "".join(data.split()[1:])

            {"STOP": self.stop,
              "GET": self.get,
              "ADD": self.add}[cmd](conn, param)

            conn.close()
            print time.time() - t0

    def stop(self, conn, param):
        """
        Stop the server process.
        """
        self.s.close()
        self.s = None

    def get(self, conn, param):
        """
        Send the next item in the queue to the connected client.
        """
        if self.queue == []:
            conn.send("EMPTY")
        else:                
            print self.queue[-1], len(self.queue)
            conn.send(self.queue.pop())

    def add(self, conn, param):
        """
        Add an item to the queue.
        """
        self.queue.insert(0, param)
        
