# sourcery skip: avoid-builtin-shadow
import asyncio
from json import dumps, loads
from typing import List, Optional

import websockets
from pydantic import BaseModel
from mcstatus import JavaServer
from mcdreforged.api.decorator import new_thread
from mcdreforged.api.types import ServerInterface

PLUGIN_METADATA = {
    "id": "mc_server_info",
    "version": "0.1.0",
    "name": (
        "Simply get server info in MCDReforged and "
        "connect NoneBot2 to send data to QQ."
    ),
    "author": "MingxuanGame",
    "dependencies": {"mcdreforged": ">=1.0.0 <2.0"},
}

SERVER_NAME: str = ""
PORT: int = 25565
WS_SERVER: str = "ws://127.0.0.1:8080/mcdr"


class Request(BaseModel):
    type: str
    group: int


class Info(BaseModel):
    type: str
    group: int


class ServerInfo(Info):
    type: str = "server_info"
    name: str
    is_online: bool
    version: str
    now_player: int
    max_player: int
    player_list: List[str]


async def get_server_info(
    server: ServerInterface, host: str, port: int, group: int
) -> ServerInfo:
    is_running = server.is_server_running()
    if is_running:
        status = JavaServer(host, port)
        query = await status.async_query()
        now_player = query.players.online
        max_player = query.players.max
        player_list = query.players.names
        version = query.software.version
        return ServerInfo(
            group=group,
            name=SERVER_NAME,
            is_online=True,
            version=version,
            now_player=now_player,
            max_player=max_player,
            player_list=player_list,
        )
    return ServerInfo(
        group=group,
        name=SERVER_NAME,
        is_online=False,
        version="",
        now_player=0,
        max_player=0,
        player_list=[],
    )


async def run_action(
    server: ServerInterface, request: Request
) -> Optional[Info]:
    if request.type == "get_server_info":
        return await get_server_info(server, "127.0.0.1", PORT, request.group)


class Sleep:
    def __init__(self):
        self.tasks = set()

    async def sleep(self, delay, result=None):
        task = asyncio.create_task(asyncio.sleep(delay, result))
        self.tasks.add(task)
        try:
            return await task
        except asyncio.CancelledError:
            return result
        finally:
            self.tasks.remove(task)

    def cancel_all(self):
        for _task in self.tasks:
            _task.cancel()
        # self.tasks = set()


sleep = Sleep()


class WebSocketClient:
    def __init__(self, address, interval: int):
        self.address = address
        self._event_queues = set()
        self.is_close = []
        self.interval = interval

    async def run(self, server: ServerInterface):
        logger = server.logger
        while True:
            try:
                event_queue = asyncio.Queue()
                self._event_queues.add(event_queue)
                async with websockets.connect(  # type: ignore
                    self.address,
                ) as websocket:
                    logger.info("Success to connect WebSocket server")
                    try:

                        async def receive(is_closed: list):
                            while True:
                                if is_closed:
                                    raise RuntimeError
                                data = loads(await websocket.recv())
                                if "type" in data:
                                    request = Request.parse_obj(data)
                                    resp = await run_action(server, request)
                                    if resp:
                                        await websocket.send(resp.json())

                        async def send(is_closed: list):
                            while True:
                                if is_closed:
                                    raise websocket
                                event = await event_queue.get()
                                await websocket.send(dumps(event))

                        await asyncio.gather(
                            send(self.is_close),
                            receive(self.is_close),
                            return_exceptions=False,
                        )
                    except websockets.ConnectionClosed as e:  # type: ignore
                        logger.warning(
                            f"Disconnect the WebSocket server: {str(e)}, "
                            "will reconnect after 5s"
                        )
                    except RuntimeError:
                        break
            except (
                websockets.WebSocketException,  # type: ignore
                ConnectionRefusedError,
            ) as e:
                logger.warning(
                    f"Cannot connect the WebSocket server：{str(e)}，"
                    "will reconnect after 5s"
                )
            if not self.is_close:
                await sleep.sleep(self.interval / 1000)


def shutdown(server: ServerInterface):
    server.logger.info("Status is shutdowns")
    websocket_client.is_close.append(1)
    sleep.cancel_all()


websocket_client = WebSocketClient(WS_SERVER, 5000)


@new_thread("ws")
def websocket_server(server: ServerInterface):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task = loop.create_task(websocket_client.run(server))
    loop.run_until_complete(asyncio.gather(task))


def on_load(server: ServerInterface, old):
    server.logger.info("Minecraft Status is loading")
    server.register_event_listener("mcdr.mcdr_stop", shutdown)
    websocket_server(server)  # type: ignore
