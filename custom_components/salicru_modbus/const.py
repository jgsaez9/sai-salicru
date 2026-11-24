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

# IQ14700: zero-based PDU addresses, FC03 only. The profile covers RO
# measurements documented for the 1–3 kVA RT3 and its alarm registers.
REGISTERS = (
    43, 59, 63, 64, 68, 33, 29, 41, 62, 1, 5,
    2, 3, 4, 6, 7, 8, 17, 25, 26, 27, 28, 34, 38, 39, 40,
    60, 61, 67, 69, 76, 103, 565, 566, 567, 568, 569, 570, 1006,
)
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
    if address in (17, 25) and value not in range(0, 7):
        return None
    if address == 28 and value not in (1, 2, 3):
        return None
    if address == 60 and value not in (1, 2, 3, 4):
        return None
    if address == 69 and value not in (0, 1):
        return None
    if address == 1006 and value not in (0, 1):
        return None
    return value
