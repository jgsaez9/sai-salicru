# Cambios

## 1.1.0

- Añade lecturas de potencia activa/aparente, bypass, temperatura, factor de potencia y datos de diagnóstico.
- Añade resultados de test, modo de carga, configuración nominal y alarmas documentadas en registros 1–8.
- Mantiene exclusivamente peticiones Modbus FC03 de solo lectura.

## 1.0.0

- Primera versión para SLC TWIN RT3 por Modbus TCP, instalable desde HACS.
- Configuración y reconfiguración desde la interfaz, con validación de lecturas.
- 18 entidades activas y 3 sensores de diagnóstico opcionales.
- Traducciones en español e inglés, ajustes de sondeo y diagnósticos.
- Recuperación de comunicación y rechazo de datos no utilizables.
- Pruebas automatizadas del protocolo y de la integración con Home Assistant.
