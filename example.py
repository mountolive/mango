from mangobocado.base_model import BaseModel
from tornado.ioloop import IOLoop


class Example(BaseModel):
    collection = "example"
    fields = [("foo", False), ("bar", True)]


async def crud():
    example = Example()
    print(example.__dict__)
    example.foo = "foo"
    await example.save()
    print(example._id, example.foo)
    await example.update(foo="foo2")
    print(example.foo)
    example2 = await example.create(**{"foo": "newfoo", "bar": "newbar"})
    print(example2._id, example2.foo)
    await example2.delete()
    await example.update_many(criteria={"foo": "foo2"}, **{"bar": "oldbar"})
    example.read_all()


IOLoop.instance().run_sync(crud)
