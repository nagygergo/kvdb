import pytest
from kvdb import server
from .utils import LOCALHOST, next_free_port


@pytest.mark.asyncio
async def test_start_server():
    port = next_free_port()
    server_instance = await server.start(LOCALHOST, port)
    assert server_instance.is_serving()
    assert server_instance.sockets[0].getsockname()[0] == LOCALHOST
    assert server_instance.sockets[0].getsockname()[1] == port
    server_instance.close()
    await server_instance.wait_closed()
    assert not server_instance.is_serving()
