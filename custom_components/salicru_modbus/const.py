"""Constants for the Salicru TWIN RT3 profile."""

DOMAIN = "salicru_modbus"
NAME = "Salicru SAI"
CONF_UNIT_ID = "unit_id"
CONF_MESSAGE_WAIT = "message_wait"
DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_TIMEOUT = 3
DEFAULT_MESSAGE_WAIT = 200

# IQ14700: zero-based PDU addresses, one uint16 each, FC03 only.
# Read frequency first, as in the reference installation.
REGISTERS = (43, 59, 63, 64, 68, 33, 29, 41, 62, 1, 5)
BYTE_REGISTERS = frozenset((62, 63, 64))
MODES = {
    0: "power_on",
    1: "standby",
    2: "bypass",
    3: "line",
    4: "battery",
    5: "battery_test",
    6: "reserved",
    7: "converter",
    8: "eco",
}


def usable_register(address: int, value: int) -> int | None:
    """Reject filler and incompatible byte layouts without inventing values."""
    if value == 0xFFFF or (address in BYTE_REGISTERS and value > 255):
        return None
    if address == 64 and value > 100:
        return None
    return value
