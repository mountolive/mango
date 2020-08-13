# Mangobocado: Small model wrapper for motor

Mangobocado is a small wrapper for the [motor](https://github.com/mongodb/motor) to be used on top of [tornado](https://github.com/tornadoweb/tornado).

The idea is trying to imitate the Ruby On Rails' ActiveRecord api for handling common operations

## Requirements

Expects a `config.yml` in the root with the `host` and `port` for mongodb

`Python 3.7.*`

To install requirements manually: `pip install -r requirements.txt`

## Installation

`python3 setup.py install`

## Example

```
from mangobocado.base_model import BaseModel
from tornado.ioloop import IOLoop

class Example(BaseModel):
    collection = 'example'
    # 'bar' will be mandatory, while 'foo' won't
    fields = [('foo', False), ('bar', True)]

async def crud():
  # Creating a new record from instance
  example = Example()
  # __dict__ = { '_id': None, 'foo': None, 'bar': None }
  example.foo = 'Foo'
  await example.save()
  # example._id ---> 5f3466b02d4dddce632f0197  

  # Updating a record from instance
  await example.update(foo='Foo2')

  # Creating a new record from class
  example2 = await Example.create(**{'foo': 'NewFoo', 'bar': 'NewBar'})
  # example2._id ---> 5f3466b02d4dddce632f0199

  # Deleting a record
  await example2.delete()

  # Bulk Update
  await Example.update_many(criteria={'foo': 'Foo2'}, **{'bar': 'OldBar'})

  # Read
  # this returns an async_generator
  Example.read_all()

  # Obtaining the raw collection, to work directly with the motor client
  collection = Example.get_raw_collection()

if __name__ == '__main__':
    IOLoop.instance().run_sync(crud)
```
