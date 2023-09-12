"""Unit tests for naive storage."""

import pytest
from kvdb.exceptions import InvalidKeyException, KeyNotFoundException
from kvdb.naive_storage import NaiveStorage
from .utils import get_random_bytes


@pytest.mark.parametrize("key,value,exception", [
    (get_random_bytes(4), get_random_bytes(32), None),
    (None, get_random_bytes(32), InvalidKeyException),
    (b'', get_random_bytes(32), InvalidKeyException)
])
def test_set(key, value, exception):
    """Check positive and negative cases for storage delete."""
    storage = NaiveStorage()
    if exception is not None:
        with pytest.raises(exception):
            storage.set(key, value)
            assert storage.get(key) == value
    else:
        storage.set(key, value)
        assert storage.get(key) == value


@pytest.mark.parametrize("key, init_dict, exception", [
    (b'test_key', {b'test_key': get_random_bytes(4)},  None),
    (b'', {b'test_key': get_random_bytes(4)},  InvalidKeyException),
    (None, {b'test_key': get_random_bytes(4)},  InvalidKeyException),
    (b'other_key', {b'test_key': get_random_bytes(4)}, KeyNotFoundException)
])
def test_delete(key, init_dict, exception):
    """Check positive and negative cases for storage delete."""
    storage = NaiveStorage(init_dict)
    if exception is not None:
        with pytest.raises(exception):
            storage.delete(key)
    else:
        storage.delete(key)


@pytest.mark.parametrize("key, init_dict, exception", [
    (b'test_key', {b'test_key': get_random_bytes(4)},  None),
    (b'', {b'test_key': get_random_bytes(4)},  InvalidKeyException),
    (None, {b'test_key': get_random_bytes(4)},  InvalidKeyException),
    (b'other_key', {b'test_key': get_random_bytes(4)}, KeyNotFoundException)
])
def test_get(key, init_dict, exception):
    """Check positive and negative cases for storage get."""
    storage = NaiveStorage(init_dict)
    if exception is not None:
        with pytest.raises(exception):
            storage.get(key)
    else:
        assert storage.get(key) == init_dict[key]
