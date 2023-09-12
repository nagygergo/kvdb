"""End to end test cases for TCP KvDB."""
import asyncio

import pytest

from .conftest import send_message


@pytest.mark.asyncio
async def test_set_value(host_port):
    """Check if set command stores the value correctly."""
    key = "test-key"
    value = "some_value"
    response = await send_message(host_port, f"SET {key} {value}")
    assert response == "100:OK"
    response = await send_message(host_port, f"GET {key}")
    assert response == value


@pytest.mark.asyncio
async def test_delete_value(host_port):
    """Check if a deleted value is not found after deletion."""
    key = "test-key"
    value = "some_value"
    response = await send_message(host_port, f"SET {key} {value}")
    assert response == "100:OK"
    response = await send_message(host_port, f"DELETE {key}")
    assert response == "100:OK"
    response = await send_message(host_port, f"GET {key}")
    assert response == "403:Key_Not_Found"


@pytest.mark.asyncio
async def test_invalid_command(host_port):
    """Check invalid command."""
    key = "test-key"
    value = "some_value"
    response = await send_message(host_port, f"NOT_A_COMMAND {key} {value}")
    assert response == "401:Invalid Command"


@pytest.mark.asyncio
async def test_concurrent_writes(host_port):
    """Check concurrent writes."""
    key = "test-key"
    value1 = "some_value1"
    value2 = "some_value2"

    responses = await asyncio.gather(
        send_message(host_port, f"SET {key} {value1}"),
        send_message(host_port, f"SET {key} {value2}"))
    assert responses[0] == "100:OK"
    assert responses[1] == "100:OK"

    response = await send_message(host_port, f"GET {key}")
    # This assert should be flaky, but it's not.
    assert response == value2
