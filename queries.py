_CREATE_DAEMON_TABLE = (
    'CREATE TABLE daemon'
    ' (daemon VARCHAR(10) PRIMARY KEY,'
    ' pid INTEGER)'
)

_CREATE_CONTACTS_TABLE = (
    'CREATE TABLE contacts'
    ' (name VARCHAR(40) PRIMARY KEY,'
    ' ip VARCHAR(15) NOT NULL,'
    ' key VARCHAR(100))'
)

INIT_QUERIES = [_CREATE_DAEMON_TABLE,
                _CREATE_CONTACTS_TABLE]

INSERT_PID = (
    'INSERT INTO daemon(daemon, pid) VALUES (:daemon, :pid)'
    ' ON CONFLICT DO UPDATE SET'
    ' pid = :pid'
    ' WHERE daemon = :daemon'
)

DELETE_PID = (
    'DELETE FROM daemon WHERE'
    ' daemon = :daemon'
    ' RETURNING pid'
)

FIND_PID = (
    'SELECT pid FROM DAEMON WHERE'
    ' daemon = :daemon'
)
