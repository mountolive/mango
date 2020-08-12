from base_model import BaseModel
from tornado.ioloop import IOLoop

class Example(BaseModel):
    collection = 'example'
    fields = [('foo', False), ('bar', True)]

async def crud():
  example = Example()
  print(example.__dict__)
  example.foo = 'Foo'
  await example.save()
  print(example._id, example.foo)
  await example.update(foo='Foo2')
  print(example.foo)
  example2 = await Example.create(**{'foo': 'NewFoo', 'bar': 'NewBar'})
  print(example2._id, example2.foo)
  await example2.delete()
  await Example.update_many(criteria={'foo': 'Foo2'}, **{'bar': 'OldBar'})
  Example.read_all()

if __name__ == '__main__':
    IOLoop.instance().run_sync(crud)

