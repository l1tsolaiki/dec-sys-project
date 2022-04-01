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


logging.basicConfig(level=logging.INFO, filename='server.log')


class MyTCPHandler(socketserver.BaseRequestHandler):
    '''
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    '''

    def handle(self):
        # self.request is the TCP socket connected to the client
        logging.info('Handle request')
        peer = db.DB.fetch_peer_by_ip(self.client_address[0])
        if not peer:
            logging.error('Cannot handle request: do not have peer with ip=%s', self.client_address[0])
            return
        tcp = transport.Transport(self.request, peer)
        data = tcp.receive_all()
        logging.info(
            'Received message from ip=%s, msg=%s', self.client_address[0], data
        )
        try:
            self.dispatch(data)
        except Exception as exc:  # noqa
            logging.error(str(exc))

    def dispatch(self, data):
        msg_type = data['type']
        peer = db.DB.fetch_peer_by_id(data['from'])
        if not peer:
            db.DB.add_peer_only_required(data['from'], data['from'])
            peer = db.DB.fetch_peer_by_id(data['from'])
        if msg_type == models.MessageType.MESSAGE.value:
            self.handle_message(data, peer)
        elif msg_type == models.MessageType.ACK.value:
            logging.info('HELLOOOO!')

    def handle_message(self, data, peer):
        logging.info('Handling message..')
        my_peer_id = db.get_peer_id()
        if my_peer_id in data['chain']:
            logging.info('Drop message, because I(%s) am in chain already')
            return

        transmitter = transport.Transmitter()

        if my_peer_id == data['to']:
            self.save_message(data)
            logging.info('Saved message')
            msg = {'id': data['id'], 'type': models.MessageType.ACK.value}
            transmitter.transmit(peer, msg)
            return
        transmitter.retransmit(data)

    def save_message(self, data):
        body = data['body']
        decrypted = False

        peer = db.DB.fetch_peer_by_id(data['from'])
        if peer:
            body = (
                encryption.Encryptor(peer.key)
                .decrypt(bytes(body, encoding='utf-8'))
                .decode('utf-8')
            )
            decrypted = True
        else:
            db.DB.add_peer_only_required(data['from'], data['from'])

        db.DB.insert_message(data['id'], data['from'], body, decrypted)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('host')
    parser.add_argument('port', type=int)

    args = parser.parse_args()
    host, port = args.host, args.port

    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((host, port), MyTCPHandler) as server:

        def signal_handler(sig, frame):
            logging.info(
                'Server gracefully shutting down; thread_id=%s',
            )
            server.shutdown()
            logging.info('Server shut down')

        server_thread = threading.Thread(target=server.serve_forever)
        signal.signal(signal.SIGTERM, signal_handler)
        logging.info('Start server, pid=%s', os.getpid())
        server_thread.start()

        signal.pause()
        server_thread.join()
