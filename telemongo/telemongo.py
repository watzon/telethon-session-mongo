import datetime

from mongoengine.context_managers import switch_db
from mongoengine import Document, StringField, IntField, BinaryField, connect

from telethon import utils
from telethon.tl import types
from telethon.crypto import AuthKey
from telethon.sessions.memory import MemorySession, _SentFileType
from telethon.tl.types import InputPhoto, InputDocument, PeerUser, PeerChat, PeerChannel

# Database version
CURRENT_VERSION = 1

class Entity(Document):
    id = IntField(primary_key=True)
    hash = IntField(required=True)
    username = StringField()
    phone = StringField()
    name = StringField()

class SentFile(Document):
    id = IntField(primary_key=True)
    md5_digest = BinaryField()
    file_size = IntField()
    type = IntField()
    hash = IntField()

class Session(Document):
    dc_id = IntField()
    server_address = StringField()
    port = IntField()
    auth_key = BinaryField()
    takeout_id = IntField()

class UpdateState(Document):
    id = IntField(primary_key=True)
    pts = IntField()
    qts = IntField()
    date = IntField()
    seq = IntField()

class Version(Document):
    version = IntField()

class MongoSession(MemorySession):
    def __init__(self, database, **kwargs):
        super().__init__()
        self.save_entities = True
        self.database = database

        connect(database, alias=database, **kwargs)

        # Do a version check
        with switch_db(Version, database) as _Version:
            version_count = _Version.objects.count()
            if version_count < 1:
                # Add the first version record
                _Version(version=CURRENT_VERSION).save()
            else:
                # Check if the version is below the current version
                lt_versions = _Version.objects(version__lt=CURRENT_VERSION)
                if len(lt_versions) > 0:
                    version = _Version.objects().order_by('version').first().version
                    self._update_database(old=version)
                    # Delete old versions
                    for version in lt_versions:
                        version.delete()

        # See if we have any previous sessions
        with switch_db(Session, database) as _Session:
            session_count = _Session.objects.count()
            print(session_count)
            if session_count > 0:
                session = _Session.objects.first()
                self._dc_id = session.dc_id
                self._server_address = session.server_address
                self._port = session.port
                self._takeout_id = session.takeout_id
                self._auth_key = AuthKey(data=session.auth_key)

    def clone(self, to_instance=None):
        cloned = super().clone(to_instance)
        cloned.save_entities = self.save_entities
        return cloned

    def _upgrade_database(self, old):
        # Nothing to be done here yet. Just a good idea to
        # have it in place.
        pass

    def set_dc(self, dc_id, server_address, port):
        super().set_dc(dc_id, server_address, port)
        self._update_session_table()

        # Fetch the auth key corresponding to this data center
        row = Session.objects.first()
        if row and row.auth_key:
            self._auth_key = AuthKey(data=row.auth_key)
        else:
            self._auth_key = None

    @MemorySession.auth_key.setter
    def auth_key(self, value):
        self._auth_key = value
        self._update_session_table()

    @MemorySession.takeout_id.setter
    def takeout_id(self, value):
        self._takeout_id = value
        self._update_session_table()


    def _update_session_table(self):
        with switch_db(Session, self.database) as _Session:
            for session in Session.objects:
                session.delete()
            _Session(dc_id=self._dc_id,
                    server_address=self._server_address,
                    port=self._port,
                    auth_key=self._auth_key.key if self._auth_key else b'',
                    takeout_id=self._takeout_id).save()

    def get_update_state(self, entity_id):
        with switch_db(UpdateState, self.database) as _UpdateState:
            row = _UpdateState.objects(id=entity_id).first()
            if row:
                date = datetime.datetime.fromtimestamp(date, tz=datetime.timezone.utc)
                return types.updates.State(row.pts, row.qts, row.date, row.seq, unread_count=0)

    def set_update_state(self, entity_id, state):
        with switch_db(UpdateState, self.database) as _UpdateState:
            return _UpdateState(entity_id=entity_id,
                               pts=state.pts,
                               qts=state.qts,
                               date=state.date.timestamp(),
                               seq=state.seq()).save()

    def save(self):
        pass

    def close(self):
        pass

    def delete(self):
        with switch_db(Session, self.database) as _Session:
            sess = _Session.objects(auth_key=self._auth_key.key).first()
            if sess:
                sess.delete()

    @classmethod
    def list_sessions(cls):
        with switch_db(Session, self.database) as _Session:
            return _Session.objects

    def process_entities(self, tlo):
        with switch_db(Entity, self.database) as _Entity:
            if not self.save_entities:
                return

            rows = self._entities_to_rows(tlo)
            if not rows:
                return

            for row in rows:
                _Entity(id=row[0],
                        hash=row[1],
                        username=row[2],
                        phone=row[3],
                        name=row[4]).save()

    def get_entity_rows_by_phone(self, phone):
        with switch_db(Entity, self.database) as _Entity:
            return _Entity.objects(phone=phone)

    def get_entity_rows_by_username(self, username):
        with switch_db(Entity, self.database) as _Entity:
            return _Entity.objects(username=username)

    def get_entity_rows_by_name(self, name):
        with switch_db(Entity, self.database) as _Entity:
            return _Entity.objects(name=name)

    def get_entity_rows_by_id(self, id, exact=True):
        with switch_db(Entity, self.database) as _Entity:
            if exact:
                return _Entity.objects(id=id)
            else:
                ids = (
                    utils.get_peer_id(PeerUser(id)),
                    utils.get_peer_id(PeerChat(id)),
                    utils.get_peer_id(PeerChannel(id))
                )
                return _Entity.objects(id__in=ids)

    def get_file(self, md5_digest, file_size, cls):
        with switch_db(SentFile, self.database) as _SentFile:
            row = _SentFile.objects(md5_digest=md5_digest,
                                   file_size=file_size,
                                   type=_SentFileType.from_type(cls).value).first()

        if row:
            return cls(row.id, row.hash)

    def cache_file(self, md5_digest, file_size, instance):
        with switch_db(SentFile, self.database) as _SentFile:
            if not isinstance(instance, (InputDocument, InputPhoto)):
                raise TypeError('Cannot cache %s instance' % type(instance))

            _SentFile(md5_digest=md5_digest,
                      file_size=file_size,
                      type=_SentFileType.from_type(type(instance)).value,
                      id=instance.id,
                      hash=instance.access_hash).save()
