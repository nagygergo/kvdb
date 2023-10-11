"""Parser for the KVDB RPC commands."""
import asyncio
import logging
from .exceptions import InvalidCommandException, InvalidKeyException
LOG = logging.getLogger(__name__)


async def parse_message(reader: asyncio.StreamReader, end_bytes=None):
    """Parses a command from the incoming TCP stream.
        :param bytes end_bytes Closing byte of the message.
            By default it reads until EOF."""
    try:
        if reader.at_eof():
            return await _parse_close()
        command = await reader.readuntil(b' ')
        match command:
            case b"REUSECONN ":
                return await _parse_reuseconn()
            case b"SET ":
                return await _parse_set(reader, end_bytes)
            case b"DELETE ":
                return await _parse_delete(reader, end_bytes)
            case b"GET ":
                return await _parse_get(reader, end_bytes)
            case _:
                LOG.error("Command %s is invalid", command)
                raise InvalidCommandException()
    except EOFError as exc:
        raise InvalidCommandException() from exc


async def _parse_set(reader, end_bytes):
    key = await reader.readuntil(b' ')
    key = key[:-1]
    if len(key) == 0:
        raise InvalidKeyException()
    value = await _read_until_end_bytes(reader, end_bytes)
    return ("SET", key, value)


async def _parse_delete(reader, end_bytes):
    key = await _read_until_end_bytes(reader, end_bytes)
    if len(key) == 0:
        raise InvalidKeyException()
    return ("DELETE", key)


async def _parse_get(reader, end_bytes):
    key = await _read_until_end_bytes(reader, end_bytes)
    if len(key) == 0:
        raise InvalidKeyException()
    return ("GET", key)


async def _parse_reuseconn():
    return ("REUSECONN", None)


async def _parse_close():
    return ("CLOSE", None)


async def _read_until_end_bytes(reader:  asyncio.StreamReader, end_bytes=None):
    if end_bytes is not None:
        read_bytes = await reader.readuntil(end_bytes)
        return read_bytes[:-len(end_bytes)]
    return await reader.read(-1)
