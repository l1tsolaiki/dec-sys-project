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
        "CREATE TABLE settings (settings_key VARCHAR(50) PRIMARY KEY, settings_value VARCHAR(50))"
    )

    _CREATE_PEERS_TABLE = (
        "CREATE TABLE peers"
        " (peer_id VARCHAR(40) PRIMARY KEY,"
        " ip VARCHAR(15) NOT NULL,"
        " name VARCHAR(40) NOT NULL UNIQUE,"
        " key TEXT NOT NULL)"
    )

    _CREATE_MESSAGES_TABLE = (
        "CREATE TABLE messages"
        " (id VARCHAR(40) PRIMARY KEY,"
        " sender VARCHAR (40) NOT NULL REFERENCES peers(peer_id) ON DELETE RESTRICT,"
        " body TEXT NOT NULL,"
        " received BOOLEAN NOT NULL DEFAULT FALSE,"
        " seen BOOLEAN NOT NULL DEFAULT FALSE,"
        " decrypted BOOLEAN)"
    )

    _CREATE_MESSAGES_INDEX = "CREATE INDEX IF NOT EXISTS unread ON messages(seen ASC)"

    _INIT_QUERIES = [
        _CREATE_DAEMON_TABLE,
        _CREATE_PEERS_TABLE,
        _CREATE_MESSAGES_TABLE,
        _CREATE_MESSAGES_INDEX,
    ]

    """Settings"""

    _INSERT_SETTING = (
        "INSERT INTO settings(settings_key, settings_value) VALUES (:settings_key, :settings_value)"
        " ON CONFLICT(settings_key) DO UPDATE SET"
        " settings_value = :settings_value"
        " WHERE settings_key = :settings_key"
    )

    _DELETE_SETTING = "DELETE FROM settings WHERE settings_key = :settings_key"

    _FIND_PID = "SELECT settings_value FROM settings WHERE settings_key = :settings_key"

    """Peers"""

    _INSERT_PEER_WITH_KEY = (
        "INSERT INTO peers (id, name, ip, key) VALUES (:peer_id, :name, :ip, :key)"
    )
    _INSERT_PEER_WITHOUT = (
        "INSERT INTO peers (id, name, ip, key) VALUES (:peer_id, :name, :ip, :key)"
    )

    _FETCH_PEER_BY_NAME = "SELECT name, ip, key FROM peers WHERE name = :name"
    _FETCH_PEER_BY_IP = "SELECT name, ip, key FROM peers WHERE ip = :ip"
    _FETCH_ALL_PEERS = "SELECT name, ip, key FROM peers"

    """Messages"""
    _INSERT_NEW_MESSAGE = (
        "INSERT INTO messages (id, sender, body, decrypted)"
        " VALUES (:id, :sender, :body, :decrypted)"
    )

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
        with get_cursor() as cursor:
            for query in DB._INIT_QUERIES:
                cursor.execute(query)

    """Daemon"""

    @staticmethod
    def insert_setting(key: str, value: str):
        return DB._execute(DB._INSERT_SETTING, settings_key=key, settings_value=value)

    @staticmethod
    def fetch_setting(key):
        return DB._execute_fetchone(DB._FIND_PID, settings_key=key)

    @staticmethod
    def delete_setting(key):
        return DB._execute_fetchone(DB._DELETE_SETTING, settings_key=key)

    """Peers"""

    @staticmethod
    def add_peer_with_key(peer_id: str, name: str, ip: str, key: str):
        return DB._execute(DB._INSERT_PEER_WITH_KEY, peer_id=peer_id, name=name, ip=ip, key=key)

    @staticmethod
    def fetch_peer_by_name(name: str):
        row = DB._execute_fetchone(DB._FETCH_PEER_BY_NAME, name=name)
        peer = None
        if row:
            peer = models.Peer(*row)
        return peer

    @staticmethod
    def fetch_peer_by_ip(ip: str):
        row = DB._execute_fetchone(DB._FETCH_PEER_BY_IP, ip=ip)
        peer = None
        if row:
            peer = models.Peer(*row)
        return peer

    @staticmethod
    def fetch_all_peers():
        rows = DB._execute_fetchall(DB._FETCH_ALL_PEERS)
        return [models.Peer(*row) for row in rows]

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


def get_peer_id():
    return DB.fetch_setting('peer_id')
