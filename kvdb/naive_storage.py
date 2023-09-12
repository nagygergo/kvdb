"""Simple set based storage for kvdb."""
from kvdb.exceptions import InvalidKeyException, KeyNotFoundException


class NaiveStorage():
    """Simple set based storage for kvdb."""

    def __init__(self, init_dict=None) -> None:
        if init_dict:
            self.dict = init_dict
        else:
            self.dict = {}

    def get(self, key):
        """Get value from db."""
        self._raise__key_invalid(key)
        self._raise_key_not_found(key)
        return self.dict[key]

    def set(self, key, value):
        """Set value in db."""
        self._raise__key_invalid(key)
        self.dict[key] = value

    def delete(self, key):
        """Delete value from db."""
        self._raise__key_invalid(key)
        self._raise_key_not_found(key)
        del self.dict[key]

    def _raise__key_invalid(self, key):
        if key is None or len(key) < 1:
            raise InvalidKeyException()

    def _raise_key_not_found(self, key):
        if key not in self.dict:
            raise KeyNotFoundException()
