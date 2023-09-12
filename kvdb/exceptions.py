"""Kvdb specific exceptions."""

from kvdb import rpc


class KvdbException(Exception):
    """Generic KVDB exception. The rpc_message message field
      contains the message that should be sent back to the client
      in case this message needs to be handled."""
    rpc_message = rpc.UNKNOWN_ERROR


class InvalidCommandException(KvdbException):
    """Should be raised in cases the rpc command is not valid."""
    rpc_message = rpc.INVALID_COMMAND


class InvalidKeyException(KvdbException):
    """Should be raised in case the KVDB key has formatting issues."""
    rpc_message = rpc.INVALID_KEY


class KeyNotFoundException(KvdbException):
    """Should be raised in case the referred key is not found."""
    rpc_message = rpc.KEY_NOT_FOUND
