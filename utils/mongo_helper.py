import yaml
import os.path
from bson.objectid import ObjectId
from motor.motor_tornado import MotorClient
from pymongo.errors import ConnectionFailure


def check_uniqueness(collection, **field_vals):
    u"""Checks uniquness of """
    if not collection:
        raise ModelException("Collection's name can't be blank")
    primary_id = ObjectId()
    for field, val in field_vals.items():
        proxy_collection = '_'.join([field, collection, 'proxy'])
        doc = {'_id': primary_id, field: val}
        # It would fail on the proxy table
        db[proxy_collection].insert_one(doc)
    return primary_id


def db_connected(Class):
    """ Class-level decorator for models. It binds the database
    connection to the model"""
    class ClassWrapper:
        def __new__(cls, Class):
            db = _create_database('config.yml')
            try:
                db.admin.command('ismaster')
            except ConnectionFailure:
                raise ModelException("""There's no connection to the db
                                     passed as argument. Please, check
                                     configuration file: db-config.yml"""
            else:
                setattr(Class, 'db', db)
            return Class
    return ClassWrapper(Class)

def _create_database(config_file_path):
    """Creates client instance from config_files
    (usually db-config.yml) parametersi
    config_file_path: str
        path of the related config file.
        The yml config file should contain at least `host`,
        `port` and `db_name` parameters"""
    config = yaml.load(open(config_file_path, 'r'))
    return MotorClient(config['host'], config['port'])[config['db_name']]


class ModelException(Exception):
    u"""Custom exception name"""
    pass
