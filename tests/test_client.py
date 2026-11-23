"""Exercise real TCP framing, failures, timeouts and cancellation locally."""

import asyncio
import struct
from contextlib import asynccontextmanager, suppress

import pytest

from custom_components.salicru_modbus.client import ModbusException, SalicruClient, SalicruError
from custom_components.salicru_modbus.const import REGISTERS, usable_register


@asynccontextmanager
async def server_for(responder):
    tasks = set()

    async def handle(reader, writer):
        tasks.add(asyncio.current_task())
        try:
            while True:
                request = await reader.readexactly(12)
                response = responder(request)
                if response is None:
                    await asyncio.sleep(5)
                else:
                    # Fragment the response to verify readexactly handles TCP streams.
                    writer.write(response[:4])
                    await writer.drain()
                    await asyncio.sleep(0)
                    writer.write(response[4:])
                    await writer.drain()
        except (asyncio.IncompleteReadError, ConnectionError):
            pass
        finally:
            writer.close()
            with suppress(ConnectionError):
                await writer.wait_closed()
            tasks.discard(asyncio.current_task())

    server = await asyncio.start_server(handle, "127.0.0.1", 0)
    try:
        yield server.sockets[0].getsockname()[1]
    finally:
        server.close()
        await server.wait_closed()
        pending = list(tasks)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)


def response(request, value=500):
    transaction, _, _, unit, _, _, _ = struct.unpack(">HHHBBHH", request)
    return struct.pack(">HHHBBBH", transaction, 0, 5, unit, 3, 2, value)


async def test_full_sample_single_register_read_only(socket_enabled, sample):
    requests = []

    def responder(request):
        decoded = struct.unpack(">HHHBBHH", request)
        requests.append(decoded)
        return response(request, sample[decoded[5]])

    async with server_for(responder) as port:
        client = SalicruClient("127.0.0.1", port, message_wait=0)
        assert await client.async_read() == sample
    assert [request[5] for request in requests] == list(REGISTERS)
    assert all((r[1], r[2], r[3], r[4], r[6]) == (0, 6, 1, 3, 1) for r in requests)
    assert len({r[0] for r in requests}) == 11


@pytest.mark.parametrize(
    "mutation", ["transaction", "protocol", "unit", "length", "function", "byte_count"]
)
async def test_malformed_response(socket_enabled, mutation):
    def responder(request):
        frame = bytearray(response(request))
        offset = {
            "transaction": 1,
            "protocol": 3,
            "unit": 6,
            "length": 5,
            "function": 7,
            "byte_count": 8,
        }[mutation]
        frame[offset] ^= 1
        return bytes(frame)

    async with server_for(responder) as port:
        with pytest.raises(SalicruError):
            await SalicruClient("127.0.0.1", port, message_wait=0).async_read()


async def test_exception_preserves_address_and_code(socket_enabled):
    def responder(request):
        return request[:4] + b"\x00\x03\x01\x83\x02"

    async with server_for(responder) as port:
        with pytest.raises(ModbusException) as error:
            await SalicruClient("127.0.0.1", port, message_wait=0).async_read()
    assert (error.value.address, error.value.code) == (43, 2)


async def test_timeout(socket_enabled):
    async with server_for(lambda request: None) as port:
        with pytest.raises(SalicruError):
            await SalicruClient("127.0.0.1", port, timeout=0.02, message_wait=0).async_read()


async def test_cancellation_releases_lock(socket_enabled, sample):
    async with server_for(lambda request: None) as port:
        client = SalicruClient("127.0.0.1", port, message_wait=0)
        task = asyncio.create_task(client.async_read())
        await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not client._lock.locked()


@pytest.mark.parametrize(
    ("address", "value", "expected"),
    [
        (43, 65535, None),
        (5, 65535, None),
        (62, 259, None),
        (64, 101, None),
        (64, 100, 100),
        (63, 130, 130),
        (62, 9, 9),
        (33, 0, 0),
    ],
)
def test_invalid_and_valid_register_values(address, value, expected):
    assert usable_register(address, value) == expected
