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

api_id = 12345
api_hash = "0123456789abcdef0123456789abcdef"
host = "mongo://username:pass@mongo_host/dbname"

session = MongoSession(host=host)

client = TelegramClient(session, api_id, api_hash)
client.start()
```
