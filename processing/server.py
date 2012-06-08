"""
This is the server code for the gattini analysis client/server
"""

from util.client_server import Server

def main():
    
    image_ids = map(str, range(1, 85741))
    image_ids = map(str, range(85741, 85800))

    PORT = 50070   # Arbitrary non-privileged port

    server = Server(PORT, image_ids)
    server.run()

if __name__ == "__main__":
    main()
