# Telethon MongoDB Session

This is a [Telethon](https://telethon.dev) session backend which uses MongoDB.

## Installing

```bash
pip3 install telemongo

# or, with poetry

poetry add telemongo
```

## Upgrading

```bash
pip3 install -U telemongo mongoengine

# or, with poetry

poetry add -U telemongo mongoengine
```

## Usage

```python
from telemongo import MongoSession
from telethon import TelegramClient
from mongoengine import connect

api_id = 12345
api_hash = "0123456789abcdef0123456789abcdef"
db = "dbname"
host = f"mongodb://username:pass@mongo_host/{dbname}"

connect(db, host=host)
session = MongoSession(db, host=host)

client = TelegramClient(session, api_id, api_hash)
client.start()
```
