import asyncio
from mangobocado.base_model import BaseModel


class Example2(BaseModel):
    collection = "example"
    fields = [("foo", False), ("bar", True)]


# Asyncio


example = Example2()
example.foo = "foo"
asyncio.gather(
    example.save(), example.update(foo="foo2"),
)
