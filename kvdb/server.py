"""TCP RPC server."""
import argparse
import asyncio
import logging
from .naive_handler import handler
from .naive_storage import NaiveStorage

LOG = logging.getLogger()


async def start(host, port):
    """Starts kvdb server"""
    LOG.info('Starting server on %s %s', host, port)
    storage = NaiveStorage()
    server = await asyncio.start_server(lambda reader, writer:
                                        handler(reader, writer, storage),
                                        host, port)

    return server


def _parse_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--host', required=True, dest="host", type=str)
    parser.add_argument('-p', '--port', required=True, dest="port", type=int)
    parser.add_argument("-l", "--log-level", required=False,
                        dest="log_level", type=int)
    parser.add_argument("-f", "--multiplex")
    return parser.parse_args()


async def run_from_cli_args():
    """Starts the server based on cli args and
      returns a coroutine that will only finish if the server is shut down."""
    args = _parse_cli_args()
    logging.basicConfig(level=args.log_level)
    server = await start(args.host, args.port)
    return await server.serve_forever()
