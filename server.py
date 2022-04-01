#!/usr/bin/python3

import argparse
import logging
import signal
import socketserver
import sys
import threading

from threading import Thread

logging.basicConfig(level=logging.INFO, filename="server.log")


class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        logging.info("{} wrote:".format(self.client_address[0]))
        logging.info(self.data)
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())


def print_thread_id():
    logging.info("Thread id = %s", threading.get_native_id())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("host")
    parser.add_argument("port", type=int)

    args = parser.parse_args()
    host, port = args.host, args.port

    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((host, port), MyTCPHandler) as server:

        def signal_handler(sig, frame):
            logging.info(
                "Server gracefully shutting down; thread_id=%s",
                threading.get_native_id(),
            )
            server.shutdown()
            logging.info("Server shut down")

        server_thread = Thread(target=server.serve_forever)
        signal.signal(signal.SIGTERM, signal_handler)
        server_thread.start()

        signal.pause()
        server_thread.join()
