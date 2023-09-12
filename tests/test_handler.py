import asyncio
import pytest
import kvdb.naive_parser
import kvdb.handler
from kvdb.naive_storage import NaiveStorage
from kvdb.rpc import OK, TIMEOUT_ERROR, INVALID_COMMAND
from kvdb.exceptions import InvalidCommandException


class MockReadStream():
    pass


class MockStreamWriter():
    def write(self, data):
        pass

    async def drain(self):
        pass

    def close(self):
        pass

    async def wait_closed(self):
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize("command,key,value", [('SET', "mykey", "myvalue"),
                                               ("GET", "mykey", "myvalue"),
                                               ('DELETE', "mykey", "myvalue")])
async def test_handler_positive(command, key, value, mocker, monkeypatch):
    key_bytes = bytes(key, "utf-8")
    value_bytes = bytes(value, "utf-8")

    async def stub_parse_message(message):
        if command == "SET":
            return (command, key_bytes, value_bytes)
        return (command, key_bytes)

    monkeypatch.setattr(kvdb.handler, "parse_message", stub_parse_message)

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

    await kvdb.handler.handler(read_stream, write_stream, storage)

    if command == "GET":
        write_spy.assert_called_with(value_bytes)
    else:
        write_spy.assert_called_with(bytes(OK, "utf-8"))
    drain_spy.assert_called_once()
    close_spy.assert_called_once()

    if command == "GET":
        get_spy.assert_called_once_with(key_bytes)
    elif command == "SET":
        set_spy.assert_called_once_with(key_bytes, value_bytes)
    elif command == "DELETE":
        delete_spy.assert_called_once_with(key_bytes)


@pytest.mark.asyncio
async def test_message_send_timeout(monkeypatch, mocker):
    async def stub_parse_message(message):
        await asyncio.sleep(3)

    monkeypatch.setattr(kvdb.handler, "parse_message", stub_parse_message)

    read_stream = MockReadStream()
    # No point in mocking the current implementation
    storage = NaiveStorage()
    write_stream = MockStreamWriter()

    write_spy = mocker.spy(write_stream, "write")
    drain_spy = mocker.spy(write_stream, "drain")
    close_spy = mocker.spy(write_stream, "wait_closed")

    monkeypatch.setattr(kvdb.handler, "REQUEST_TIMEOUT", 0.1)

    await kvdb.handler.handler(read_stream, write_stream, storage)

    write_spy.assert_called_with(bytes(TIMEOUT_ERROR, "utf-8"))
    drain_spy.assert_called_once()
    close_spy.assert_called_once()


@pytest.mark.asyncio
async def test_message_send_invalid_command(monkeypatch, mocker):
    async def stub_parse_message(message):
        raise InvalidCommandException()

    monkeypatch.setattr(kvdb.handler, "parse_message", stub_parse_message)

    read_stream = MockReadStream()
    # No point in mocking the current implementation
    storage = NaiveStorage()
    write_stream = MockStreamWriter()

    write_spy = mocker.spy(write_stream, "write")
    drain_spy = mocker.spy(write_stream, "drain")
    close_spy = mocker.spy(write_stream, "wait_closed")

    monkeypatch.setattr(kvdb.handler, "REQUEST_TIMEOUT", 0.1)

    await kvdb.handler.handler(read_stream, write_stream, storage)

    write_spy.assert_called_with(bytes(INVALID_COMMAND, 'utf-8'))
    drain_spy.assert_called_once()
    close_spy.assert_called_once()
