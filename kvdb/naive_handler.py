"""Handler for RPC messages"""
import asyncio
import logging
from kvdb import rpc
from kvdb.exceptions import KvdbException
from kvdb.naive_parser import parse_message

LOG = logging.getLogger(__name__)
REQUEST_TIMEOUT = 2


async def handler(reader, writer, storage):
    """Routes messages to the specific handlers, and handles error scenarios"""
    connection_getting_reused = False
    first_message_parsed = True
    while connection_getting_reused or first_message_parsed:
        first_message_parsed = False
        try:
            end_bytes = rpc.encode_response_message(
                rpc.NEWLINE) if connection_getting_reused else None

            message = await asyncio.wait_for(parse_message(reader, end_bytes),
                                             REQUEST_TIMEOUT)
            LOG.info("%s", message)
            match message[0]:
                case rpc.DELETE:
                    _delete_handler(message, writer, storage)
                case rpc.GET:
                    _get_handler(message, writer, storage)
                case rpc.SET:
                    _set_handler(message, writer, storage)
                case rpc.REUSECONN:
                    LOG.info("Upgrading connection for multiple commands")
                    connection_getting_reused = True
                case rpc.CLOSE:
                    LOG.info("Client side connection close proposed")
        except KvdbException as err:
            LOG.warning(err.rpc_message)
            writer.write(err.rpc_message.encode())
        except asyncio.exceptions.TimeoutError as err:
            LOG.error(err)
            LOG.error("Terminating connection due to timeout")
            writer.write(rpc.TIMEOUT_ERROR.encode())
            break
        except ConnectionResetError as err:
            LOG.error()
            LOG.error(err)
            break
        # pylint: disable-next=broad-exception-caught
        except Exception as err:
            LOG.error(err)
            writer.write(KvdbException().rpc_message.encode())
        finally:
            await writer.drain()
    await writer.drain()
    writer.close()
    await writer.wait_closed()


def _get_handler(message, writer, storage):
    value = storage.get(message[1])
    writer.write(value)
    LOG.info("Sending %s", value[0:64])


def _set_handler(message, writer: asyncio.StreamWriter, storage):
    storage.set(message[1], message[2])
    writer.write(rpc.OK.encode())
    LOG.info("Sending %s", rpc.OK)


def _delete_handler(message, writer, storage):
    storage.delete(message[1])
    writer.write(rpc.OK.encode())
    LOG.info("Sending %s", rpc.OK)
