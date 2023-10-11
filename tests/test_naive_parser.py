"""Unit tests for naive parser."""
import asyncio
import pytest
from kvdb.exceptions import InvalidCommandException, InvalidKeyException
from kvdb.naive_parser import parse_message
from .utils import get_random_bytes


@pytest.mark.asyncio
@pytest.mark.parametrize("command,key,value,end_bytes", [
    (b'GET', get_random_bytes(2), None, None),
    (b'SET', get_random_bytes(8), get_random_bytes(32), None),
    (b'DELETE', get_random_bytes(3), None, None),
    (b'REUSECONN', None, None, None),
    (b'GET', get_random_bytes(4), None, bytes('\r\n', "utf-8")),
    (b'SET', get_random_bytes(10),
     get_random_bytes(32),
     bytes('\r\n', "utf-8")),
    (b'DELETE', get_random_bytes(4), None, bytes('\r\n', "utf-8")),
])
async def test_positive_message(command, key, value, end_bytes):
    """Check positive cases for parsing messages."""
    stream = asyncio.StreamReader()
    message = command + b' '
    if key is not None:
        message = message + key
    if value is not None:
        message = message + b' ' + value
    if end_bytes is not None:
        message = message + end_bytes
    stream.feed_data(message)
    stream.feed_eof()
    command_text = command.decode("utf-8")

    parsed = await parse_message(stream, end_bytes)
    if value is None:
        assert parsed == (command_text, key)
    else:
        assert parsed == (command_text, key, value)


@pytest.mark.asyncio
async def test_empty_message():
    """Test that empty stream with
    EOF triggers a close command."""
    stream = asyncio.StreamReader()
    stream.feed_data(b'')
    stream.feed_eof()
    assert await parse_message(stream) == ("CLOSE", None)


@pytest.mark.asyncio
@pytest.mark.parametrize("message,ex_type", [
    (get_random_bytes(10) + b' ' + get_random_bytes(2),
     InvalidCommandException),
    (b'' + b' ' + get_random_bytes(2) + b' ' +
     get_random_bytes(2), InvalidCommandException),
    (b'SET' + b' ' + b'' + b' ' + get_random_bytes(8), InvalidKeyException),
    (b'GET' + b' ' + b'', InvalidKeyException),
    (b'DELETE' + b' ' + b'', InvalidKeyException),
])
async def test_negative_cases(message, ex_type):
    """Check negative cases for parsing messages."""
    stream = asyncio.StreamReader()
    stream.feed_data(message)
    stream.feed_eof()
    with pytest.raises(ex_type):
        await parse_message(stream)
