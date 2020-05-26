import yaml
from utils.mongo_helper import ModelException, check_uniqueness, db_connected


@db_connected
class BaseModel:
    u"""Defines the base methods for all models
    Class Attributes
    ________________
    collection: str
        The name of the collection associated to the model
    fields: str
        List of tuples containing the `field_name` for te document
        as the first element, and a boolean value indicating if the
        field is unique or not.
        This also holds the expected attributes when initilizing an
        instance of the given model"""
    #Collection name holder
    collection = ''

    #Fields tuples of the form ('field_name', unique?)
    fields = []

    _field_names = list(map(lambda x: x[0], fields))

    def __init__(self, **kwargs):
        u"""kwargs parameter should be a dictionary, being the
        keys the associated fields named in the class parameter `fields`"""
        if not (collection and fields):
            raise ModelException(u"""You need define the `fields` parameter
                                 and the name of the collection, as the
                                 parameter `collection`""")
        self._valid_fields()
        for k, v in kwarags.items():
            if not (k in _field_names or k == '_id'):
                raise ModelException(u"""Passed parameter %s is not part
                                     of the model's fields""" % k)
            setattr(self, k, v)

    def save(self):
        u""" Saves a given instance's document.
        If the instance as an existing
        associated `_id` it executes an update_one query for
        the instance's values.
        Else it creates that given instance's document and returns it"""
        cls =  type(self)
        existing = self._get_existing(cls)
        if existing: return cls.update_one({'_id': self._id}, self.__dict__)
        res = cls.create(self.__dict__)
        self._id = res._id
        return res

    def update(self, **params):
        u""" Updates a given instance's document.
        raises ModelException if the associated instance's _id
        doesn't exist
        params: dict or kwargs
            named parameters, dictionary of the k: v to be updated"""
        cls = type(self)
        existing = self._get_existing(cls)
        if not existing: raise ModelException(u"""Document with given
                                              id not found""")
        return cls.update_one({'_id': self._id}, self.__dict__)

    def delete(self):
        u""" Deletes a given instance's document"""
        cls = type(self)
        cls.destroy(self.__dict__)

    @classmethod
    async def create(cls, **params):
        u"""Creates a document given in the current collection.
        Checks if the queries violates uniqueness of any field,
        according to the rules set in the `fields` parameter of
        the model
        params: dict
            Should contain only the k:v pairs for the associated
        ____________
        Returns
        ____________
        Model of the corresponding document just created
        Can throw ModelException if there's an uniqueness violation
        """
        object_id = check_uniqueness(collection, cls._extract_uniq(params))
        params.update({'_id': object_id})
        result = await cls.db[collection].insert_one(params)
        return cls.__init__(result)

    @classmethod
    async def update_one(cls, criteria={}, **params):
        u""" Updates a row that matches the criteria parameter, with
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
        """
        check_uniqueness(collection, cls._extract_uniq(params))
        result = await cls.db[collection]
                          .update_one(criteria, {'$set': params})
        return cls.__init__(result)

    @classmethod
    async def update_many(cls, criteria={}, **params):
        u""" Updates all rows that matches the criteria parameter, with
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
        """
        check_uniqueness(collection, cls._extract_uniq(params))
        result = await cls.db[collection]
                          .update_many(criteria, {'$set': params})
        return list(map(lambda x: cls.__init__(x), result))

    @classmethod
    async def read_all(cls, **criteria):
        u""" Read all rows that matches the criteria parameter
        Parameters
        ___________
        criteria: dict
            contains the filter for retrieving the document.
        ___________
        Returns
        ___________
        List of the corresponding model
        """
        result = await cls.db[collection].find(criteria)
        return list(map(lambda x: cls.__init__(x), result))

    @classmethod
    async def read_one(cls, **criteria):
        u""" Read first rows that matches the criteria parameter
        Parameters
        ___________
        criteria: dict
            contains the filter for retrieving the document.
        ___________
        Returns
        ___________
        Model of the found document
        """
        result = await cls.db[collection].find_one(criteria)
        return cls.__init__(result)

    @classmethod
    async def destroy(cls, **criteria):
        u""" Destroy a given document based on criteria
        passed

        Parameters
        _____________
        cirteria: dict (kwargs)
            contains filter of document to be deleted
        """
        await cls.db[collection].delete_one(criteria)

    @classmethod
    async def destroy_many(cls, **criteria):
        u""" Destroy all documents matching criteria
        passed

        Parameters
        _____________
        cirteria: dict (kwargs)
            contains filter of documents to be deleted
        """
        await cls.db[collection].delete_many(criteria)

    @classmethod
    def _extract_uniq(cls, **params):
        u"""Used to filter unique fields at __init__"""
        return {k[0]: params[k] for k in fields if k[1]}

    def _get_existing(self, cls):
        u""" Retrieves a existing document"""
        return cls.read_one({'_id': self._id})

    def _valid_fields(self):
        u"""Helper function that checks whether the k:v at
        __init__ are valid as for the definition of the model"""
        flt = list(filter(lambda x: isinstance(x, tuple) and len(x) == 2, self.fields))
        if not len(flt) == len(self.fields):
            raise ModelException(u"""`fields` most contain tuples of 2 elements each""")
        for tup in self.fields:
            if not (type(tup[0]) == str and
                    type(tup[2]) ==  bool):
                raise ModelException(u"""Each `field` element in `fields` should contain
                                     first the name of the field in the document
                                     and second a boolean value indicating if
                                     the fields is unique or not""")
