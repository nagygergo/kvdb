"""End to end test cases for TCP KvDB."""
import asyncio

import pytest

from .conftest import send_message, Client


@pytest.mark.asyncio
async def test_set_value(host_port):
    """Check if set command stores the value correctly."""
    key = "test-key"
    value = "some_value"
    response = await send_message(host_port, f"SET {key} {value}")
    assert response == "100:OK\n"
    response = await send_message(host_port, f"GET {key}")
    assert response == value + "\n"


@pytest.mark.asyncio
async def test_delete_value(host_port):
    """Check if a deleted value is not found after deletion."""
    key = "test-key"
    value = "some_value"
    response = await send_message(host_port, f"SET {key} {value}")
    assert response == "100:OK\n"
    response = await send_message(host_port, f"DELETE {key}")
    assert response == "100:OK\n"
    response = await send_message(host_port, f"GET {key}")
    assert response == "403:Key_Not_Found\n"


@pytest.mark.asyncio
async def test_invalid_command(host_port):
    """Check invalid command."""
    key = "test-key"
    value = "some_value"
    response = await send_message(host_port, f"NOT_A_COMMAND {key} {value}")
    assert response == "401:Invalid Command\n"


@pytest.mark.asyncio
async def test_concurrent_writes(host_port):
    """Check concurrent writes."""
    key = "test-key"
    value1 = "some_value1"
    value2 = "some_value2"

    responses = await asyncio.gather(
        send_message(host_port, f"SET {key} {value1}"),
        send_message(host_port, f"SET {key} {value2}"))
    assert responses[0] == "100:OK\n"
    assert responses[1] == "100:OK\n"

    response = await send_message(host_port, f"GET {key}")
    # This assert should be flaky, but it's not.
    assert response == value2 + "\n"


@pytest.mark.asyncio
async def test_reused_connection(host_port):
    """Test a single persistent connection."""

    await _reused_connection_flow("1", host_port)


@pytest.mark.asyncio
async def test_multiple_reused_connections(host_port):
    """Test multiple persistent connections."""
    await asyncio.gather(_reused_connection_flow("1", host_port),
                         _reused_connection_flow("2", host_port))


async def _reused_connection_flow(seed, host_port):
    key = "key" + seed
    value = "value" + seed
    async with Client(host_port) as client:
        resuseconn_resp = await client.send("REUSECONN ", True)
        assert resuseconn_resp == "100:OK\n"
        set_resp = await client.send("SET " + key + " " + value)
        assert set_resp == "100:OK\n"
        get_resp = await client.send("GET " + key)
        assert get_resp == value + "\n"
        delete_resp = await client.send("DELETE " + key)
        assert delete_resp == "100:OK\n"
