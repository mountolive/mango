import os.path

from motor.motor_tornado import MotorClient
from pymongo.errors import ConnectionFailure
import yaml

def db_connected(Class):
    ''' Class-level decorator for models. It binds the database
    connection to the model'''
    class ClassWrapper:
        def __new__(cls, Class):
            db = _create_database('config.yml', Class.__name__.lower())
            try:
                db.command('ismaster')
            except ConnectionFailure:
                raise ModelException('''There's no connection to the db
                                     passed as argument. Please, check
                                     configuration file: config.yml''')
            else:
                setattr(Class, 'db', db)
            return Class
    return ClassWrapper(Class)

def _create_database(config_file_path: str, db_name: str):
    '''Creates client instance from config_files
    (usually db-config.yml) parametersi
    config_file_path: str
        path of the related config file.
        The yml config file should contain at least `host`,
        `port` and `db_name` parameters'''
    config = yaml.load(open(config_file_path, 'r'), Loader=yaml.BaseLoader)
    if not config['host']:
        raise ModelException('''host must be present in config.yaml''')
    if not config['port']:
        raise ModelException('''port must be present in config.yaml''')
    if not config['port'].isnumeric():
        raise ModelException('''Port must be a numeric value''')
    return MotorClient(config['host'],
                       int(config['port']))[db_name]


class ModelException(Exception):
    '''Custom exception name'''
    pass
