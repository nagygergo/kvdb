"""RPC constants for kvdb."""

from functools import cache

SET = "SET"
GET = "GET"
DELETE = "DELETE"
REUSECONN = "REUSECONN"
CLOSE = "CLOSE"
OK = "100:OK"
UNKNOWN_ERROR = "000:UnknownError"
INVALID_COMMAND = "401:Invalid Command"
INVALID_KEY = "402:Invalid_Key"
KEY_NOT_FOUND = "403:Key_Not_Found"
TIMEOUT_ERROR = "405:TimeoutError"
NEWLINE = '\n'


@cache
def encode_response_message(msg: str):
    """Encodes and caches the response messages.
    Should only be used for RPC messages."""
    return msg.encode()
