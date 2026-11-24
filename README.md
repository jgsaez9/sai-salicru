<p align="center">
  <img src="custom_components/salicru_modbus/brand/icon.png" alt="Salicru SAI para Home Assistant" width="160" />
</p>

# Salicru SAI para Home Assistant

Integra un **Salicru SLC TWIN RT3 por Modbus TCP** desde la interfaz de Home Assistant, sin editar YAML, sin NUT y sin cuenta Nimbus. Instalación como repositorio personalizado de HACS.

[![Añadir a HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jgsaez9&repository=sai-salicru&category=integration)
[![Añadir integración](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=salicru_modbus)

## Compatibilidad

- Home Assistant **2025.3.2 o posterior**.
- Perfil **SLC TWIN RT3 / IQ14700**, con Modbus TCP habilitado y accesible en la red local.
- El tutorial de referencia utilizó un **SLC-1000-TWIN RT3**, firmware principal `00.01.15485` e IoT `02.02.000`. Otros tamaños, tarjetas y versiones de firmware necesitan comprobar que utilizan el mismo mapa.
- La integración se verifica con pruebas automatizadas y un servidor TCP simulado. **Esta versión no se ha probado físicamente contra tu SAI.** La conexión inicial comprueba las lecturas del perfil; contrasta después las medidas con la pantalla del equipo.
- Un puerto Ethernet por sí solo no garantiza compatibilidad. Los modelos USB, NUT, RTU y otras familias Salicru requieren otro método.

## 1. Preparar el SAI

1. Conecta el SAI a la red y localiza su IP. Una reserva DHCP evita cambios de dirección.
2. Habilita **Modbus TCP** en los ajustes de comunicaciones del SAI. En el portal IoT de la unidad de referencia está en `Settings → Network → Access Control → Modbus TCP`. Guarda el cambio.
3. Comprueba que Home Assistant puede acceder al puerto TCP **502**. El Unit ID inicial es **1**; ajústalo si tu equipo utiliza otro.

Si el ajuste aparece habilitado pero se rechaza la conexión, consulta la sección de diagnóstico. Activar el servicio en el SAI es un paso previo a esta integración.

## 2. Instalar con HACS

Pulsa **Añadir a HACS** arriba, o sigue estos pasos:

1. Abre **HACS → menú ⋮ → Repositorios personalizados**.
2. Pega `https://github.com/jgsaez9/sai-salicru` y selecciona el tipo **Integración**.
3. Busca **Salicru SAI** y descárgala.
4. **Reinicia Home Assistant** para cargar la integración.
5. Abre **Ajustes → Dispositivos y servicios → Añadir integración → Salicru SAI**.
6. Introduce un nombre, la IP del SAI, el puerto y el Unit ID. No incluyas `https://` en la IP.

El asistente valida las lecturas del perfil completo y crea sensores de medidas, modos y alarmas. No se necesita añadir una segunda conexión en la integración Modbus nativa.

**Instalación manual:** copia únicamente la carpeta `custom_components/salicru_modbus` a `/config/custom_components/salicru_modbus`, reinicia Home Assistant y realiza los pasos 5 y 6.

## Entidades

La versión 1.1 amplía el perfil con potencia activa y aparente de salida, tensión y frecuencia de bypass, temperatura interna, factor de potencia, modo de carga, resultado del último test de batería, información nominal y más alarmas. Incluye registros de estado sin decodificar como entidades de diagnóstico opcionales. Solo usa funciones Modbus de lectura; no envía órdenes al SAI.

La autonomía restante y la capacidad de batería no se publican todavía: el mapa presenta solapamiento/formato de varios registros y sus valores necesitan validación adicional en esta unidad.

| Medida | Dirección PDU | Conversión |
| --- | ---: | --- |
| Tensión de entrada | 33 | ÷ 10 V |
| Frecuencia de entrada | 29 | ÷ 10 Hz |
| Tensión de salida | 59 | ÷ 10 V |
| Frecuencia de salida | 43 | ÷ 10 Hz |
| Corriente de salida | 41 | ÷ 10 A |
| Carga del SAI | 63 | % |
| Nivel de batería | 64 | % |
| Tensión de batería | 68 | ÷ 10 V |
| Modo del SAI | 62 | Estado traducido |

| Estado / alarma | Registro | Máscara |
| --- | ---: | ---: |
| Red eléctrica presente | 5 | 16384 |
| Salida alimentada | 5 | 8 |
| Batería presente | 1 | 1 |
| Batería baja | 5 | 1 |
| Sobrecarga | 5 | 32 |
| Temperatura elevada | 5 | 64 |
| Fallo interno | 5 | 16 |
| Sustitución de batería | 5 | 256 |
| Fallo del ventilador | 5 | 4 |

Además se registran **3 sensores de diagnóstico deshabilitados de inicio**: código de modo y registros de estado 1 y 5. Puedes habilitarlos desde la lista de entidades del dispositivo.

Los modos se traducen en la interfaz. Para automatizaciones, sus estados internos son: `power_on`, `standby`, `bypass`, `line`, `battery`, `battery_test`, `reserved`, `converter`, `eco` y `unknown_mode`. El atributo `raw_code` conserva el código numérico. Los IDs de entidad los genera Home Assistant según idioma y nombre; selecciónalos desde el editor visual de automatizaciones o tarjetas.

Las direcciones son **PDU base cero**, sin sumar uno ni prefijo 40001. Cada petición lee una palabra de 16 bits con **FC03**. Los campos de un byte requieren byte alto cero; no se recortan silenciosamente valores incompatibles. La carga puede superar el 100 % en una sobrecarga; el nivel de batería se limita al rango 0–100 %. Los valores `0xFFFF` se consideran no utilizables.

## Ajustes y uso

- **Opciones / Configurar:** intervalo entre ciclos (10–3600 s; inicial 60), espera por respuesta (1–30 s; inicial 3) y pausa entre peticiones (200–2000 ms; inicial 200). Se aplica una recarga de la integración.
- **Menú ⋮ → Reconfigurar:** cambia nombre, IP, puerto o Unit ID conservando los identificadores de entidades y el historial. La nueva conexión se valida antes de guardarse.
- **Varios SAI:** añade una entrada por destino; se rechazan duplicados con el mismo host, puerto y Unit ID. Usa siempre la misma forma de dirección: una IP y un alias DNS del mismo equipo no se detectan como duplicado.
- **Panel:** abre el dispositivo y utiliza **Añadir al panel**, o crea una tarjeta nativa de entidades y selecciona los sensores que quieras mostrar.
- **Actualizaciones:** HACS ofrece las nuevas versiones publicadas en este repositorio. Reinicia Home Assistant después de actualizar.
- **Desinstalar:** elimina la entrada en Dispositivos y servicios, retira la descarga en HACS y reinicia Home Assistant.

Cada ciclo abre una conexión, lee los 39 registros en secuencia y la cierra. Las alarmas reutilizan los registros de estado, sin generar peticiones por cada entidad. Una pérdida de comunicación marca todas las entidades como **no disponibles**; una lectura inválida aislada deja no disponibles solo sus entidades dependientes. La siguiente lectura correcta recupera los estados. No se convierte una falta de datos en una alarma desactivada.

La actualización es por sondeo: la detección depende del intervalo, del tiempo de lectura y de la red. No garantiza detectar microcortes. Se incluyen potencia en W/VA y temperatura con registros documentados y leídos en un RT3 de 2 kVA. La autonomía y la capacidad de batería se omiten porque el mapa presenta ambigüedades que requieren validación adicional.

## Diagnóstico

| Problema | Comprobación |
| --- | --- |
| No aparece en Añadir integración | Reinicia Home Assistant y comprueba la carpeta `custom_components/salicru_modbus`. |
| No se ha podido leer el SAI | IP, puerto, Unit ID, activación de Modbus y acceso desde la red de Home Assistant. |
| Conexión rechazada con Modbus habilitado | En el tutorial fue necesario `Control → Reinicio IoT interno` en el LCD. Consulta el manual de tu variante antes de usarlo: es el módulo de comunicaciones, no el apagado del SAI. |
| El SAI rechaza una lectura | El log conserva el código de excepción y la dirección. Revisa Unit ID, modelo, firmware y mapa IQ14700. |
| Valores no válidos al configurar | Algún registro devuelve relleno o un formato incompatible. No se crea una entrada con datos dudosos. |
| Sensores no disponibles | Espera el siguiente ciclo y comprueba la conexión. No equivale a ausencia de alarmas. |
| Entidades duplicadas | Si vienes del paquete YAML del tutorial, retira ese paquete al migrar. Sus entidades no se migran automáticamente. |

Puedes descargar los diagnósticos desde el menú de la integración: contienen los registros y la fecha del último ciclo correcto, omitiendo IP, nombre personalizado e identidad de la entrada. Para investigar fallos, activa **Registro de depuración** en la integración y reproduce el problema.

Esta integración solo monitoriza; no envía órdenes, pruebas de batería ni apagados. Mantén Modbus en tu red local y verifica la detección y recuperación en tu instalación antes de utilizar sus estados en automatizaciones de protección de equipos.

## Desarrollo y pruebas

En Linux con Python 3.14:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-test.txt
ruff check custom_components tests
ruff format --check custom_components tests
pytest -q
```

Las pruebas usan el entorno real de Home Assistant y un servidor TCP simulado. Cubren configuración, duplicados, opciones, reconfiguración, entidades, máscaras independientes, errores Modbus, cabeceras incorrectas, timeout, cancelación, disponibilidad y recuperación. GitHub Actions ejecuta las pruebas, hassfest y la validación HACS.

## Fuentes y licencia

Implementación independiente basada en el [tutorial de Tecnoyfoto](https://tecnoyfoto.com/salicru-home-assistant-modbus-tcp) y las tablas del fabricante [Salicru IQ14700, anexos II y III](https://d7rh5s3nxmpy4.cloudfront.net/CMP1313/files/IQ14700.pdf). La estructura sigue la [documentación de integraciones de Home Assistant](https://developers.home-assistant.io/docs/creating_integration_file_structure/) y los [requisitos de HACS](https://www.hacs.xyz/docs/publish/integration/).

Proyecto comunitario, sin afiliación con Salicru. Código e icono genérico original bajo licencia MIT. Las marcas y documentos enlazados pertenecen a sus respectivos titulares.
