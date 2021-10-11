# Telethon MongoDB Session

This is a [Telethon](https://telethon.dev) session backend which uses MongoDB.

## Installing

```
pip3 install telemongo
```

## Upgrading

```
pip3 install -U telemongo mongoengine
```

## Usage

```python
from mongoengine import connect
from telemongo import MongoSession
from telethon import TelegramClient

api_id = 12345
api_hash = "0123456789abcdef0123456789abcdef"
host = "mongo://username:pass@mongo_host/dbname"

connect('dbname', host=host)
session = MongoSession('dbname', host=host)

client = TelegramClient(session, api_id, api_hash)
client.start()
```
