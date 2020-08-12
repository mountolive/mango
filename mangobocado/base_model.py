from bson.objectid import ObjectId
import sys
from tornado import gen
from typing import List, Tuple, Dict
import yaml

sys.path.insert(1, '../util/mongo_helper.py')

from mangobocado.mongo_helper import ModelException, db_connected

Fields = List[Tuple[str, bool]]


@db_connected
class BaseModel:
    '''Defines the base methods for all models
    Class Attributes
    ________________
    collection: str
        The name of the collection associated to the model
    fields: str
        List of tuples containing the `field_name` for te document
        as the first element, and a boolean value indicating if the
        field is unique or not.
        This also holds the expected attributes when initilizing an
        instance of the given model'''
    #Collection name holder
    collection: str = ''

    #Fields tuples of the form ('field_name', unique?)
    fields: Fields = []

    def __init__(self, **kwargs):
        '''kwargs parameter should be a dictionary, being the
        keys the associated fields named in the class parameter
        `fields`'''
        if not self.collection or not self.fields:
            raise ModelException('''You need define the `fields` parameter
                                 and the name of the collection, as the
                                 parameter `collection`''')
        self._valid_fields()
        field_names = list(map(lambda x: x[0], self.fields))
        for k, v in kwargs.items():
            if not (k in field_names or k == '_id'):
                raise ModelException('Passed parameter %s is not part \
                                     of the model\'s fields' % k)
            setattr(self, k, v)
        self._id = kwargs['_id'] if '_id' in kwargs else None

    async def save(self):
        ''' Saves a given instance's document.
        If the instance as an existing
        associated `_id` it executes an update_one query for
        the instance's values.
        Else it creates that given instance's document and returns it'''
        cls = type(self)
        existing = await self._get_existing(cls)
        if existing: return await cls.update_one(
                                        criteria={'_id': self._id},
                                        **self.__dict__
                                     )
        res = await cls.create(**self.__dict__)
        self._id = res._id
        return True

    async def update(self, **params):
        ''' Updates a given instance's document.
        raises ModelException if the associated instance's _id
        doesn't exist
        params: dict or kwargs
            named parameters, dictionary of the k: v to be updated'''
        cls = type(self)
        existing = await self._get_existing(cls)
        if not existing: raise ModelException('Document with given \
                                              id not found')
        return await cls.update_one(criteria={'_id': self._id},
                                    **self.__dict__)

    async def delete(self):
        ''' Deletes a given instance's document'''
        cls = type(self)
        await cls.destroy(**self.__dict__)

    @classmethod
    async def create(cls, **params):
        '''Creates a document given in the current collection.
        Checks if the queries violates uniqueness of any field,
        according to the rules set in the `fields` parameter of
        the model
        params: dict
            Should contain only the k:v pairs for the associated
        ____________
        Returns
        ____________
        Instance of the corresponding document just created
        Can throw ModelException if there's an uniqueness violation
        '''
        object_id = cls._check_uniqueness(**cls._extract_uniq(**params))
        params.update({'_id': object_id})
        result = await cls.db[cls.collection].insert_one(params)
        return cls(**params)

    @classmethod
    async def update_one(cls, criteria={}, **params):
        ''' Updates a row that matches the criteria parameter, with
        the corresponding params
        Parameters
        ___________
        criteria: dict
            contains the filter for retrieving the document.
            the first one would be updated according the `params`
            parameter
        params: dict (kwargs)
            contains the map of the data to be updated
        ___________
        Returns
        ___________
        Updated model
        Can throw ModelException if there's an uniqueness violation
        '''
        cls._check_uniqueness(**cls._extract_uniq(**params))
        result = await cls.db[cls.collection] \
                          .update_one(criteria, {'$set': params})
        return True

    @classmethod
    async def update_many(cls, criteria={}, **params):
        ''' Updates all rows that matches the criteria parameter, with
        the corresponding params
        Parameters
        ___________
        criteria: dict
            contains the filter for retrieving the document.
            the first one would be updated according the `params`
            parameter
        params: dict (kwargs)
            contains the map of the data to be updated
        Returns
        ___________
        List of the corresponding model
        Can throw ModelException if there's an uniqueness violation
        '''
        cls._check_uniqueness(**cls._extract_uniq(**params))
        result = await cls.db[cls.collection] \
                          .update_many(criteria, {'$set': params})
        return True

    @classmethod
    def read_all(cls, length=10, **criteria):
        ''' Read all rows that matches the criteria parameter
        Parameters
        ___________
        criteria: dict
            contains the filter for retrieving the document.
        length: int
            page size for fetching
        ___________
        Returns
        ___________
        List of the corresponding model
        '''
        cursor = cls.db[cls.collection].find(criteria)
        docs = yield cursor.to_list(length=length)
        while docs:
            docs = yield cursor.to_list(lenght=length)

    @classmethod
    def get_raw_collection(cls):
        ''' Returns the raw collection associated with this model
        to be used for more custome tasks'''
        return cls.db[cls.collection]

    @classmethod
    async def read_one(cls, **criteria):
        ''' Read first rows that matches the criteria parameter
        Parameters
        ___________
        criteria: dict
            contains the filter for retrieving the document.
        ___________
        Returns
        ___________
        Model of the found document
        '''
        result = await cls.db[cls.collection].find_one(criteria)
        if result: return cls(**result)
        return None

    @classmethod
    async def destroy(cls, **criteria):
        ''' Destroy a given document based on criteria
        passed

        Parameters
        _____________
        cirteria: dict (kwargs)
            contains filter of document to be deleted
        '''
        await cls.db[cls.collection].delete_one(criteria)

    @classmethod
    async def destroy_many(cls, **criteria):
        ''' Destroy all documents matching criteria
        passed

        Parameters
        _____________
        cirteria: dict (kwargs)
            contains filter of documents to be deleted
        '''
        await cls.db[cls.collection].delete_many(criteria)

    @classmethod
    def _extract_uniq(cls, **params):
        '''Used to filter unique fields at __init__'''
        return {k[0]: params[k[0]] for k in cls.fields if k[1]}

    async def _get_existing(self, cls):
        ''' Retrieves a existing document'''
        return await cls.read_one(**{'_id': self._id})

    def _valid_fields(self):
        '''Helper function that checks whether the k:v at
        __init__ are valid as for the definition of the model'''
        flt = list(filter(lambda x: isinstance(x, tuple) \
                          and len(x) == 2, self.fields))
        if not len(flt) == len(self.fields):
            raise ModelException('`fields` most contain tuples \
                                 of 2 elements each')
        for tup in self.fields:
            if not (type(tup[0]) == str and type(tup[1]) ==  bool):
                raise ModelException('''Each `field` element in
                                     `fields` should contain
                                     first the name of the field in the document
                                     and second a boolean value indicating if
                                     the fields is unique or not''')
            self.__dict__[tup[0]] = None

    @classmethod
    def _check_uniqueness(cls, **field_vals):
        '''Checks uniquness of fields'''
        if not cls.collection:
            raise ModelException('Collection\'s name can\'t be blank')
        primary_id = ObjectId()
        for field, val in field_vals.items():
            proxy_collection = '_'.join([field, cls.collection, 'proxy'])
            doc = {'_id': primary_id, field: val}
            # It would fail on the proxy table
            cls.db[proxy_collection].insert_one(doc)
        return primary_id



