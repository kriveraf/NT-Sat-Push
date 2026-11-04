---
title: "Runbook: captura y análisis del tráfico de Aircast con Wireshark"
status: draft
created: 2026-11-04
basis: "Brief Nuevatel SAT Platform, rama origin/brief/sat-platform-update-2026-10-30 (updated 2026-10-30)"
---

# Runbook: qué envía Aircast "por debajo"

Objetivo: observar en la red qué viaja realmente cuando un consumidor llama a la API de Aircast, para (a) fijar el contrato real del *unified send API* compatible con UstkRequest (ADR-1, R3) y (b) responder preguntas abiertas del Brief (OQ-4, OQ-8, OQ-27, OQ-28, OQ-33, OQ-34).

El Brief ya prevé esta prueba: Fase 0, *"a scoped sniffer on Aircast's SMPP bind, limited to test lines, with authorization and later deletion"*, y la Decisión 8 pide autorizarla. Un sniffer **no entrega la llave de Sleepy** (Brief, addendum K).

> Fuentes: lo que sigue sale del Brief ([DOC] IS-SU-TS 23915 §2.1.3, [LLAVE]) y, para la API REST, de la colección Postman `PUSH-ussd-sat` ([POSTMAN], recibida 2026-11-04). Esa colección vive en Descargas y **no debe copiarse al repositorio**: trae números reales y una credencial de otra API. El documento IS-SU-TS 23915 no está en el repositorio, y el cliente SMPP (host, puerto, TLS) sigue sin confirmar. Lo marcado *(estándar)* viene de 3GPP TS 23.048 y TS 23.040, que tampoco están en la carpeta del proyecto; verificar contra el texto antes de afirmarlo en el Brief.

## 1. Las capas que se pueden ver

| Capa | Tramo | Qué contiene | Visible con Wireshark |
|---|---|---|---|
| Norte | Consumidor (página web de campañas por CSV, aplicaciones VAS) → Aircast, API REST en `10.40.35.118:8082`, **HTTP sin TLS** [POSTMAN] | `UstkRequest` de tipo Text, Menu, Url, Call o Ussd, cuerpo JSON (sección 4) | Sí, en claro |
| Norte (retorno) | `POST http://10.45.56.53:8980/topup/callBackSatPush/` hacia una aplicación de recargas [POSTMAN]. Inferencia: la colección solo trae la petición de ejemplo y supongo que Aircast es quien la envía | `result`, `requestId`, `campaignId`, `lastActionId`, `msisdn` | Sí, en claro |
| Sur | Aircast → SMSC, cliente SMPP | `submit_sm` con el paquete OTA; vuelven `submit_sm_resp`, `deliver_sm` (recibos y MO) | Sí si no usa TLS |
| Radio | SMSC → red → SIM | SMS-PP hacia el applet por TAR | No (no es IP) |

Lo que se busca en cada capa está en la sección 5.

## 2. Reglas de seguridad antes de capturar

Vienen del Brief (nota de seguridad, Fase 0, R15) y de la naturaleza del tráfico:

1. **Autorización escrita** del dueño del servidor/red y de la operación. Capturar solo **líneas de prueba**.
2. El PDU `bind_transmitter`/`bind_transceiver` de SMPP lleva `system_id` y **`password` en claro** si no hay TLS. Tratar el .pcap como secreto.
3. **No guardar capturas dentro de esta carpeta ni en OneDrive.** El proyecto vive en una carpeta sincronizada con la nube; el propio Brief marca eso como exposición (OQ-10, R15). Usar una carpeta local fuera de OneDrive, por ejemplo `C:\captures\aircast\`, en un disco cifrado (BitLocker).
4. Los .pcap/.pcapng/.etl están ahora en `.gitignore` como segunda barrera.
5. Borrar las capturas al terminar el análisis y dejar constancia (el Brief exige "later deletion").
6. No pegar en el Brief ni en chats: MSISDN, IMSI, ICCID reales, `system_id`/`password`, ni bytes del paquete OTA completo. Para compartir hallazgos, usar agregados o enmascarar.

## 3. Cómo capturar

### 3.1 Dónde (decidir primero)

| Punto de captura | Ve la capa norte | Ve la capa sur | Requiere |
|---|---|---|---|
| En el servidor de Aircast (datacenter de Nuevatel) | Sí | Sí | Acceso root al servidor |
| Puerto espejo (SPAN) hacia una máquina con Wireshark | Según el segmento | Según el segmento | Red / datacenter |
| En el SMSC o el firewall SMS | No | Sí (lado SMSC) | Dueño del SMSC |
| En tu laptop | Solo si tu laptop es el cliente que llama a la API | No (no pasa por tu equipo) | Nada especial |

**Recomendación:** capturar en el servidor `10.40.35.118` con `tcpdump` (herramienta de consola, ligera) y analizar el archivo con Wireshark en la laptop. No instalar Wireshark en el servidor: es una aplicación gráfica, pide dependencias y un cambio en un servidor de producción, y no aporta nada frente a `tcpdump`. Ver 3.2.

Límite a verificar: el nombre del despliegue (`aircast-slave-api-rest-server-war`) sugiere un nodo "slave" de la API. Puede que el cliente SMPP corra en **otro** nodo. En `10.40.35.118` se ve seguro la capa norte; la capa sur solo si el SMPP sale de ahí (se comprueba con el paso 2 de 3.2).

### 3.2 En el servidor 10.40.35.118 (Linux, recomendado)

Supone Linux (Aircast corre como WAR); si es Windows, usar `pktmon` como en 3.3.

**Paso 1. ¿Hay `tcpdump`?** Si no está, pedir al administrador que lo instale o que otorgue la capacidad de captura; no instalar Wireshark.

```bash
which tcpdump
```

**Paso 2. Averiguar con quién habla Aircast.** Es de solo lectura y no captura nada. Muestra las conexiones establecidas de los procesos Java: ahí aparecerán el bind SMPP (IP del SMSC y su puerto, habitual 2775; 3550 es común con TLS) y cualquier salto interno hacia otro nodo de Aircast.

```bash
sudo ss -tnp state established | grep java
```

**Paso 3. Capturar la capa norte y el retorno.** Filtro de captura (BPF), con duración acotada: `-G 900 -W 8` rota cada 15 min y se detiene solo tras 8 archivos (2 h).

```bash
sudo tcpdump -i any -s 0 -n -w /var/tmp/aircast-%Y%m%d-%H%M.pcap -G 900 -W 8 \
  'tcp port 8082 or (host 10.45.56.53 and tcp port 8980)'
```

Cuando el paso 2 muestre el SMPP, repetir (o ampliar el filtro) con `or (host <IP_SMSC> and tcp port <PUERTO_SMPP>)`. Capturar solo lo necesario: el filtro BPF es la mejor protección de privacidad, porque lo que no se captura no hay que borrarlo.

**Paso 4. Traer el archivo.** `scp` a una carpeta de la laptop fuera de OneDrive (ver sección 2), y borrar el original del servidor.

#### Variante: captura remota en vivo

Wireshark puede leer el `tcpdump` del servidor por SSH sin instalar nada allá (interfaz *SSH remote capture / sshdump*, o `ssh ... | Wireshark -k -i -` desde `cmd.exe`; PowerShell 5.1 corrompe el flujo binario). Sirve para pruebas cortas de pocos minutos. Desventajas: el tráfico capturado viaja por la red hasta la laptop, depende de la sesión SSH, y no deja archivo en el servidor para auditar. Para el flujo del Brief (captura acotada, autorizada y borrada después), el archivo en el servidor es mejor.

#### Variante: solo saber quién llama a la API (sin contenido)

Para el inventario de consumidores del Brief (¿qué sistemas llaman hoy a la API de Aircast?), basta capturar los intentos de conexión, sin cuerpo ni números:

```bash
sudo tcpdump -i any -n -w /var/tmp/aircast-clientes-%Y%m%d-%H.pcap -G 3600 -W 24 \
  'tcp dst port 8082 and tcp[tcpflags] == tcp-syn'
```

En Wireshark: Statistics > Endpoints > IPv4 da la lista de IP origen. Con conexiones persistentes subestima el volumen de peticiones, pero sirve para saber **quién** llama. Los registros de acceso del servidor web de Aircast, si existen, dan lo mismo sin capturar nada.

### 3.3 En la laptop con Wireshark

Wireshark **no está instalado** en esta máquina (tampoco tshark ni Npcap). Instalación oficial, desde PowerShell, que el usuario ejecuta (requiere administrador para Npcap):

```powershell
winget install --id WiresharkFoundation.Wireshark -e
```

Alternativa sin instalar nada: `pktmon` (ya incluido en Windows). Desde PowerShell **como administrador**:

```powershell
New-Item -ItemType Directory -Force C:\captures\aircast | Out-Null
pktmon filter remove
pktmon filter add AircastApi -p <PUERTO_API>
pktmon start --capture --comp nics --pkt-size 0 --file-name C:\captures\aircast\aircast.etl
# ... ejecutar la prueba ...
pktmon stop
pktmon etl2pcap C:\captures\aircast\aircast.etl --out C:\captures\aircast\aircast.pcapng
```

Comprobar las opciones con `pktmon help start` si alguna cambia en esta versión de Windows.

### 3.4 Si el SMPP va por TLS

La API REST de Aircast va por HTTP [POSTMAN] y no necesita esto. Aplica solo si el paso 2 de 3.2 muestra que el bind SMPP usa TLS. (La API de la app Viva que también trae la colección es HTTPS, pero no es de Aircast y queda fuera de este análisis.) Wireshark solo ve el cifrado. Opciones, de más a menos limpia:

- Capturar **detrás del terminador TLS** (por ejemplo entre el proxy inverso y Aircast), donde el tráfico vuelve a ir en claro.
- En un cliente de prueba propio (navegador, o Java/curl con soporte), exportar las llaves de sesión con la variable `SSLKEYLOGFILE` y cargarlas en Wireshark (Edit > Preferences > Protocols > TLS > *(Pre)-Master-Secret log filename*).
- Probar en un entorno de laboratorio donde la API responda por HTTP.

## 4. Prueba controlada (una línea de prueba)

Para poder correlacionar capa norte y capa sur, enviar **una petición por tipo** a una sola línea de prueba y anotar la hora exacta de cada una:

| # | `type` | Petición de la colección | Hora de envío | Resultado visto en la SIM | Observaciones |
|---|---|---|---|---|---|
| 1 | `TextRequest` | "sat sms whitelist" | | | |
| 2 | `MenuRequest` | "sat 2 menu" | | | |
| 3 | `UrlRequest` | "sat 2 landing" | | | |
| 4 | `CallRequest` | "sat 2 Call" | | | |
| 5 | `UssdRequest` | "sat ussd 511" | | | |

**Antes de enviar, cambiar el `msisdn` por el de la línea de prueba.** La colección trae números que parecen de abonados reales y `campaignId` de campañas que parecen reales (inferencia): enviarlas tal cual podría llegar a un cliente o contaminar los contadores de una campaña. Preguntar al operador de Aircast qué `campaignId` usar para pruebas. Tampoco ejecutar desde Postman las dos peticiones "callback" de la colección: ambas apuntan al mismo host `10.45.56.53`, sea desa o prod, y llegarían a una aplicación real.

#### Contrato de la API según la colección [POSTMAN], sin captura todavía

`POST http://10.40.35.118:8082/aircast-slave-api-rest-server-war/api/pub/v1/ustk/UstkRequest`, cuerpo JSON. La colección no define cabeceras ni autenticación para esta API (las listas de cabeceras están vacías); la captura confirmará si viaja alguna. No incluye ejemplos de respuesta.

| `type` | Campos comunes | Campos propios |
|---|---|---|
| `TextRequest` | `type`, `msisdn`, `requestId`, `campaignId`, `requestDeliveryReport`, `text1` | `tpda`, `mo` |
| `UssdRequest` | ídem | `ussdString` (por ejemplo `*511#`) |
| `UrlRequest` | ídem | `title2`, `url`, `flashSmsText`, `smsText`, `alwaysSendSmsText` |
| `CallRequest` | ídem | `title2`, `tpda` |
| `MenuRequest` | ídem | `title2`, `items[]` con `text`, `value` y, opcionales, `tpda` y `mo` |

Notas: `requestId` aparece como número y una vez como texto. Inferencias sin probar: `tpda` sería la dirección de destino del SMS MO o el número a llamar, y `mo` el texto de ese SMS cuando el abonado acepta. Ninguna petición lleva la URL de callback, así que el destino del callback estaría configurado en Aircast. Para el contrato compatible (ADR-1), estos cinco `type` son el mínimo que debe reproducir la API unificada.

Repetir la #1 dos o tres veces seguidas: sirve para ver cómo evoluciona el contador (sección 5.2). Registrar en una tabla aparte el ICCID/MSISDN de la línea de prueba, **fuera del repositorio**.

## 5. Qué mirar en Wireshark

### 5.1 Capa norte (REST)

Filtros de visualización (puerto y ruta tomados de la colección [POSTMAN]):

```
tcp.port == 8082 && http.request.method == "POST"
http.request.uri contains "/api/pub/v1/ustk/UstkRequest"
http.request.uri contains "callBackSatPush"
```

Si Wireshark muestra TCP crudo en el 8082, no lo reconoce como HTTP: Analyze > Decode As… > TCP port 8082 → HTTP.

Clic derecho en un paquete > *Follow > HTTP Stream* para ver la solicitud y la respuesta completas. Anotar: URL y método, cabeceras de autenticación (sin copiar el valor), formato del cuerpo (JSON/XML), nombres y tipos de campo de cada `UstkRequest`, campos opcionales, códigos de respuesta, y si hay callback o consulta de estado. Esto es el insumo del contrato compatible (ADR-1).

### 5.2 Capa sur (SMPP)

Si el puerto no es estándar: Analyze > Decode As… > TCP port → SMPP.

| Para ver | Filtro |
|---|---|
| Todo el SMPP | `smpp` |
| Quién se conecta (binds) | `smpp.command_id == 0x00000002 \|\| smpp.command_id == 0x00000009 \|\| smpp.command_id == 0x00000001` |
| Envíos | `smpp.command_id == 0x00000004` |
| Respuesta del SMSC a cada envío | `smpp.command_id == 0x80000004` |
| Recibos y mensajes MO (Discovery, pruebas de recepción) | `smpp.command_id == 0x00000005` |
| Solo OTA (PID de descarga de datos a la SIM) | `smpp.command_id == 0x00000004 && smpp.protocol_id == 0x7f` |
| OTA con DCS clase 2 de 8 bits | `smpp.protocol_id == 0x7f && smpp.data_coding == 0xf6` |
| Una línea de prueba | `smpp.destination_addr == "<MSISDN_PRUEBA>"` |

Comprobar los nombres de campo en la versión instalada: `tshark -G fields | findstr /i smpp`.

Qué anotar por cada `submit_sm`:

- **Cuántos `submit_sm` genera cada UstkRequest** (¿uno, o varios concatenados?) y en qué orden.
- `source_addr` (origen que usa Aircast) y `destination_addr`: el origen interesa para OQ-8 (qué orígenes autoriza el firewall mientras convivan Aircast y Nuevatel).
- `esm_class` (¿UDHI activo?), `protocol_id`, `data_coding`, `registered_delivery`, `validity_period`, y si el contenido viaja en `short_message` o en el TLV `message_payload`.
- `system_id` del bind y la IP origen de cada conexión: sirve para OQ-28 y OQ-34 (¿la aplicación SAT PUSH y Aircast usan la misma conexión directa y sin firewall?). **No copiar el `password`.**
- Tasa de envío (Statistics > I/O Graph con `smpp.command_id == 0x00000004`) como dato de TPS para OQ-8.

### 5.3 El paquete OTA dentro de `short_message`

Wireshark decodifica SMPP y la capa SMS, pero **no el paquete de comando de 23.048** *(conviene confirmarlo en la versión instalada)*. Para eso está [decode_ota_header.py](decode_ota_header.py), en esta carpeta (uso abajo). Estructura que decodifica *(contrastada con dos implementaciones abiertas, pycrate y pySim; no verificada con tráfico de Aircast)*: tras la UDH (`02 70 00` en un comando, `02 71 00` en una respuesta) vienen CPL (2 octetos), CHL (1), **SPI** (2), **KIc**, **KID**, **TAR** (3), **CNTR** (5), PCNTR, RC/CC/DS y los datos. Si CPL no coincide con el largo real, el script lo avisa: es la señal de que el marco real es otro.

Lo que se ve **en claro** aunque el paquete esté protegido, y por qué importa:

| Campo | Qué responde en el Brief |
|---|---|
| **TAR** | A qué aplicación va: `534054` S@T, `505348` PSH, `534C59` Sleepy, `B00010` SIM_RFM, `B20100` Admin Agent (addendum A). Confirma qué usa hoy cada tipo de UstkRequest |
| **SPI** | Nivel de seguridad real: sin protección (`0000`) o checksum criptográfico con contador mayor (`1200`) en S@T; para Sleepy se espera MSL 0. Alimenta R11 y OQ-27 |
| **KIc / KID** | Algoritmo y clave que usa cada envío (el byte, no la clave) |
| **CNTR** | Si el SPI indica sin cifrado, el contador va en claro: permite ver los valores que usa Aircast por tarjeta y cómo avanzan entre envíos. Con cifrado activo no se ve. Es evidencia útil para OQ-4 (modo mayor-que o exacto +1) y OQ-33 (salto de contador). Es una inferencia a probar, no un hecho confirmado |

Sleepy usa un formato propio con AES o 3DES (addendum K): se verá el TAR `534C59` pero el contenido seguirá opaco.

### 5.4 Retorno

Buscar en los `deliver_sm` el recibo de entrega y el **paquete de respuesta** de la SIM (prueba de recepción). Es la evidencia que pide la condición 1 del Brief (lectura RFM real con prueba positiva de recepción) y muestra cómo reporta Aircast el resultado de vuelta al consumidor.

## 6. Extracción a CSV (para análisis fuera de Wireshark)

Requiere tshark (viene con Wireshark). El resultado contiene MSISDN: guardarlo junto a la captura, fuera del repositorio, y enmascarar antes de compartir.

```powershell
tshark -r C:\captures\aircast\aircast.pcapng -Y "smpp.command_id == 0x00000004" `
  -T fields -E header=y -E separator=, -E quote=d `
  -e frame.time_epoch -e ip.src -e ip.dst -e smpp.sequence_number `
  -e smpp.source_addr -e smpp.destination_addr -e smpp.esm_class `
  -e smpp.protocol_id -e smpp.data_coding -e smpp.registered_delivery `
  -e smpp.short_message > C:\captures\aircast\submit_sm.csv
```

El campo `-e smpp.password` **no se incluye** a propósito.

### Decodificar la cabecera OTA de ese CSV

`decode_ota_header.py` solo usa la biblioteca estándar de Python y **no necesita ni usa llaves**: no descifra ni verifica checksums, solo lee los campos en claro. Se ejecuta con `py` (el `python` de WindowsApps en esta máquina es un acceso directo a la Tienda) y con `-I`, que aísla el intérprete al procesar datos capturados.

```powershell
# 0. Comprobar que el script funciona (paquetes sintéticos; no prueba tráfico real)
py -3.14 -I decode_ota_header.py --selftest

# 1. Un mensaje suelto (hex, con o sin espacios): detalle campo por campo
py -3.14 -I decode_ota_header.py 02 70 00 00 1A 15 12 00 ...

# 2. Todo el CSV: una línea por mensaje, más un resumen
py -3.14 -I decode_ota_header.py --csv C:\captures\aircast\submit_sm.csv --out C:\captures\aircast\ota_resumen.csv
```

Qué entrega el modo CSV: por cada mensaje, TAR y aplicación, SPI, integridad, si va cifrado, modo de contador y el **CNTR cuando es legible**; al final, las combinaciones vistas (tipo, TAR, SPI, cifrado, modo de contador) con su cantidad, y **la secuencia del contador por destino y TAR**, con el paso entre envíos consecutivos. Esa secuencia es la evidencia directa para OQ-4 y OQ-33. El destino sale enmascarado (últimos 4 dígitos) salvo `--show-msisdn`; `--data` imprime también los datos asegurados cuando no van cifrados.

Antes de procesar todo, comprobar que `smpp.short_message` sale en hexadecimal y no como texto:

```powershell
tshark -r C:\captures\aircast\aircast.pcapng -Y "smpp.command_id == 0x00000004" -c 1 -T fields -e smpp.short_message
```

Si sale texto ilegible, buscar el campo binario con `tshark -G fields | findstr /i smpp` (o usar `-e data`). El script marca como `ERROR` las filas que no son hexadecimal, sin detenerse.

Respuestas de la SIM (UDH `02 71 00`): el script muestra el **código de estado** del PoR, por ejemplo `02 CNTR bajo` o `03 CNTR alto`. Es la forma más clara de ver si una SIM rechazó un envío por el contador, pero solo es legible si el PoR no va cifrado.

**Estado de validación:** las autopruebas usan paquetes sintéticos construidos con la misma lectura del estándar, así que solo comprueban coherencia interna. Hasta que se pase tráfico real de Aircast, tratar la salida como hipótesis: si CPL no coincide o aparecen bits reservados, el marco real es distinto y hay que ajustar el script.

## 7. Cómo registrar los hallazgos

Cuando haya resultados, llevarlos al Brief como agregados (formato, cantidades, TAR y SPI observados, nunca valores de llave ni identificadores reales) con una etiqueta de fuente propia, por ejemplo **[CAPTURA]**, junto a las ya existentes [DOC], [LLAVE] e [INFERENCE]. Cerrar o actualizar así: OQ-4, OQ-8, OQ-27, OQ-28, OQ-33, OQ-34, y el contrato de ADR-1.

## 8. Pendiente de confirmar

- Qué host tiene el cliente SMPP de Aircast (¿el mismo `10.40.35.118` o otro nodo?), su puerto y si usa TLS.
- Si hay saltos internos entre el nodo "slave" de la API y el resto de Aircast.
- Quién autoriza la captura en `10.40.35.118` y si el servidor tiene `tcpdump`.
- Qué `campaignId` usar en las pruebas.
- MSISDN/ICCID de la línea de prueba y de qué familia de SIM es (idealmente un lote conocido, como NTE04570).
