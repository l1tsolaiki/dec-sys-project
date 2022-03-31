#!python3

import click
import contextlib
import os
import signal
import sqlite3
import subprocess
import sys

import queries

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

DB_NAME = 'messenger.db'
DAEMON_HOST = 'localhost'
DAEMON_PORT = '41479'


@contextlib.contextmanager
def get_cursor():
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn.cursor()
    finally:
        conn.commit()


def init():
    if not os.path.exists(DB_NAME):
        with get_cursor() as cursor:
            for query in queries.INIT_QUERIES:
                cursor.execute(query)


@click.group()
def cli():
    """CLI app for messaging.
    """
    pass


@click.command()
def daemon_up():
    try:
        p = subprocess.Popen([sys.executable, './server.py', DAEMON_HOST, DAEMON_PORT],
                             cwd=".",
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,)
        try:
            p.wait(timeout=1)
            print(f'Error! Subprocess exited with exit code {p.returncode}. '
                  f'Check that port is not in use.', file=sys.stderr)
            return
        except subprocess.TimeoutExpired:
            # Process did not exit abruptly
            pass

        with get_cursor() as cursor:
            try:
                cursor.execute(queries.INSERT_PID, {'pid': p.pid, 'daemon': 'daemon'})
            except sqlite3.Error as exc:
                p.kill()
                print(f'Error with DB:\n{str(exc)}')
                return
        print(f'Daemon started with pid={p.pid} on {DAEMON_HOST}:{DAEMON_PORT}')
    except PermissionError:
        print(f'Could not run daemon. Run:\n'
              f'chmod +x {os.path.abspath("./server.py")}\n'
              f'And try again', file=sys.stderr)


@click.command()
def daemon_down():
    with get_cursor() as cursor:
        res = cursor.execute(
            queries.DELETE_PID, {'daemon': 'daemon'}
        ).fetchone()

        if res is None:
            print('Daemon is not running')
            return

        pid = res[0]
        print(f'Shutting down daemon with pid={pid} ...')
        try:
            os.kill(pid, signal.SIGTERM)
            print(f'Daemon shut down')
        except ProcessLookupError:
            print('Looks like daemon was not running')


@click.command()
@click.argument('name')
@click.argument('ip')
def add_contact(name, ip):
    print(f'You passed: {name}, {ip}')


cli.add_command(add_contact)
cli.add_command(daemon_up, name='daemon-up')
cli.add_command(daemon_down, name='daemon-down')

if __name__ == '__main__':
    init()
    cli()
