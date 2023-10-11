"""Unit tests for handler."""
import asyncio
import pytest
import kvdb.naive_parser
import kvdb.naive_handler
from kvdb.naive_storage import NaiveStorage
from kvdb.rpc import OK, TIMEOUT_ERROR, INVALID_COMMAND
from kvdb.exceptions import InvalidCommandException


class MockReadStream():
    # pylint: disable=too-few-public-methods
    """Mocking asyncio.ReadStream."""


class MockStreamWriter():
    """Mocking asyncio.StreamWriter."""

    def write(self, data):
        """Mocking asyncio.StreamWriter.write"""

    async def drain(self):
        """Mocking asyncio.StreamWriter.drain"""

    def close(self):
        """Mocking asyncio.StreamWriter.close"""

    async def wait_closed(self):
        """Mocking asyncio.StreamWriter.wait_closed"""


@pytest.mark.asyncio
@pytest.mark.parametrize("command,key,value", [('SET', "mykey", "myvalue"),
                                               ("GET", "mykey", "myvalue"),
                                               ('DELETE', "mykey", "myvalue")])
async def test_handler_positive(command, key, value, mocker, monkeypatch):
    """Positive test cases for handle function."""
    # pylint: disable=too-many-locals
    key_bytes = bytes(key, "utf-8")
    value_bytes = bytes(value, "utf-8")

    async def stub_parse_message(message, end_bytes):
        # pylint: disable=unused-argument
        if command == "SET":
            return (command, key_bytes, value_bytes)
        return (command, key_bytes)

    monkeypatch.setattr(kvdb.naive_handler,
                        "parse_message", stub_parse_message)

    read_stream = MockReadStream()
    # No point in mocking the current implementation
    storage = NaiveStorage({key_bytes: value_bytes})
    write_stream = MockStreamWriter()

    get_spy = mocker.spy(storage, "get")
    set_spy = mocker.spy(storage, "set")
    delete_spy = mocker.spy(storage, "delete")

    write_spy = mocker.spy(write_stream, "write")
    drain_spy = mocker.spy(write_stream, "drain")
    close_spy = mocker.spy(write_stream, "wait_closed")

    await kvdb.naive_handler.handler(read_stream, write_stream, storage)

    if command == "GET":
        write_spy.assert_called_with(value_bytes)
    else:
        write_spy.assert_called_with(bytes(OK, "utf-8"))
    assert drain_spy.call_count == 2
    close_spy.assert_called_once()

    if command == "GET":
        get_spy.assert_called_once_with(key_bytes)
    elif command == "SET":
        set_spy.assert_called_once_with(key_bytes, value_bytes)
    elif command == "DELETE":
        delete_spy.assert_called_once_with(key_bytes)


@pytest.mark.asyncio
async def test_message_send_timeout(monkeypatch, mocker):
    """Test on waiting for timeout."""

    async def stub_parse_message(message, end_bytes):
        # pylint: disable=unused-argument
        await asyncio.sleep(3)

    monkeypatch.setattr(kvdb.naive_handler,
                        "parse_message", stub_parse_message)

    read_stream = MockReadStream()
    # No point in mocking the current implementation
    storage = NaiveStorage()
    write_stream = MockStreamWriter()

    write_spy = mocker.spy(write_stream, "write")
    drain_spy = mocker.spy(write_stream, "drain")
    close_spy = mocker.spy(write_stream, "wait_closed")

    monkeypatch.setattr(kvdb.naive_handler, "REQUEST_TIMEOUT", 0.1)

    await kvdb.naive_handler.handler(read_stream, write_stream, storage)

    write_spy.assert_called_with(bytes(TIMEOUT_ERROR, "utf-8"))
    assert drain_spy.call_count == 2
    close_spy.assert_called_once()


@pytest.mark.asyncio
async def test_message_send_invalid_command(monkeypatch, mocker):
    """Test to validate invalid commands are handled correctly."""
    async def stub_parse_message(message, end_bytes):
        raise InvalidCommandException()

    monkeypatch.setattr(kvdb.naive_handler,
                        "parse_message", stub_parse_message)

    read_stream = MockReadStream()
    # No point in mocking the current implementation
    storage = NaiveStorage()
    write_stream = MockStreamWriter()

    write_spy = mocker.spy(write_stream, "write")
    drain_spy = mocker.spy(write_stream, "drain")
    close_spy = mocker.spy(write_stream, "wait_closed")

    monkeypatch.setattr(kvdb.naive_handler, "REQUEST_TIMEOUT", 0.1)

    await kvdb.naive_handler.handler(read_stream, write_stream, storage)

    write_spy.assert_called_with(bytes(INVALID_COMMAND, 'utf-8'))
    assert drain_spy.call_count == 2
    close_spy.assert_called_once()
