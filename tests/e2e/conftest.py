"""Fixtures and utilities for e2e testing."""
import socket
import asyncio
from time import sleep
from multiprocessing import Process
import pytest
from kvdb import server

LOCALHOST = "127.0.0.1"


@pytest.fixture
def host_port():
    """Sets up a server to be tested in an other process,
      and provides host and port to where the server is available."""
    port = _next_free_port()
    host_port_tuple = (LOCALHOST, port)
    server_process = Process(target=_run_server_in_process,
                             args=host_port_tuple)
    server_process.start()
    wait_for_socket(LOCALHOST, port)
    yield host_port_tuple
    server_process.terminate()


def _run_server_in_process(host, port):
    """Server main function to be executed in a subprocess."""
    asyncio.run(_run_server(host, port))


async def _run_server(host, port):
    """Starts the server that will only return if the server is stopped."""
    test_server = await server.start(host, port)
    return await test_server.serve_forever()


def _next_free_port(port=1024, max_port=65535):
    """Finds the next available port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while port <= max_port:
        try:
            sock.bind(('', port))
            sock.close()
            return port
        except OSError:
            port += 1
    raise IOError('no free ports')


def wait_for_socket(host, port, tries=5):
    """Polls the provided socket address,
    waiting for a non connection refused response."""
    connected = False
    tries_left = tries
    while not connected and tries_left > 0:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.connect((host, port))
                connected = True
                return
            except ConnectionRefusedError:
                tries_left = tries_left - 1
        sleep(0.1)
    raise TimeoutError("Couldn't connect to socket in time")


async def send_message(host_port_tuple, message):
    """Utility to send a message to the TCP server."""
    host, port = host_port_tuple
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(message.encode())
    writer.write_eof()
    await writer.drain()

    data = await reader.read(-1)

    writer.close()
    await writer.wait_closed()
    return data.decode("utf-8")
