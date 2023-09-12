"""Benchmarking script for KVDB."""
import random

import socket
import time
from locust import task, User

# Should not be in this file, but locust doesn't seem
# to handle relative module imports correctly


class KvdbClient():
    """Client for kvdb.
    Should not be in this file, but locust doesn't seem
      to handle relative module imports correctly"""

    def __init__(self, host, port, request_event):
        self.host = host
        self.port = port
        self._request_event = request_event

    def get(self, key):
        """Get value from kvdb."""
        return self._exchange(b'GET ' + bytes(key, 'utf-8'), "get")

    def set(self, key, value):
        """Set value in kvdb."""
        return self._exchange(b'SET ' + bytes(key,  'utf-8') + b' '
                              + bytes(value, 'utf-8'),
                              "set")

    def delete(self, key):
        """Delete value from kvdb."""
        return self._exchange(b'DELETE ' + bytes(key, 'utf-8'), "delete")

    def _exchange(self, message, command_meta):
        request_meta = {
            "request_type": "kvdbrpc",
            "name": command_meta,
            "start_time": time.time(),
            "response_length": 0,
            "response": None,
            "context": {},
            "exception": None,
        }
        response = ""
        start_perf_counter = time.perf_counter()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            sock.settimeout(3)
            sock.sendall(message)
            sock.shutdown(socket.SHUT_WR)
            response = sock.recv(2048).decode()
            sock.close()
            request_meta["response_length"] = len(response)
            request_meta["response"] = response

            if response.startswith("40"):
                raise ValueError(response)
        except (ConnectionError, ValueError, TimeoutError) as exc:
            request_meta["exception"] = exc
        request_meta["response_time"] = (
            time.perf_counter() - start_perf_counter) * 1000
        self._request_event.fire(**request_meta)
        return response


class KvDbUser(User):
    """Locust abstract user for kvdb.
    Should not be in this file, but locust doesn't seem
      to handle relative module imports correctly"""
    abstract = True
    host = None
    port = None

    def __init__(self, environment):
        super().__init__(environment)
        self.client = KvdbClient(self.host, self.port,
                                 request_event=environment.events.request)


class TestUser(KvDbUser):
    """Locust user for running benchmark steps."""
    host = "127.0.0.1"
    port = 1024

    @task()
    def test_task(self):
        """Sets, gets and deletes a randomized key in kvdb."""
        target_key = str(random.randint(0, 1000000))
        self.client.set(target_key, str(random.randbytes(3)))
        self.client.get(target_key)
        self.client.delete(target_key)
