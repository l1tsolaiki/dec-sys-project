import argparse
import logging
import os
import signal
import socketserver
import threading

import db
import encryption
import models
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
        logging.info("Handle request")
        contact = db.DB.fetch_contact_by_ip(self.client_address[0])
        tcp = transport.Transport(self.request, contact)
        data = tcp.receive_all()
        logging.info(
            "Received message from ip=%s, msg=%s", self.client_address[0], data
        )
        self.dispatch(data)
        # just send back the same data, but upper-cased
        tcp.send(data)

    def dispatch(self, data):
        msg_type = data["type"]
        if msg_type == models.MessageType.MESSAGE.value:
            self.handle_message(data)

    def handle_message(self, data):
        logging.info("Handling message..")
        my_ip = self.request.getsockname()[0]
        if my_ip in data['chain']:
            logging.info('Drop message, because I(%s) am in chain already')
            return
        if my_ip == data['to']:
            self.save_message(data)
            logging.info('Saved message')

    def save_message(self, data):
        body = data['body']

        contact = db.DB.fetch_contact_by_ip(data['from'])
        if contact:
            decrypted = encryption.Encryptor(contact.key).decrypt(bytes(body, encoding='utf-8')).decode('utf-8')
            logging.info('decrypted body: %s', decrypted)


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
            )
            server.shutdown()
            logging.info("Server shut down")

        server_thread = threading.Thread(target=server.serve_forever)
        signal.signal(signal.SIGTERM, signal_handler)
        logging.info("Start server, pid=%s", os.getpid())
        server_thread.start()

        signal.pause()
        server_thread.join()
