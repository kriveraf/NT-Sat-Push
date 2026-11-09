---
title: "Addendum: Brief acotado de la Fase 0"
status: draft
created: 2026-11-04
updated: 2026-11-04
---

# Addendum: Brief acotado de la Fase 0

Detalle de apoyo para el brief acotado. No contiene llaves ni números de abonados. Las etiquetas de fuente son las del brief.

## A. Contrato de la API de Aircast según la colección Postman [POSTMAN]

`POST http://10.40.35.118:8082/aircast-slave-api-rest-server-war/api/pub/v1/ustk/UstkRequest`, cuerpo JSON. Las listas de cabeceras de la colección están vacías y no hay ejemplos de respuesta. Todo esto es lo que **dice la colección**; la captura debe confirmarlo.

| `type` | Campos comunes | Campos propios |
|---|---|---|
| `TextRequest` | `type`, `msisdn`, `requestId`, `campaignId`, `requestDeliveryReport`, `text1` | `tpda`, `mo` |
| `UssdRequest` | ídem | `ussdString` |
| `UrlRequest` | ídem | `title2`, `url`, `flashSmsText`, `smsText`, `alwaysSendSmsText` |
| `CallRequest` | ídem | `title2`, `tpda` |
| `MenuRequest` | ídem | `title2`, `items[]` con `text`, `value` y, opcionales, `tpda` y `mo` |

- Resultado devuelto a la aplicación de recargas: `POST` con `result`, `requestId`, `campaignId`, `lastActionId` y `msisdn`. La colección solo trae la petición de ejemplo; que Aircast sea quien la envía es una inferencia [INFERENCE].
- Ninguna petición lleva la URL del resultado, así que ese destino estaría configurado en Aircast [INFERENCE].
- `tpda` sería la dirección de destino del SMS MO o el número a llamar, y `mo` el texto de ese SMS cuando el abonado acepta [INFERENCE].

## B. Qué pregunta cierra cada dato de la captura

| Dato observable | Dónde se ve | Pregunta que alimenta |
|---|---|---|
| Campos y respuestas de los cinco tipos | Capa REST | Contrato de la API unificada (ADR-1, R3) |
| Número de `submit_sm` por petición, origen, `protocol_id`, `data_coding`, `esm_class` | SMPP | OQ-8 (orígenes autorizados, capacidad) |
| IP origen y `system_id` de cada conexión | SMPP | OQ-28, OQ-34 |
| TAR de cada tipo de petición | Cabecera OTA | OQ-27, R11 |
| SPI: protección y modo de contador | Cabecera OTA | OQ-4, R11 |
| Contador (CNTR) y su avance por destino | Cabecera OTA, si no va cifrada | OQ-4, OQ-24, OQ-33 |
| Código de estado de las respuestas (por ejemplo contador bajo) | Respuestas de la SIM | OQ-4, condición 1 |
| IP origen de las llamadas a la API | Capa REST | OQ-30 |
| Tasa de envío | SMPP | OQ-8 (TPS) |

## C. Matriz de la prueba de laboratorio (Prueba 2)

Tres destinos (lectura RFM con prueba de recepción, TAR 505348 y TAR 534054), cada uno sin seguridad y con seguridad (checksum criptográfico y contador): seis casos. Los casos sin seguridad responden a la exposición R11; los casos con seguridad confirman el camino que usaría el motor propio. Cada resultado se anota por familia de SIM: esta prueba cubre solo NTE04570.

## D. Herramientas ya preparadas

- Procedimiento formal de captura remota (versión 1.0, para aprobación): [runbook.md](../../aircast-traffic-capture/runbook.md). La estación del analista, Windows o macOS, ejecuta por SSH un script fijo en el servidor ([aircast-capture.sh](../../aircast-traffic-capture/aircast-capture.sh)) que transmite la captura; nada se guarda en el servidor. El análisis se hace en Wireshark, en la estación.
- Decodificador de cabeceras OTA: [decode_ota_header.py](../../aircast-traffic-capture/decode_ota_header.py). No usa llaves. Se contrastó con dos implementaciones abiertas (pycrate y pySim) y se probó solo con paquetes sintéticos, **no con tráfico real de Aircast**; hasta entonces sus resultados son hipótesis.
- El perfil `clientes` del script registra solo quién llama a la API, sin cuerpos ni números, para el inventario de consumidores.

Si el enlace SMPP corre en otro nodo que la API (`10.40.35.118`), hará falta un segundo punto de captura [INFERENCE: el nombre del despliegue, `aircast-slave-api-rest-server-war`, sugiere un nodo "slave"].

## E. El resto del diagnóstico

Actividades de la Fase 0 distintas de las dos pruebas piloto, con la pregunta abierta del brief completo que cada una cierra.

| Actividad | Por qué importa | Preguntas |
|---|---|---|
| Remediar los archivos de salida en texto plano (historial, papelera, copias, dispositivos sincronizados) y establecer quién tuvo acceso | Es la primera acción: exposición de seguridad vigente | OQ-10, OQ-25 |
| Medir la cobertura de llaves por lote: instantánea completa de la base y conteo de SIM por perfil y applet desde Aircast | Condición 4, el mayor riesgo | OQ-1, OQ-2, OQ-29 |
| Definir la ruta del contador: prueba de exportación en ICCID de muestra, o prueba de salto | Sin ruta, el motor solo sirve lotes nuevos | OQ-4, OQ-33 |
| Revisar el contrato con Mobiera: derechos sobre Aircast, contadores y copia de llaves | Vencido en julio de 2022 [DOC]; su estado actual se desconoce | OQ-7 |
| Confirmar la solicitud ampliada al fabricante para el lote nuevo | Condición 2 | OQ-15 |
| Revisar SMSC y firewall: capacidad (TPS), regla para tráfico externo, bloqueo del PID 0x7F externo | R11 | OQ-8, OQ-28 |
| Reunir lo necesario para decidir sobre Sleepy: especificación, llave y condiciones | Condición 3 | OQ-3, OQ-27 |
| Decidir construir, contratar o aliarse; iniciar la compra del HSM; aprobar dueño de negocio y caso de negocio | Decisiones de largo plazo | OQ-9, OQ-11, OQ-12, OQ-16 |

## F. Riesgos de la Fase 0

- **Base inalcanzable (R1).** Si la mayoría de las SIM activas no tiene archivos de salida válidos, Aircast nunca podrá retirarse. Por eso la cobertura es criterio del gate.
- **Contadores y llaves bloqueados en Aircast (R2).** Sin exportación ni salto probado, los primeros envíos propios se rechazan como repetidos.
- **Push sin protección alcanzable por terceros (R11).** Sleepy opera sin seguridad (MSL 0) y S@T podría compartir la exposición [INFERENCE]. Las pruebas pueden confirmarla, así que sus resultados se tratan como confidenciales.
- **Autenticación de la API por confirmar.** La colección no muestra autenticación ni TLS en la API de Aircast [POSTMAN]. Puede haber controles por red que la colección no refleja; la captura lo aclara.
- **Datos de abonados en la captura.** Mitigación: filtros de captura mínimos, solo líneas de prueba, borrado documentado.
- **Bloqueo al final (R13).** Las Fases 5 y 6 dependen de pruebas de laboratorio y de terceros que podrían no cumplir sus entregas. Mitigación: plan alterno decidido en el gate.
