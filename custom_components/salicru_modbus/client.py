"""Small asynchronous, read-only Modbus TCP client for the RT3 profile.

No third-party Modbus dependency and no write/control functions. A new TCP
connection is used for each polling cycle; all requests within it are serial.
"""

import asyncio
import struct
from contextlib import suppress

from .const import REGISTERS, usable_register


class SalicruError(Exception):
    """A connection or Modbus protocol error."""


class ModbusException(SalicruError):
    """The device returned a Modbus exception."""

    def __init__(self, address: int, code: int) -> None:
        self.address = address
        self.code = code
        super().__init__(f"Modbus exception {code} at register {address}")


class SalicruClient:
    """Read the documented single-register FC03 profile."""

    def __init__(
        self,
        host: str,
        port: int = 502,
        unit_id: int = 1,
        timeout: float = 3,
        message_wait: int = 200,
    ) -> None:
        if not host or not 1 <= port <= 65535 or not 1 <= unit_id <= 255:
            raise ValueError("Invalid endpoint")
        if timeout <= 0 or message_wait < 0:
            raise ValueError("Invalid timing")
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.message_wait = message_wait / 1000
        self._transaction = 0
        self._lock = asyncio.Lock()

    async def async_read(self) -> dict[int, int | None]:
        """Read a complete sample, or fail without publishing partial data."""
        async with self._lock:
            writer = None
            try:
                async with asyncio.timeout(self.timeout):
                    reader, writer = await asyncio.open_connection(self.host, self.port)
                values = {}
                for index, address in enumerate(REGISTERS):
                    if index:
                        await asyncio.sleep(self.message_wait)
                    async with asyncio.timeout(self.timeout):
                        value = await self._read_register(reader, writer, address)
                    values[address] = usable_register(address, value)
                return values
            except (OSError, TimeoutError, asyncio.IncompleteReadError) as err:
                raise SalicruError("Connection failed or response timed out/incomplete") from err
            finally:
                if writer is not None:
                    writer.close()
                    with suppress(OSError, TimeoutError):
                        async with asyncio.timeout(1):
                            await writer.wait_closed()

    async def _read_register(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        address: int,
    ) -> int:
        self._transaction = (self._transaction + 1) & 0xFFFF
        transaction = self._transaction
        writer.write(struct.pack(">HHHBBHH", transaction, 0, 6, self.unit_id, 3, address, 1))
        await writer.drain()
        header = await reader.readexactly(7)
        response_id, protocol, length, unit = struct.unpack(">HHHB", header)
        if (response_id, protocol, unit) != (transaction, 0, self.unit_id):
            raise SalicruError("Mismatched Modbus response header")
        # One-register reply is five bytes including Unit ID; exception is three.
        if length not in (3, 5):
            raise SalicruError("Invalid Modbus response length")
        pdu = await reader.readexactly(length - 1)
        if len(pdu) == 2 and pdu[0] == 0x83:
            raise ModbusException(address, pdu[1])
        if len(pdu) != 4 or pdu[:2] != b"\x03\x02":
            raise SalicruError("Invalid FC03 response")
        return struct.unpack(">H", pdu[2:])[0]
