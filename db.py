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
    _CREATE_DAEMON_TABLE = (
        "CREATE TABLE daemon (daemon VARCHAR(10) PRIMARY KEY, pid INTEGER)"
    )

    _CREATE_CONTACTS_TABLE = (
        "CREATE TABLE contacts"
        " (name VARCHAR(40) PRIMARY KEY,"
        " ip VARCHAR(15) NOT NULL UNIQUE,"
        " key TEXT)"
    )

    _INIT_QUERIES = [_CREATE_DAEMON_TABLE, _CREATE_CONTACTS_TABLE]

    _INSERT_PID = (
        "INSERT INTO daemon(daemon, pid) VALUES (:daemon, :pid)"
        " ON CONFLICT(daemon) DO UPDATE SET"
        " pid = :pid"
        " WHERE daemon = :daemon"
    )

    _DELETE_PID = "DELETE FROM daemon WHERE daemon"

    _FIND_PID = "SELECT pid FROM DAEMON WHERE daemon = :daemon"

    _INSERT_CONTACT_WITH_KEY = (
        "INSERT INTO contacts (name, ip, key) VALUES (:name, :ip, :key)"
    )

    _FETCH_CONTACT_BY_NAME = "SELECT name, ip, key FROM contacts WHERE name = :name"
    _FETCH_CONTACT_BY_IP = "SELECT name, ip, key FROM contacts WHERE ip = :ip"

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

    @staticmethod
    def initialize():
        for query in DB._INIT_QUERIES:
            DB._execute(query)

    @staticmethod
    def insert_pid(daemon, pid):
        return DB._execute(DB._INSERT_PID, daemon=daemon, pid=pid)

    @staticmethod
    def fetch_pid(daemon):
        return DB._execute_fetchone(DB._FIND_PID, daemon=daemon)

    @staticmethod
    def delete_pid(daemon):
        return DB._execute_fetchone(DB._DELETE_PID, daemon=daemon)

    @staticmethod
    def add_contact_with_key(name, ip, key):
        return DB._execute(DB._INSERT_CONTACT_WITH_KEY, name=name, ip=ip, key=key)

    @staticmethod
    def fetch_contact_by_name(name):
        row = DB._execute_fetchone(DB._FETCH_CONTACT_BY_NAME, name=name)
        contact = None
        if row:
            contact = models.Contact(*row)
        return contact

    @staticmethod
    def fetch_contact_by_ip(ip):
        row = DB._execute_fetchone(DB._FETCH_CONTACT_BY_NAME, ip=ip)
        contact = None
        if row:
            contact = models.Contact(*row)
        return contact
