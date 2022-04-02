# must import it first
import log

import logging
import os
import signal
import sqlite3
import subprocess
import sys
import uuid

import click
import tabulate

import db
import consts
import encryption
import models
import transport

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


def init():
    if not os.path.exists(consts.DB_NAME):
        db.DB.initialize()
        db.DB.insert_setting('peer_id', uuid.uuid4().hex)
        return True
    return False


@click.group()
def cli():
    """CLI app for messaging."""
    pass


@cli.command('purge')
def purge():
    db.DB.purge()


@cli.command('init')
def purge():
    db.DB.initialize()


@cli.group('id')
def id_group():
    """ "Manipulate your ID"""


@id_group.command('set')
@click.argument('id')
def set_id(id):
    db.DB.insert_setting('peer_id', id)


@cli.group('daemon')
def daemon_group():
    """Control daemon"""
    pass


@daemon_group.command('up')
def daemon_up():
    try:
        p = subprocess.Popen(
            [sys.executable, './server.py', consts.DAEMON_HOST, consts.DAEMON_PORT],
            cwd='.',
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        try:
            p.wait(timeout=1)
            logging.info(
                f'Error! Subprocess exited with exit code {p.returncode}. '
                f'Check that port is not in use.',
            )
            return
        except subprocess.TimeoutExpired:
            # Process did not exit abruptly
            pass

        try:
            db.DB.insert_setting('daemon', p.pid)
        except sqlite3.Error as exc:
            p.kill()
            logging.error(f'Error with DB: %s', str(exc))
            return
        logging.info(
            f'Daemon started with pid=%s on %s:%s',
            p.pid,
            consts.DAEMON_HOST,
            consts.DAEMON_PORT,
        )
    except PermissionError:
        logging.info(
            f'Could not run daemon. Run:\n' f'chmod +x %s\n' f'And try again',
            os.path.abspath('./server.py'),
        )


@daemon_group.command('down')
def daemon_down():
    res = db.DB.fetch_setting('daemon')

    if res is None:
        logging.info('Daemon is not running')
        return

    pid = res[0]
    logging.info(f'Shutting down daemon with pid={pid} ...')
    try:
        os.kill(int(pid), signal.SIGTERM)
        logging.info(f'Daemon shut down')
    except ProcessLookupError:
        logging.info('Looks like daemon was not running')
    db.DB.delete_setting('daemon')


@cli.group('peer')
def peers_group():
    """Manage peers"""
    pass


@peers_group.command('add')
@click.argument('peer_id')
@click.argument('name')
@click.argument('ip')
@click.option(
    '--key-file',
    type=str,
    default=None,
    help='Path to file with key for this peer (excludes --key option)',
)
@click.option(
    '--key', type=str, default=None, help='Key for this peer (excludes --key-file)'
)
@click.option('--auto', is_flag=True, help='Automatically generate key')
def add_peer(peer_id, name, ip, key_file, key, auto):
    if auto:
        peer_key = encryption.generate_key()
        db.DB.add_peer_with_key(peer_id, name, ip, peer_key)
        return

    if (key_file is None and key is None) or (key_file is not None and key is not None):
        logging.info('Pass only (exactly) one of \'--key-file\' and \'--key\'')
        return
    if key:
        peer_key = key
    if key_file:
        with open(key_file, 'r') as f:
            peer_key = f.read().strip()
    db.DB.add_peer_with_key(peer_id, name, ip, peer_key)


@peers_group.command('show')
@click.argument('name', type=str, default=None, required=False)
@click.argument('peer_id', type=str, default=None, required=False)
@click.option('--show-key', is_flag=True)
def show_peer(name, peer_id, show_key):
    def display_peers(peers: list):
        print(tabulate.tabulate(peers, headers=['Peer ID', 'Name', 'IP', 'Key']))

    if not name and not peer_id and not peer_id:
        all_peers = db.DB.fetch_all_peers()
    elif peer_id:
        all_peers = [db.DB.fetch_peer_by_id(peer_id)]
    elif name:
        all_peers = [db.DB.fetch_peer_by_name(name)]
    else:
        all_peers = [db.DB.fetch_peer_by_id(peer_id)]

    if not any(all_peers):
        print('Could not find peers')
        return
    if show_key:
        all_peers = list(map(lambda x: x.show_key(), all_peers))
    display_peers(list(map(lambda x: x.to_tuple(), all_peers)))


@peers_group.command('edit')
@click.argument('peer_name')
@click.option('--id', type=str)
@click.option('--name', type=str)
@click.option('--ip', type=str)
@click.option('--key', type=str)
def edit_peer(peer_name, id, name, ip, key):
    peer = db.DB.fetch_peer_by_name(peer_name)
    if not peer:
        print('No such peer')
        return

    if id:
        peer.peer_id = id
    if name:
        peer.name = name
    if ip:
        peer.ip = ip
    if key:
        peer.key = key
    db.DB.update_peer(peer_name, peer.peer_id, peer.name, peer.ip, peer.key)


@cli.group('message')
def message():
    """Manage messaged"""


@message.command('send')
@click.argument('name')
def send_message(name):
    peer = db.DB.fetch_peer_by_name(name)
    if not peer:
        logging.info('Could not find peer \'%s\'', name)
        return

    text = input('Enter your message: ')
    transmitter = transport.Transmitter()
    msg = {
        'id': uuid.uuid4().hex,
        'type': models.MessageType.MESSAGE.value,
        'body': text,
    }
    db.DB.insert_message(
        msg['id'], db.get_peer_id(), text, received=False, seen=False, decrypted=True
    )
    success = transmitter.transmit(peer, msg)
    if not success:
        logging.warning('Could not transmit message to anybody')
        return
    logging.info('Transmitted msg to %s peers', success)


@message.command('read')
@click.option('-a', '--all', is_flag=True)
@click.option('--limit', type=int)
def read_messages(all, limit):
    def beautify_bools(tpl):
        change_to_sign = lambda x: '✔' if x else '×'
        return (
            tpl[0],
            tpl[1],
            tpl[2],
            tpl[3],
            change_to_sign(tpl[4]),
            change_to_sign(tpl[5]),
            change_to_sign(tpl[6]),
        )

    if all and not limit:
        print('You need to specify \'--limit\' with \'--all\'')
        return

    cursor = int(db.get_msg_cursor())

    if all or not cursor:
        messages = db.DB.fetch_all_messages(limit)
    else:
        messages = db.DB.fetch_messages_by_cursor(cursor)

    if messages:
        assert max([msg[0] for msg in messages]) == messages[-1][0]
        cursor = str(messages[-1][0])
        db.update_msg_cursor(cursor)

    messages = list(map(beautify_bools, messages))
    print(
        tabulate.tabulate(
            messages,
            headers=['ID', 'Sender Peer ID', 'Body', 'Created At', 'Received', 'Seen', 'Decrypted'],
        )
    )


if __name__ == '__main__':
    if init():
        print('\nNew ID was generated for you: {}\n'.format(db.get_peer_id()))
    else:
        print('\nYour ID is {}\n'.format(db.get_peer_id()))
    cli()
