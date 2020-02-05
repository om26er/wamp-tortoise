from autobahn.asyncio.component import Component, run
from autobahn.wamp.protocol import ApplicationSession
from tortoise import Tortoise

from serializers import ProfileSerializer

component = Component(transports="ws://localhost:8080/ws", realm="realm1")


async def init_db():
    await Tortoise.init(db_url='sqlite://db.sqlite3', modules={'users': ['models']})
    await Tortoise.generate_schemas()


@component.register("io.crossbar.register")
async def register_user(name: str, age: str, height: str):
    serializer = ProfileSerializer()
    return await serializer.create(name=name, age=age, height=height)


@component.on_join
async def joined(session: ApplicationSession, _details):
    await init_db()
    session.log.info("ready to rock")


if __name__ == '__main__':
    run(component)
