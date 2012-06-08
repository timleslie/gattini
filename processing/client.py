"""
This is the client code for the gattini analysis client/server.

It defines 3 actions, each of which communicate with a running server:

stop: stop the server from running
add: add an image id to the servers processing list
process: retrieve an image id from the sever and process it.

"""

from util.client_server import Client
from new_ops import single_phot
HOST = 'mcba11'    # The remote host
PORT = 50070       # The same port as used by the server

def _int_single_phot(s):
    return single_phot(int(s))

def main():
    c = Client(HOST, PORT, _int_single_phot)
    #for i in range(45000, 85741, 3):
    #for i in range(24000, 85741):
    #    c.add(i)

    while(c.process()):
        pass
    #c.stop()

if __name__ == '__main__':
    main()
