"""Unit tests for handler."""
import asyncio
import pytest
import kvdb.naive_parser
import kvdb.naive_handler
from kvdb.naive_storage import NaiveStorage
from kvdb.rpc import OK, TIMEOUT_ERROR, INVALID_COMMAND, NEWLINE
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
        write_spy.assert_called_with(value_bytes + bytes(NEWLINE, "utf-8"))
    else:
        write_spy.assert_called_with(bytes(OK + NEWLINE, "utf-8"))
    assert drain_spy.call_count == 2
    close_spy.assert_called_once()

    if command == "GET":
        get_spy.assert_called_once_with(key_bytes)
    elif command == "SET":
        set_spy.assert_called_once_with(key_bytes, value_bytes)
    elif command == "DELETE":
        delete_spy.assert_called_once_with(key_bytes)


@pytest.mark.asyncio
@pytest.mark.parametrize("commands", [
    [("REUSECONN", None, None),
     ("SET", b'mykey', b'myvalue'),
     ("GET", b'mykey', b'myvalue'),
     ("CLOSE", None, None)],
    [("REUSECONN", None, None),
     ("DELETE", b'mykey', b'myvalue'),
     ("CLOSE", None, None)],
    [("REUSECONN", None, None),
     ("REUSECONN", None, None),
     ("DELETE", b'mykey', b'myvalue'),
     ("CLOSE", None, None)],
    [("REUSECONN", None, None),
     ("CLOSE", None, None)],
])
async def test_handler_positive_with_reuseconn(commands,
                                               mocker,
                                               monkeypatch):
    """Positive test cases for handle function."""

    # pylint: disable=too-many-locals

    command_counter = 0

    async def stub_parse_message(message, end_bytes):
        # pylint: disable=unused-argument
        nonlocal command_counter
        (command, key, value) = commands[command_counter]
        command_counter = command_counter + 1
        if command == "SET":
            return (command, key, value)
        if command in ("REUSECONN", "CLOSE"):
            return (command, None)

        return (command, key)

    monkeypatch.setattr(kvdb.naive_handler,
                        "parse_message", stub_parse_message)

    read_stream = MockReadStream()

    storage_contents = {command[1]: command[2] for command in commands}
    # No point in mocking the current implementation
    storage = NaiveStorage(storage_contents)
    write_stream = MockStreamWriter()

    get_spy = mocker.spy(storage, "get")
    set_spy = mocker.spy(storage, "set")
    delete_spy = mocker.spy(storage, "delete")

    write_spy = mocker.spy(write_stream, "write")
    drain_spy = mocker.spy(write_stream, "drain")
    close_spy = mocker.spy(write_stream, "wait_closed")

    await kvdb.naive_handler.handler(read_stream, write_stream, storage)

    write_calls = []
    get_calls = []
    set_calls = []
    delete_calls = []
    for (command, key, value) in commands:
        if command == "GET":
            get_calls.append(mocker.call(key))
            write_calls.append(mocker.call(value + bytes(NEWLINE, "utf-8")))
        if command == "SET":
            set_calls.append(mocker.call(key, value))
            write_calls.append(mocker.call(bytes(OK + NEWLINE, "utf-8")))
        if command == "DELETE":
            delete_calls.append(mocker.call(key))
            write_calls.append(mocker.call(bytes(OK + NEWLINE, "utf-8")))

    write_spy.assert_has_calls(write_calls)
    get_spy.assert_has_calls(get_calls)
    set_spy.assert_has_calls(set_calls)
    delete_spy.assert_has_calls(delete_calls)
    # Drain once for each command + once when closing connection
    assert drain_spy.call_count == len(commands)
    close_spy.assert_called_once()


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
    assert drain_spy.call_count == 1
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

    write_spy.assert_called_with(bytes(INVALID_COMMAND + NEWLINE, 'utf-8'))
    assert drain_spy.call_count == 1
    close_spy.assert_called_once()
