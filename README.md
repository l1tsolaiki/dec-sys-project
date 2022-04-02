# decentralized messenger

## Description
This P2P messenger uses symmetric encryption (Fernet), therefore
in order to communicate with each other both peers have to know
shared key in advance (although it is possible for receiver to
not know key advance: in this case body of the message will not
be decrypted until the key is known, however the message itself
will be stored)

Main components are:
- CLI - interact with DB, send messages
- Daemon (server) - receive, store and forward messages
- DB sqlite3 - store all data

## Usage

All examples assume `alias cli='python3 main.py`

### Peers
- `cli` - show help and view available commands
- `cli peer add 3042ed16e7754d9c85834f7f3e908e5b wowser 192.168.1.88 --auto` -
 add peer with id *3042ed16e7754d9c85834f7f3e908e5b*, name *wowser*, 
 ip *192.168.1.88* and automatically generate key for him.
- `cli peer edit wowser --key couTtHiDysBpOazleFq9-cWRBIqBihDL5TFrVgGNOf0=` - edit peer: change key
- `cli peer edit wowser --name darling` - change name of peer

### Daemon
- `cli daemon up` - start daemon to receive messages
- `cli daemon down` - stop daemon

### Messages
- `cli message send darling` - send message to *darling*
- `cli message read` - read unread messages
- `cli message read --all --limit 50` - read all messages (from
 beginning, limit 50)

### Storage manipulation
- `cli purge` - drop all tables, except for `settings` table
- `cli init` - run init queries
- `cli id set <id>` - manually set your peer id to `<id>`
