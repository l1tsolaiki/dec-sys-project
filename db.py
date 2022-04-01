import contextlib
import sqlite3

import consts
import models


@contextlib.contextmanager
def get_cursor():
    conn = sqlite3.connect(consts.DB_NAME)
    try:
        yield conn.cursor()
    finally:
        conn.commit()


class DB:

    """Init"""

    _CREATE_DAEMON_TABLE = (
        "CREATE TABLE daemon (daemon VARCHAR(10) PRIMARY KEY, pid INTEGER)"
    )

    _CREATE_CONTACTS_TABLE = (
        "CREATE TABLE contacts"
        " (ip VARCHAR(15) PRIMARY KEY,"
        " name VARCHAR(40) NOT NULL UNIQUE,"
        " key TEXT NOT NULL)"
    )

    _CREATE_MESSAGES_TABLE = (
        "CREATE TABLE messages"
        " (id VARCHAR(40) PRIMARY KEY,"
        " sender VARCHAR (15) NOT NULL REFERENCES contacts(ip) ON DELETE CASCADE ON UPDATE CASCADE,"
        " body TEXT NOT NULL,"
        " received BOOLEAN NOT NULL DEFAULT FALSE,"
        " seen BOOLEAN NOT NULL DEFAULT FALSE,"
        " decrypted BOOLEAN)"
    )

    _INIT_QUERIES = [
        _CREATE_DAEMON_TABLE,
        _CREATE_CONTACTS_TABLE,
        _CREATE_MESSAGES_TABLE,
    ]

    """Daemon"""

    _INSERT_PID = (
        "INSERT INTO daemon(daemon, pid) VALUES (:daemon, :pid)"
        " ON CONFLICT(daemon) DO UPDATE SET"
        " pid = :pid"
        " WHERE daemon = :daemon"
    )

    _DELETE_PID = "DELETE FROM daemon WHERE daemon"

    _FIND_PID = "SELECT pid FROM DAEMON WHERE daemon = :daemon"

    """Contacts"""

    _INSERT_CONTACT_WITH_KEY = (
        "INSERT INTO contacts (name, ip, key) VALUES (:name, :ip, :key)"
    )

    _FETCH_CONTACT_BY_NAME = "SELECT name, ip, key FROM contacts WHERE name = :name"
    _FETCH_CONTACT_BY_IP = "SELECT name, ip, key FROM contacts WHERE ip = :ip"
    _FETCH_ALL_CONTACTS = "SELECT name, ip, key FROM contacts"

    """Messages"""
    _INSERT_NEW_MESSAGE = "INSERT INTO messages (id, sender, body, decrypted) VALUES (:id, :sender, :body, :decrypted)"

    @staticmethod
    def _execute(query, **kwargs):
        with get_cursor() as cursor:
            cursor.execute(query, kwargs)

    @staticmethod
    def _execute_fetchall(query, **kwargs):
        with get_cursor() as cursor:
            return cursor.execute(query, kwargs).fetchall()

    @staticmethod
    def _execute_fetchone(query, **kwargs):
        with get_cursor() as cursor:
            return cursor.execute(query, kwargs).fetchone()

    """Init"""

    @staticmethod
    def initialize():
        for query in DB._INIT_QUERIES:
            DB._execute(query)

    """Daemon"""

    @staticmethod
    def insert_pid(daemon: str, pid):
        return DB._execute(DB._INSERT_PID, daemon=daemon, pid=pid)

    @staticmethod
    def fetch_pid(daemon):
        return DB._execute_fetchone(DB._FIND_PID, daemon=daemon)

    @staticmethod
    def delete_pid(daemon):
        return DB._execute_fetchone(DB._DELETE_PID, daemon=daemon)

    """Contacts"""

    @staticmethod
    def add_contact_with_key(name: str, ip: str, key: str):
        return DB._execute(DB._INSERT_CONTACT_WITH_KEY, name=name, ip=ip, key=key)

    @staticmethod
    def fetch_contact_by_name(name: str):
        row = DB._execute_fetchone(DB._FETCH_CONTACT_BY_NAME, name=name)
        contact = None
        if row:
            contact = models.Contact(*row)
        return contact

    @staticmethod
    def fetch_contact_by_ip(ip: str):
        row = DB._execute_fetchone(DB._FETCH_CONTACT_BY_IP, ip=ip)
        contact = None
        if row:
            contact = models.Contact(*row)
        return contact

    @staticmethod
    def fetch_all_contacts():
        rows = DB._execute_fetchall(DB._FETCH_ALL_CONTACTS)
        return [models.Contact(*row) for row in rows]

    """Messages"""

    @staticmethod
    def insert_message(msg_id: str, sender: str, body: str, decrypted: bool):
        return DB._execute(
            DB._INSERT_NEW_MESSAGE,
            id=msg_id,
            sender=sender,
            body=body,
            decrypted=decrypted,
        )
