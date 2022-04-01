import argparse
import logging
import signal
import socketserver
import threading

import db
import transport


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
        contact = db.DB.fetch_contact_by_ip(self.client_address[0])
        tcp = transport.Transport(self.request, contact)
        data = tcp.receive_all()
        logging.info("{} wrote:".format(self.client_address[0]))
        logging.info(data)
        # just send back the same data, but upper-cased
        tcp.send(data)


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

        server_thread = threading.Thread(target=server.serve_forever)
        signal.signal(signal.SIGTERM, signal_handler)
        server_thread.start()

        signal.pause()
        server_thread.join()
