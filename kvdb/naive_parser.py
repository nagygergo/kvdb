"""Parser for the KVDB RPC commands."""
import asyncio
from .exceptions import InvalidCommandException, InvalidKeyException


async def parse_message(reader: asyncio.StreamReader):
    """Parses the command from the incoming TCP stream."""
    try:
        command = await reader.readuntil(b' ')
        match command:
            case b"SET ":
                return await _parse_set(reader)
            case b"DELETE ":
                return await _parse_delete(reader)
            case b"GET ":
                return await _parse_get(reader)
            case _:
                raise InvalidCommandException()
    except EOFError as exc:
        raise InvalidCommandException() from exc


async def _parse_set(reader):
    key = await reader.readuntil(b' ')
    key = key[:-1]
    if len(key) == 0:
        raise InvalidKeyException()
    value = await reader.read(-1)
    return ("SET", key, value)


async def _parse_delete(reader):
    key = await reader.read(-1)
    if len(key) == 0:
        raise InvalidKeyException()
    return ("DELETE", key)


async def _parse_get(reader):
    key = await reader.read(-1)
    if len(key) == 0:
        raise InvalidKeyException()
    return ("GET", key)
