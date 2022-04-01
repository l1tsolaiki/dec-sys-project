#!python3
import socket

import click
import os
import signal
import sqlite3
import subprocess
import sys

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


@click.group()
def cli():
    """CLI app for messaging."""
    pass


@cli.group('daemon')
def daemon_group():
    """Control daemon"""
    pass


@daemon_group.command("up")
def daemon_up():
    try:
        p = subprocess.Popen(
            [sys.executable, "./server.py", consts.DAEMON_HOST, consts.DAEMON_PORT],
            cwd=".",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        try:
            p.wait(timeout=1)
            print(
                f"Error! Subprocess exited with exit code {p.returncode}. "
                f"Check that port is not in use.",
                file=sys.stderr,
            )
            return
        except subprocess.TimeoutExpired:
            # Process did not exit abruptly
            pass

        try:
            db.DB.insert_pid("daemon", p.pid)
        except sqlite3.Error as exc:
            p.kill()
            print(f"Error with DB:\n{str(exc)}")
            return
        print(
            f"Daemon started with pid={p.pid} on {consts.DAEMON_HOST}:{consts.DAEMON_PORT}"
        )
    except PermissionError:
        print(
            f"Could not run daemon. Run:\n"
            f'chmod +x {os.path.abspath("./server.py")}\n'
            f"And try again",
            file=sys.stderr,
        )


@daemon_group.command("down")
def daemon_down():
    res = db.DB.fetch_pid("daemon")

    if res is None:
        print("Daemon is not running")
        return

    pid = res[0]
    print(f"Shutting down daemon with pid={pid} ...")
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"Daemon shut down")
    except ProcessLookupError:
        print("Looks like daemon was not running")
    db.DB.delete_pid("daemon")


@cli.group('contact')
def contacts_group():
    """Manage contacts"""
    pass


@contacts_group.command("add")
@click.argument("name")
@click.argument("ip")
@click.option(
    "--key-file",
    type=str,
    default=None,
    help="Path to file with key for this contact (excludes --key option)",
)
@click.option(
    "--key", type=str, default=None, help="Key for this contact (excludes --key-file)"
)
@click.option("--auto", is_flag=True, help="Automatically generate key")
def add_contact(name, ip, key_file, key, auto):
    if auto:
        contact_key = encryption.generate_key()
        db.DB.add_contact_with_key(name, ip, contact_key)
        return

    if (key_file is None and key is None) or (key_file is not None and key is not None):
        print("Pass only (exactly) one of '--key-file' and '--key'")
        return
    if key:
        contact_key = key
    if key_file:
        with open(key_file, "r") as f:
            f.read()
            contact_key = key
    db.DB.add_contact_with_key(name, ip, bytes(contact_key, encoding='utf-8'))


@contacts_group.command("show")
@click.argument("name", type=str, default=None, required=False)
@click.argument("ip", type=str, default=None, required=False)
@click.option("--show-key", is_flag=True)
def show_contact(name, ip, show_key):

    def display_contacts(contacts: list):
        print(tabulate.tabulate(contacts, headers=['Name', 'IP', 'Key']))

    if not name and not ip:
        all_contacts = db.DB.fetch_all_contacts()
    elif name:
        all_contacts = [db.DB.fetch_contact_by_name(name)]
    else:
        all_contacts = [db.DB.fetch_contact_by_ip(ip)]

    if not all_contacts:
        print('Could not find contacts')
    if show_key:
        all_contacts = list(map(lambda x: x.show_key(), all_contacts))
    display_contacts(list(map(lambda x: x.to_tuple(), all_contacts)))


@cli.group('message')
def message():
    """Manage messaged"""


@message.command("send")
@click.argument("name")
def send_message(name):
    contact = db.DB.fetch_contact_by_name(name)
    if not contact:
        print(f"Could not find contact '{name}'")
        return

    tcp = transport.Transport(transport.Transport.create_socket(), contact).connect()
    text = input("Enter your message: ")
    print(contact, text)
    try:
        tcp.send({"msg": text})
    except socket.timeout:
        print(f"Could not reach {contact.name} on {contact.ip}")


if __name__ == "__main__":
    init()
    cli()
