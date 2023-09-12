"""Utils for unit tests."""
import random
import socket

random.seed(32)
LOCALHOST = "127.0.0.1"


def get_random_bytes(number_of_bytes):
    """Get stable random bytes."""
    return random.randbytes(number_of_bytes)


def next_free_port(port=1024, max_port=65535):
    """Finds the next available port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while port <= max_port:
        try:
            sock.bind(("", port))
            sock.close()
            return port
        except OSError:
            port += 1
    raise IOError("no free ports")
