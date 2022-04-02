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

    _CREATE_SETTINGS_TABLE = (
        'CREATE TABLE IF NOT EXISTS settings '
        '(settings_key VARCHAR(50) PRIMARY KEY,'
        'settings_value VARCHAR(50))'
    )

    _CREATE_PEERS_TABLE = (
        'CREATE TABLE IF NOT EXISTS peers'
        ' (peer_id VARCHAR(40) PRIMARY KEY,'
        ' ip VARCHAR(15),'
        ' name VARCHAR(40) NOT NULL UNIQUE,'
        ' key TEXT NOT NULL)'
    )

    _CREATE_MESSAGES_TABLE = (
        'CREATE TABLE IF NOT EXISTS messages'
        ' (id INTEGER PRIMARY KEY AUTOINCREMENT,'
        ' created_at DATETIME DEFAULT CURRENT_TIMESTAMP,'
        ' msg_id VARCHAR(40) NOT NULL,'
        ' sender VARCHAR (40) NOT NULL,'
        ' body TEXT NOT NULL,'
        ' received BOOLEAN NOT NULL,'
        ' seen BOOLEAN NOT NULL,'
        ' decrypted BOOLEAN NOT NULL)'
    )

    _CREATE_MESSAGES_INDEX = 'CREATE INDEX IF NOT EXISTS by_id ON messages(msg_id)'

    _INIT_QUERIES = [
        _CREATE_SETTINGS_TABLE,
        _CREATE_PEERS_TABLE,
        _CREATE_MESSAGES_TABLE,
        _CREATE_MESSAGES_INDEX,
    ]

    """Purge"""

    _DROP_PEERS_TABLE = 'DROP TABLE IF EXISTS peers'
    _DROP_TABLE_MESSAGES = 'DROP TABLE IF EXISTS MESSAGES'
    _DROP_CURSOR = 'UPDATE SETTINGS SET settings_value = null WHERE settings_key = \'cursor\''

    _PURGE_QUERIES = [
        _DROP_PEERS_TABLE,
        _DROP_TABLE_MESSAGES,
        _DROP_CURSOR,
    ]

    """Settings"""

    _INSERT_SETTING = (
        'INSERT INTO settings(settings_key, settings_value) VALUES (:settings_key, :settings_value)'
        ' ON CONFLICT(settings_key) DO UPDATE SET'
        ' settings_value = :settings_value'
        ' WHERE settings_key = :settings_key'
    )

    _DELETE_SETTING = 'DELETE FROM settings WHERE settings_key = :settings_key'

    _FETCH_SETTING = 'SELECT settings_value FROM settings WHERE settings_key = :settings_key'

    """Peers"""

    _INSERT_PEER_WITH_KEY = (
        'INSERT INTO peers (peer_id, name, ip, key) VALUES (:peer_id, :name, :ip, :key)'
    )
    _INSERT_PEER_ONLY_REQUIRED = (
        'INSERT INTO peers (peer_id, name) VALUES (:peer_id, :name)'
    )

    _FETCH_PEER_BY_NAME = 'SELECT peer_id, name, ip, key FROM peers WHERE name = :name'
    _FETCH_PEER_BY_IP = 'SELECT peer_id, name, ip, key FROM peers WHERE ip = :ip'
    _FETCH_PEER_BY_ID = (
        'SELECT peer_id, name, ip, key FROM peers WHERE peer_id = :peer_id'
    )
    _FETCH_ALL_PEERS = 'SELECT peer_id, name, ip, key FROM peers'

    _UPDATE_PEER = (
        'UPDATE peers SET'
        ' peer_id = :new_id,'
        ' name = :new_name,'
        ' ip = :new_ip,'
        ' key = :new_key'
        ' WHERE name = :old_name'
    )

    """Messages"""

    _INSERT_NEW_MESSAGE = (
        'INSERT INTO messages (msg_id, sender, body, received, seen, decrypted)'
        ' VALUES (:msg_id, :sender, :body, :received, :seen, :decrypted)'
    )

    _FETCH_UNREAD_MESSAGES = (
        'SELECT msg_id,'
        ' created_at,'
        ' sender,'
        ' body,'
        ' received,'
        ' seen,'
        ' decrypted'
        ' FROM messages WHERE id > :id'
        ' ORDER BY id'
    )

    _FETCH_ALL_MESSAGES = (
        'SELECT msg_id,'
        ' created_at,'
        ' sender,'
        ' body,'
        ' received,'
        ' seen'
        ' decrypted'
        ' FROM messages ORDER BY id LIMIT :limit'
    )

    _UPDATE_MESSAGE_RECEIVED = (
        'UPDATE messages SET received = true WHERE msg_id = :msg_id'
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

    @staticmethod
    def purge():
        with get_cursor() as cursor:
            for query in DB._PURGE_QUERIES:
                cursor.execute(query)

    """Settings"""

    @staticmethod
    def insert_setting(key: str, value: str):
        return DB._execute(DB._INSERT_SETTING, settings_key=key, settings_value=value)

    @staticmethod
    def fetch_setting(key):
        return DB._execute_fetchone(DB._FETCH_SETTING, settings_key=key)

    @staticmethod
    def delete_setting(key):
        return DB._execute_fetchone(DB._DELETE_SETTING, settings_key=key)

    """Peers"""

    @staticmethod
    def add_peer_with_key(peer_id: str, name: str, ip: str, key: str):
        return DB._execute(
            DB._INSERT_PEER_WITH_KEY, peer_id=peer_id, name=name, ip=ip, key=key
        )

    @staticmethod
    def add_peer_only_required(peer_id: str, name: str):
        return DB._execute(DB._INSERT_PEER_ONLY_REQUIRED, peer_id=peer_id, name=name)

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
    def fetch_peer_by_id(peer_id: str):
        row = DB._execute_fetchone(DB._FETCH_PEER_BY_ID, peer_id=peer_id)
        peer = None
        if row:
            peer = models.Peer(*row)
        return peer

    @staticmethod
    def fetch_all_peers():
        rows = DB._execute_fetchall(DB._FETCH_ALL_PEERS)
        return [models.Peer(*row) for row in rows]

    @staticmethod
    def update_peer(old_name, new_id, new_name, new_ip, new_key):
        return DB._execute(
            DB._UPDATE_PEER,
            old_name=old_name,
            new_id=new_id,
            new_name=new_name,
            new_ip=new_ip,
            new_key=new_key,
        )

    """Messages"""

    @staticmethod
    def insert_message(
        msg_id: str, sender: str, body: str, received=False, seen=False, decrypted=False
    ):
        return DB._execute(
            DB._INSERT_NEW_MESSAGE,
            msg_id=msg_id,
            sender=sender,
            body=body,
            received=received,
            seen=seen,
            decrypted=decrypted,
        )

    @staticmethod
    def fetch_all_messages(limit):
        return DB._execute_fetchall(DB._FETCH_ALL_MESSAGES, limit=limit)

    @staticmethod
    def fetch_messages_by_cursor(cursor):
        return DB._execute_fetchall(DB._FETCH_UNREAD_MESSAGES, id=cursor)

    @staticmethod
    def update_message_received(msg_id):
        return DB._execute(DB._UPDATE_MESSAGE_RECEIVED, msg_id=msg_id)


def get_peer_id():
    return DB.fetch_setting('peer_id')[0]


def get_msg_cursor():
    cursor = DB.fetch_setting('cursor')
    return cursor[0] if cursor else None


def update_msg_cursor(cursor):
    return DB.insert_setting('cursor', cursor)
