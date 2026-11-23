"""Generate translations and an original code-drawn UPS icon (stdlib only)."""

import json
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1] / "custom_components" / "salicru_modbus"
SENSOR_NAMES = {
    "input_voltage": ("Input voltage", "Tensión de entrada"),
    "output_voltage": ("Output voltage", "Tensión de salida"),
    "input_frequency": ("Input frequency", "Frecuencia de entrada"),
    "output_frequency": ("Output frequency", "Frecuencia de salida"),
    "output_current": ("Output current", "Corriente de salida"),
    "load": ("UPS load", "Carga del SAI"),
    "battery_level": ("Battery level", "Nivel de batería"),
    "battery_voltage": ("Battery voltage", "Tensión de batería"),
    "operating_mode": ("Operating mode", "Modo del SAI"),
    "mode_code": ("Mode code", "Código de modo"),
    "status_1": ("Status register 1", "Registro de estado 1"),
    "status_5": ("Status register 5", "Registro de estado 5"),
}
BINARY_NAMES = {
    "mains_present": ("Mains present", "Red eléctrica presente"),
    "output_powered": ("Output powered", "Salida alimentada"),
    "battery_present": ("Battery present", "Batería presente"),
    "low_battery": ("Low battery", "Batería baja"),
    "overload": ("Overload", "Sobrecarga"),
    "over_temperature": ("Over temperature", "Temperatura elevada"),
    "internal_fault": ("Internal fault", "Fallo interno"),
    "replace_battery": ("Replace battery", "Sustitución de batería"),
    "fan_fault": ("Fan fault", "Fallo del ventilador"),
}
MODE_NAMES = {
    "power_on": ("Power on", "Encendido inicial"),
    "standby": ("Standby", "Espera"),
    "bypass": ("Bypass", "Bypass"),
    "line": ("On line", "En línea"),
    "battery": ("On battery", "Batería"),
    "battery_test": ("Battery test", "Prueba de batería"),
    "reserved": ("Reserved", "Reservado"),
    "converter": ("Converter", "Convertidor"),
    "eco": ("ECO", "ECO"),
    "unknown_mode": ("Unknown code", "Código desconocido"),
}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


for index, language in enumerate(("en", "es")):
    spanish = language == "es"
    fields = {
        "name": "Nombre" if spanish else "Name",
        "host": "Dirección IP o nombre de host" if spanish else "IP address or hostname",
        "port": "Puerto" if spanish else "Port",
        "unit_id": "Unit ID (dirección Modbus)" if spanish else "Unit ID (Modbus address)",
    }
    description = (
        "Conecta tu SLC TWIN RT3 por la red local. Activa Modbus TCP en el SAI antes de continuar. Introduce solo la IP o el nombre de host, sin https://. Se comprobarán los 11 registros del perfil IQ14700; puede tardar unos segundos. No se necesita cuenta Nimbus ni editar YAML."
        if spanish else
        "Connect your SLC TWIN RT3 over the local network. Enable Modbus TCP on the UPS first. Enter only the IP address or hostname, without https://. All 11 registers in the IQ14700 profile will be checked; this may take a few seconds. No Nimbus account or YAML is required."
    )
    user = {"title": "Salicru SAI", "description": description, "data": fields}
    reconfigure = {
        "title": "Cambiar conexión" if spanish else "Change connection",
        "description": "Actualiza la conexión conservando las entidades y su historial." if spanish else "Update the connection while keeping entities and their history.",
        "data": fields,
    }
    translations = {
        "title": "Salicru SAI",
        "config": {
            "step": {"user": user, "reconfigure": reconfigure},
            "error": {
                "cannot_connect": "No se ha podido leer el SAI. Comprueba IP, puerto, Unit ID y que Modbus TCP esté habilitado y accesible desde Home Assistant." if spanish else "Unable to read the UPS. Check the host, port, Unit ID and that Modbus TCP is enabled and reachable from Home Assistant.",
                "modbus_error": "El SAI ha rechazado una lectura Modbus. Comprueba el Unit ID y la compatibilidad con el mapa IQ14700 de SLC TWIN RT3." if spanish else "The UPS rejected a Modbus read. Check the Unit ID and compatibility with the SLC TWIN RT3 IQ14700 map.",
                "invalid_data": "Uno o más registros contienen valores no válidos para este perfil. Comprueba modelo, firmware y mapa Modbus." if spanish else "One or more registers contain invalid values for this profile. Check the model, firmware and Modbus map.",
                "invalid_host": "Introduce una IP o nombre de host, sin protocolo ni puerto." if spanish else "Enter an IP address or hostname, without a URL scheme or port.",
            },
            "abort": {
                "already_configured": "Este destino Modbus ya está configurado." if spanish else "This Modbus endpoint is already configured.",
                "reconfigure_successful": "Conexión actualizada." if spanish else "Connection updated.",
            },
        },
        "options": {"step": {"init": {
            "title": "Actualización de datos" if spanish else "Polling settings",
            "description": "Valores iniciales: 60 s entre ciclos, 3 s de espera por respuesta y 200 ms entre peticiones. Los cambios recargan la integración." if spanish else "Defaults: 60 s between cycles, 3 s response timeout and 200 ms between requests. Changes reload the integration.",
            "data": {
                "scan_interval": "Intervalo de actualización (segundos)" if spanish else "Polling interval (seconds)",
                "timeout": "Tiempo de espera (segundos)" if spanish else "Response timeout (seconds)",
                "message_wait": "Pausa entre peticiones (milisegundos)" if spanish else "Delay between requests (milliseconds)",
            },
        }}},
        "entity": {
            "sensor": {key: {"name": names[index]} for key, names in SENSOR_NAMES.items()},
            "binary_sensor": {key: {"name": names[index]} for key, names in BINARY_NAMES.items()},
        },
    }
    translations["entity"]["sensor"]["operating_mode"]["state"] = {key: names[index] for key, names in MODE_NAMES.items()}
    write_json(ROOT / "translations" / f"{language}.json", translations)
    if language == "en":
        write_json(ROOT / "strings.json", translations)

write_json(ROOT / "icons.json", {"entity": {
    "sensor": {"load": {"default": "mdi:gauge"}, "operating_mode": {"default": "mdi:power-plug"},
               **{key: {"default": "mdi:code-braces"} for key in ("mode_code", "status_1", "status_5")}},
    "binary_sensor": {"battery_present": {"default": "mdi:battery-check"}},
}})

# Original generic UPS glyph. No manufacturer logo or external image assets.
def chunk(kind, payload):
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))


def make_icon(size):
    pixels = bytearray()
    for y in range(size):
        pixels.append(0)
        for x in range(size):
            px, py = x * 256 / size, y * 256 / size
            color = (0, 0, 0, 0)
            if 48 <= px < 208 and 24 <= py < 232:
                color = (22, 42, 62, 255)
            if 64 <= px < 192 and 40 <= py < 112:
                color = (33, 196, 145, 255)
            if 80 <= px < 165 and 60 <= py < 92:
                color = (240, 255, 249, 255)
            if 165 <= px < 177 and 68 <= py < 84:
                color = (240, 255, 249, 255)
            if 72 <= px < 184 and (136 <= py < 144 or 156 <= py < 164):
                color = (123, 153, 174, 255)
            if (px - 128) ** 2 + (py - 196) ** 2 < 11 ** 2:
                color = (33, 196, 145, 255)
            pixels.extend(color)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b"")


(ROOT / "brand").mkdir(exist_ok=True)
for filename, size in (("icon.png", 256), ("icon@2x.png", 512)):
    (ROOT / "brand" / filename).write_bytes(make_icon(size))
print("Generated English/Spanish translations, icons and brand assets.")
