import logging
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
    meta = {
        'collection': 'telethon_entities',
        'indexes': [
            'username',
            'phone',
            'name'
        ]
    }


class SentFile(Document):
    id = IntField(primary_key=True)
    md5_digest = BinaryField()
    file_size = IntField()
    type = IntField()
    hash = IntField()
    meta = {'collection': 'telethon_sent_files'}

class Session(Document):
    dc_id = IntField()
    server_address = StringField()
    port = IntField()
    auth_key = BinaryField()
    takeout_id = IntField()
    meta = {'collection': 'telethon_sessions'}

class UpdateState(Document):
    id = IntField(primary_key=True)
    pts = IntField()
    qts = IntField()
    date = IntField()
    seq = IntField()
    meta = {'collection': 'telethon_update_states'}

class Version(Document):
    version = IntField()


class MongoSession(MemorySession):
    """MongoSession is a Telethon session which stores all data in a MongoDB database."""

    def __init__(self, **kwargs):
        """Creates a new MongoSession instance. Accepts the same parameters as the MongoClient.

        :param db: The name of the database to use. If the database is running locally and without
                    auth, this is the only parameter you need to pass.
        :param host: The host of the database, or the full URI. If not specified, defaults to localhost.
        :param port: The port of the database. If not specified, defaults to 27017.
        :param username: The username to use to authenticate to the database. If not specified, no
                            authentication will be performed.
        :param password: The password to use to authenticate to the database. If not specified, no
                            authentication will be performed.
        :param authentication_source: The database to authenticate against.
        :param authentication_mechanism: The authentication mechanism to use. Defaults to SCRAM-SHA-1.
        :param mongo_client_class: The MongoClient class to use. Defaults to pymongo.MongoClient.
        :param kwargs: Any other keyword arguments to pass to the MongoClient constructor.
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.save_entities = True

        try:
            connect(**kwargs)
        except Exception as e:
            # Silently ignore if the database connection already exists
            if 'A different connection with alias' in e.args[0]:
                pass
            else:
                raise e

        # Do a version check
        version_count = Version.objects.count()
        if version_count < 1:
            # Add the first version record
            Version(version=CURRENT_VERSION).save()
        else:
            # Check if the version is below the current version
            lt_versions = Version.objects(version__lt=CURRENT_VERSION)
            if len(lt_versions) > 0:
                version = Version.objects().order_by('version').first().version
                self._update_database(old=version)
                # Delete old versions
                for version in lt_versions:
                    version.delete()

        # See if we have any previous sessions
        session_count = Session.objects.count()
        if session_count > 0:
            session = Session.objects.first()
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
        for session in Session.objects:
            session.delete()
        Session(dc_id=self._dc_id,
                    server_address=self._server_address,
                    port=self._port,
                    auth_key=self._auth_key.key if self._auth_key else b'',
                    takeout_id=self._takeout_id).save()

    def get_update_state(self, entity_id):
        row = UpdateState.objects(id=entity_id).first()
        if row:
            date = datetime.datetime.fromtimestamp(
                date, tz=datetime.timezone.utc)
            return types.updates.State(row.pts, row.qts, row.date, row.seq, unread_count=0)

    def set_update_state(self, entity_id, state):
        return UpdateState(id=entity_id,
                            pts=state.pts,
                            qts=state.qts,
                            date=state.date.timestamp(),
                            seq=state.seq).save()

    def save(self):
        pass

    def close(self):
        pass

    def delete(self):
        sess = Session.objects(auth_key=self._auth_key.key).first()
        if sess:
            sess.delete()

    @classmethod
    def list_sessions(self, cls):
        return Session.objects

    def process_entities(self, tlo):
        if not self.save_entities:
            return

        rows = self._entities_to_rows(tlo)
        if not rows:
            return

        for row in rows:
            Entity(id=row[0],
                    hash=row[1],
                    username=row[2],
                    phone=row[3],
                    name=row[4]).save()

    def get_entity_rows_by_phone(self, phone):
        try:
            ent = Entity.objects(phone=phone).first()
            return (ent.id, ent.hash)
        except:
            pass

    def get_entity_rows_by_username(self, username):
        try:
            ent = Entity.objects(username=username).first()
            return (ent.id, ent.hash)
        except:
            pass

    def get_entity_rows_by_name(self, name):
        try:
            ent = Entity.objects(name=name).first()
            return (ent.id, ent.hash)
        except:
            pass

    def get_entity_rows_by_id(self, id, exact=True):
        try:
            if exact:
                ent = Entity.objects(id=id).first()
                return (ent.id, ent.hash)
            else:
                ids = (
                    utils.get_peer_id(PeerUser(id)),
                    utils.get_peer_id(PeerChat(id)),
                    utils.get_peer_id(PeerChannel(id))
                )
                ent = Entity.objects(id__in=ids).first()
                return (ent.id, ent.hash)
        except:
            pass

    def get_file(self, md5_digest, file_size, cls):
        try:
            row = SentFile.objects(md5_digest=md5_digest,
                                    file_size=file_size,
                                    type=_SentFileType.from_type(cls).value).first()

            if row:
                return cls(row.id, row.hash)
        except:
            pass

    def cache_file(self, md5_digest, file_size, instance):
        if not isinstance(instance, (InputDocument, InputPhoto)):
            raise TypeError('Cannot cache %s instance' % type(instance))

        SentFile(md5_digest=md5_digest,
                    file_size=file_size,
                    type=_SentFileType.from_type(type(instance)).value,
                    id=instance.id,
                    hash=instance.access_hash).save()
