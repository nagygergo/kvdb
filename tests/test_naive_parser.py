"""Unit tests for naive parser."""
import asyncio
import pytest
from kvdb.exceptions import InvalidCommandException, InvalidKeyException
from kvdb.naive_parser import parse_message
from .utils import get_random_bytes


@pytest.mark.asyncio
@pytest.mark.parametrize("command,key,value", [
    (b'GET', get_random_bytes(2), None),
    (b'SET', get_random_bytes(8), get_random_bytes(32)),
    (b'DELETE', get_random_bytes(3), None)
    # (b'SET', bytes("key with spaces", 'utf-8'), get_random_bytes(32)),
    #  #Keys with spaces in it are not supported.
])
async def test_positive_message(command, key, value):
    """Check positive cases for parsing messages."""
    stream = asyncio.StreamReader()
    message = command + b' ' + key
    if value is not None:
        message = message + b' ' + value
    stream.feed_data(message)
    stream.feed_eof()
    command_text = command.decode("utf-8")

    parsed = await parse_message(stream)
    if value is None:
        assert parsed == (command_text, key)
    else:
        assert parsed == (command_text, key, value)


@pytest.mark.asyncio
@pytest.mark.parametrize("message,ex_type", [
    (get_random_bytes(10) + b' ' + get_random_bytes(2),
     InvalidCommandException),
    (b'' + b' ' + get_random_bytes(2) + b' ' +
     get_random_bytes(2), InvalidCommandException),
    (b'SET' + b' ' + b'' + b' ' + get_random_bytes(8), InvalidKeyException),
    (b'GET' + b' ' + b'', InvalidKeyException),
    (b'DELETE' + b' ' + b'', InvalidKeyException),
    (b'', InvalidCommandException)
])
async def test_negative_cases(message, ex_type):
    """Check negative cases for parsing messages."""
    stream = asyncio.StreamReader()
    stream.feed_data(message)
    stream.feed_eof()
    with pytest.raises(ex_type):
        await parse_message(stream)
