---
title: "Procedimiento de captura remota del tráfico de Aircast desde una estación Windows o macOS"
version: "1.0"
status: "para aprobación"
created: 2026-11-04
updated: 2026-11-09
basis: "Fase 0 del brief de la Nuevatel SAT Platform (versión del 2026-10-30); acuerdo con Infraestructura y Seguridad: captura remota desde una estación Windows o macOS"
---

# Procedimiento de captura remota del tráfico de Aircast

## Control del documento

| Versión | Fecha | Cambio |
|---|---|---|
| 0.1 | 2026-11-04 | Borrador con varios escenarios de captura (en el servidor, espejo de puerto, laptop) |
| 1.0 | 2026-11-09 | Se limita al escenario acordado con Infraestructura y Seguridad: captura remota desde una estación Windows o macOS |

| Aprobación | Nombre | Fecha | Firma |
|---|---|---|---|
| Infraestructura (dueño del servidor 10.40.35.118) | | | |
| Seguridad de la Información | | | |
| Responsable de la Fase 0 | | | |

> Fuentes: **[DOC]** documento del proyecto; **[POSTMAN]** colección de la API de Aircast `PUSH-ussd-sat`; **[INFERENCE]** inferencia sin probar. Las referencias OQ-n, Rn y ADR-n remiten al brief completo. Este documento no contiene llaves, contraseñas ni números de abonados.

## 1. Objetivo

Obtener, con la mínima exposición posible, evidencia de lo que Aircast envía realmente cuando un consumidor llama a su API:

- el contrato real de la API (`UstkRequest`);
- los mensajes SMPP que genera hacia el SMSC;
- la cabecera de seguridad OTA de esos mensajes.

Es la Prueba 1 de la Fase 0 ([brief acotado](../briefs/brief-sat-push-2026-11-04/brief.md)). Sus resultados alimentan el contrato de la API de envío unificada (ADR-1) y las preguntas OQ-4, OQ-8, OQ-27, OQ-28, OQ-30, OQ-33 y OQ-34. La captura **no** entrega la llave de Sleepy ni mide la cobertura de llaves.

## 2. Alcance

**Incluye únicamente este escenario.** El analista, desde una estación Windows o macOS, abre una sesión SSH al servidor de la API de Aircast (`10.40.35.118`) y ejecuta un script fijo que corre `tcpdump` con un filtro y una duración acotados. La captura viaja cifrada por esa misma sesión y se guarda solo en la estación. **Nada se escribe en el disco del servidor.**

**No incluye:**

- captura con archivo en el servidor;
- puertos espejo (SPAN), ni captura en el SMSC o en el firewall;
- captura local en la estación (`pktmon`, Npcap);
- descifrado de TLS;
- envíos a abonados reales.

Cualquier otro escenario requiere un nuevo acuerdo con Infraestructura y Seguridad.

## 3. Referencias

| Referencia | Ubicación |
|---|---|
| Brief completo, Fase 0 y Decisión 8 | `brief-sat-push-2026-10-22`, versión del 2026-10-30 (rama `origin/brief/sat-platform-update-2026-10-30`) |
| Brief acotado de la Fase 0 | [brief.md](../briefs/brief-sat-push-2026-11-04/brief.md) y su [addendum](../briefs/brief-sat-push-2026-11-04/addendum.md) |
| Script del servidor | [aircast-capture.sh](aircast-capture.sh) |
| Regla sudo | [aircast-capture.sudoers](aircast-capture.sudoers) |
| Decodificador de cabeceras OTA | [decode_ota_header.py](decode_ota_header.py) |
| Colección Postman `PUSH-ussd-sat` | **Fuera del repositorio**: contiene números reales y una credencial de otra API |

## 4. Roles y responsabilidades

| Rol | Responsabilidades |
|---|---|
| Analista de captura | Prepara su estación, ejecuta la captura y la prueba controlada, analiza, borra y completa el acta |
| Infraestructura | Instala el script y la regla sudo, da de alta las llaves SSH, confirma el nodo y el puerto del SMPP, y revoca el acceso al cerrar la ventana |
| Seguridad de la Información | Aprueba la ventana, revisa el acta, verifica el borrado y consulta los registros del servidor |
| Operador de Aircast | Indica el `campaignId` de prueba y confirma que la línea de prueba puede recibir campañas |
| Responsable de la línea de prueba | Entrega la línea y la SIM de prueba. Sus identificadores no se escriben en el repositorio |

## 5. Arquitectura de la captura

```text
Estación del analista (Windows o macOS)              Servidor de la API de Aircast 10.40.35.118 (Linux)

  ssh aircast-cap "sudo -n ... api 30"  ── SSH, TCP 22, cifrado ──▶  aircast-capture (script fijo, root vía sudo)
                                                                        └─ timeout ─ tcpdump -w -  (sin archivo)
  archivo .pcap  ◀───────── flujo pcap por el mismo canal SSH ─────────┘
  Wireshark / tshark / decode_ota_header.py
```

Propiedades del diseño:

- **Sin archivos en el servidor.** `tcpdump` escribe por la salida estándar y el flujo llega a la estación por SSH.
- **Filtro fijado en el servidor.** El analista elige un perfil; no puede ampliar el filtro ni pasar opciones a `tcpdump`.
- **Duración acotada.** Entre 1 y 120 minutos por ejecución; al vencer, `timeout` detiene `tcpdump`.
- **Trazabilidad.** Cada ejecución queda en el syslog del servidor (etiqueta `aircast-capture`, con el usuario) y en el registro de sudo.

## 6. Requisitos previos

### 6.1 Servidor 10.40.35.118 (Infraestructura)

1. Comprobar que existen `tcpdump`, `timeout` y `logger`:

   ```bash
   command -v tcpdump timeout logger
   ```

2. Instalar el script, ajustando antes la variable `TCPDUMP` a la ruta real:

   ```bash
   install -o root -g root -m 0755 aircast-capture.sh /usr/local/sbin/aircast-capture
   ```

3. Crear el grupo `aircast-cap` y agregar las cuentas **personales** de los analistas. No usar cuentas compartidas.
4. Instalar la regla sudo con `visudo -f /etc/sudoers.d/aircast-capture` (contenido de [aircast-capture.sudoers](aircast-capture.sudoers)) y validarla con `visudo -cf`.
5. Dar de alta la llave pública de cada analista en su `authorized_keys`, restringida:

   ```text
   from="<IP de la estación o de la VPN>",no-port-forwarding,no-agent-forwarding,no-X11-forwarding,no-pty ssh-ed25519 AAAA... aircast-cap <nombre>
   ```

6. Entregar al analista, por un canal distinto al correo del proyecto, la huella de la llave del servidor:

   ```bash
   ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
   ```

7. Perfil `smpp`: identificar con quién habla Aircast y, si el enlace SMPP sale de este nodo, completar `SMSC_FILTRO` en el script (por ejemplo `'host <IP_SMSC> and tcp port <PUERTO>'`). Si el SMPP corre en otro nodo, la captura de la capa sur requiere repetir esta configuración allí, con nueva aprobación.

   ```bash
   ss -tnp state established | grep java
   ```

> **No conceder `sudo tcpdump` genérico.** `tcpdump -z` ejecuta un comando arbitrario, así que una regla sudo abierta sobre `tcpdump` equivale a dar root. El script fija las opciones y el filtro; la regla sudo autoriza solo el script.

**Perfiles del script**

| Perfil | Filtro de captura | Para qué |
|---|---|---|
| `check` | No captura | Verifica el acceso y la versión de `tcpdump` |
| `api` | `tcp port 8082 or (host 10.45.56.53 and tcp port 8980)` | API REST de Aircast y el callback hacia la aplicación de recargas (capa norte) |
| `clientes` | `tcp dst port 8082 and tcp[tcpflags] == tcp-syn` | Solo qué sistemas llaman a la API: sin cuerpos ni números (OQ-30) |
| `smpp` | Lo define Infraestructura (`SMSC_FILTRO`) | Enlace SMPP hacia el SMSC, si sale de este nodo (capa sur) |

### 6.2 Estación del analista

| Requisito | Windows | macOS |
|---|---|---|
| Sistema | Windows 10 (1809 o posterior) u 11 | Versión de macOS con soporte del fabricante |
| Cliente SSH | OpenSSH integrado; comprobar con `ssh -V`. Si falta: Configuración > Características opcionales > Cliente OpenSSH | Integrado |
| Wireshark | Instalador oficial de wireshark.org. Npcap no es necesario para este procedimiento | Imagen `.dmg` oficial de wireshark.org (Apple Silicon o Intel) |
| Cifrado de disco | BitLocker activo (`manage-bde -status C:`, como administrador) | FileVault activo (`fdesetup status`) |
| Carpeta de capturas | `%USERPROFILE%\captures\aircast`. No debe estar dentro de Escritorio, Documentos ni Imágenes, que OneDrive puede respaldar | `~/captures/aircast`, con permisos 700. No debe estar dentro de Escritorio ni Documentos, que iCloud puede sincronizar |
| Terminal para capturar | **Símbolo del sistema (`cmd.exe`).** No usar Windows PowerShell 5.1: al redirigir la salida la reescribe como texto UTF-16 y el archivo queda inservible | Terminal (zsh) |
| Python 3 (decodificador) | `py -3` | `python3` |

### 6.3 Llave SSH y configuración del cliente

Cada analista genera una llave **personal, con frase de paso**, y entrega a Infraestructura **solo** el archivo `.pub`.

Windows (`cmd.exe`):

```bat
ssh-keygen -t ed25519 -f "%USERPROFILE%\.ssh\id_ed25519_aircast" -C "aircast-cap <nombre>"
```

macOS:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_aircast -C "aircast-cap <nombre>"
```

Agregar esta entrada al archivo de configuración SSH (Windows: `%USERPROFILE%\.ssh\config`; macOS: `~/.ssh/config`). Los comandos de este procedimiento usan el alias `aircast-cap`.

```text
Host aircast-cap
    HostName 10.40.35.118
    User <usuario personal>
    IdentityFile ~/.ssh/id_ed25519_aircast
    IdentitiesOnly yes
    # ProxyJump <bastión>     (solo si Seguridad exige pasar por un bastión)
```

En la primera conexión, comparar la huella que muestra `ssh` con la entregada por Infraestructura. **Si no coincide, no continuar** y avisar a Seguridad.

### 6.4 Red

TCP 22 desde la estación (o su VPN o bastión) hacia `10.40.35.118`, abierto solo durante la ventana. La restricción `from=` de la llave debe coincidir con la IP que ve el servidor; con VPN, esa es la IP de la VPN.

### 6.5 Antes de cada ventana

- [ ] Acta de captura abierta con su identificador (sección 10).
- [ ] Ventana aprobada por Seguridad: fecha, hora de inicio y de fin.
- [ ] Línea y SIM de prueba asignadas; su referencia anotada fuera del repositorio.
- [ ] `campaignId` de prueba confirmado por el operador de Aircast.
- [ ] Perfiles y minutos que se van a ejecutar.
- [ ] Si se captura la capa sur: `SMSC_FILTRO` completado por Infraestructura.

## 7. Controles de seguridad obligatorios

| N.º | Control |
|---|---|
| C1 | La captura solo se ejecuta dentro de la ventana aprobada. Fuera de ella, la regla sudo y las llaves están deshabilitadas |
| C2 | Solo líneas de prueba. Las peticiones de la colección se envían con el `msisdn` de la línea de prueba y el `campaignId` de prueba. Nunca se ejecutan las peticiones "callback" de la colección |
| C3 | El filtro lo fija el script del servidor. Cambiar o agregar un perfil requiere un cambio aprobado por Seguridad |
| C4 | Cada ejecución dura como máximo 120 minutos |
| C5 | Nada se escribe en el disco del servidor |
| C6 | Acceso solo con llave SSH personal ed25519 con frase de paso, y con la huella del servidor verificada |
| C7 | Las capturas se guardan solo en la estación, con cifrado de disco activo y fuera de carpetas sincronizadas (OneDrive, iCloud). Nunca en el repositorio, en correo, en chat ni en medios extraíbles |
| C8 | El archivo `.pcap` es secreto: puede contener el `system_id` y la contraseña del enlace SMPP, números de la línea de prueba y el contenido de los mensajes |
| C9 | Hacia fuera solo se comparten agregados: el resumen enmascarado del decodificador y el informe de hallazgos. Nunca el `.pcap` ni el CSV completo |
| C10 | Las capturas se borran al terminar el análisis y, como máximo, `<N>` días hábiles después de la captura (plazo a fijar por Seguridad). El borrado queda en el acta |
| C11 | Al cerrar la ventana, Infraestructura retira las llaves y la regla sudo, y lo registra en el acta |

## 8. Procedimiento

### Paso 1. Verificar el acceso (no captura)

Igual en Windows (`cmd.exe`) y macOS:

```text
ssh aircast-cap "sudo -n /usr/local/sbin/aircast-capture check"
```

Resultado esperado: la versión de `tcpdump` y de `libpcap`. Si aparece otro mensaje, ver la sección 11.

### Paso 2. Iniciar la captura

El nombre del archivo sigue la convención `aircast-<perfil>-AAAAMMDD-HHMM.pcap`, con la hora de inicio. Los mensajes de estado de `tcpdump` ("listening on any...") salen en la terminal, no en el archivo. Dejar la terminal abierta durante toda la prueba.

Windows (`cmd.exe`; reemplazar fecha y hora en el nombre):

```bat
mkdir "%USERPROFILE%\captures\aircast"
ssh aircast-cap "sudo -n /usr/local/sbin/aircast-capture api 30" > "%USERPROFILE%\captures\aircast\aircast-api-20261110-1000.pcap"
```

macOS:

```bash
mkdir -p ~/captures/aircast && chmod 700 ~/captures ~/captures/aircast
ssh aircast-cap "sudo -n /usr/local/sbin/aircast-capture api 30" > ~/captures/aircast/aircast-api-$(date +%Y%m%d-%H%M).pcap
```

**Variante con vista en vivo (opcional).** La captura se abre directamente en Wireshark.

Windows (`cmd.exe`). Al terminar, guardar con File > Save As en la carpeta de capturas:

```bat
ssh aircast-cap "sudo -n /usr/local/sbin/aircast-capture api 30" | "C:\Program Files\Wireshark\Wireshark.exe" -k -i -
```

macOS (guarda el archivo y abre Wireshark a la vez):

```bash
ssh aircast-cap "sudo -n /usr/local/sbin/aircast-capture api 30" | tee ~/captures/aircast/aircast-api-$(date +%Y%m%d-%H%M).pcap | /Applications/Wireshark.app/Contents/MacOS/Wireshark -k -i -
```

También sirve la interfaz *SSH remote capture* (sshdump) de Wireshark, con el alias `aircast-cap` y el comando remoto `sudo -n /usr/local/sbin/aircast-capture api 30`. En Windows, sshdump es un componente opcional del instalador. Mientras no se guarda, Wireshark mantiene la captura en un archivo temporal (`wireshark_*` en la carpeta temporal del usuario), que se borra en el paso 5.

### Paso 3. Ejecutar la prueba controlada

Con la captura en marcha, enviar **una petición por tipo** a la API de Aircast. Anotar la hora exacta de cada envío para poder correlacionar la capa norte con la capa sur.

| # | `type` | Petición de la colección | Hora de envío | Resultado en la SIM | Observaciones |
|---|---|---|---|---|---|
| 1 | `TextRequest` | "sat sms whitelist" | | | |
| 2 | `MenuRequest` | "sat 2 menu" | | | |
| 3 | `UrlRequest` | "sat 2 landing" | | | |
| 4 | `CallRequest` | "sat 2 Call" | | | |
| 5 | `UssdRequest` | "sat ussd 511" | | | |

- **Antes de enviar, cambiar el `msisdn` por el de la línea de prueba y usar el `campaignId` de prueba** (C2). La colección trae números y campañas que parecen reales [INFERENCE].
- Repetir la petición 1 dos o tres veces seguidas. Así se ve cómo avanza el contador de la tarjeta (sección 9.4).
- No ejecutar las peticiones "callback" de la colección: ambas apuntan al mismo host `10.45.56.53` y llegarían a una aplicación real.
- Si las peticiones salen desde Postman en la estación del analista, la IP de la estación aparecerá como cliente de la API en la captura.

### Paso 4. Detener y verificar

1. La captura termina sola al vencer los minutos pedidos, o se detiene con Ctrl+C después del último envío. Tras Ctrl+C, el proceso remoto termina con el siguiente paquete que coincida con el filtro o, a más tardar, al vencer los minutos. Para comprobarlo:

   ```text
   ssh aircast-cap "pgrep -a tcpdump"
   ```

   Si la ventana está por cerrar y el proceso sigue activo, pedir a Infraestructura que lo detenga.

2. Comprobar el archivo y calcular su huella SHA-256. Anotar paquetes, duración y huella en el acta.

   Windows (`cmd.exe`):

   ```bat
   "C:\Program Files\Wireshark\capinfos.exe" -c -u "%USERPROFILE%\captures\aircast\aircast-api-20261110-1000.pcap"
   certutil -hashfile "%USERPROFILE%\captures\aircast\aircast-api-20261110-1000.pcap" SHA256
   ```

   macOS:

   ```bash
   /Applications/Wireshark.app/Contents/MacOS/capinfos -c -u ~/captures/aircast/<archivo>.pcap
   shasum -a 256 ~/captures/aircast/<archivo>.pcap
   ```

### Paso 5. Analizar

Seguir la sección 9. Todo el análisis se hace en la estación, sobre la carpeta de capturas.

### Paso 6. Borrar y cerrar

Windows (`cmd.exe`). `del` no pasa por la Papelera de reciclaje:

```bat
del /q "%USERPROFILE%\captures\aircast\*"
del /q "%TEMP%\wireshark_*"
dir "%USERPROFILE%\captures\aircast"
```

macOS. `find` no pasa por la Papelera y no falla si la carpeta ya está vacía:

```bash
find ~/captures/aircast -type f -delete
find "$TMPDIR" -maxdepth 1 -name 'wireshark_*' -delete
ls -la ~/captures/aircast
```

Con el cifrado de disco activo (C7), lo borrado queda cifrado en reposo. En discos SSD, sobrescribir no garantiza un borrado físico; Seguridad decide si exige algo más.

Para cerrar: registrar el borrado en el acta, pedir a Infraestructura que retire las llaves y la regla sudo (C11) y entregar el acta a Seguridad.

## 9. Guía de análisis

### 9.1 Qué se ve desde 10.40.35.118

| Capa | Tramo | Contenido | Visible |
|---|---|---|---|
| Norte | Consumidores (página web de campañas por CSV, aplicaciones VAS) → API REST de Aircast en `10.40.35.118:8082` | `UstkRequest` de tipo Text, Menu, Url, Call o Ussd, cuerpo JSON | Sí: HTTP sin TLS [POSTMAN] |
| Norte, retorno | `POST http://10.45.56.53:8980/topup/callBackSatPush/` hacia la aplicación de recargas [POSTMAN] | `result`, `requestId`, `campaignId`, `lastActionId`, `msisdn` | Sí, si lo envía este nodo [INFERENCE] |
| Sur | Aircast → SMSC, cliente SMPP | `submit_sm` con el paquete OTA; vuelven `submit_sm_resp` y `deliver_sm` (recibos y MO) | Solo si el enlace SMPP sale de este nodo y no usa TLS |
| Radio | SMSC → red → SIM | SMS-PP hacia el applet, por TAR | No: no es tráfico IP |

Si el enlace SMPP usa TLS, este procedimiento no ve su contenido: queda fuera de alcance y se escala a Infraestructura y Seguridad.

### 9.2 Capa norte (REST)

Filtros de visualización:

```text
tcp.port == 8082 && http.request.method == "POST"
http.request.uri contains "/api/pub/v1/ustk/UstkRequest"
http.request.uri contains "callBackSatPush"
```

Si Wireshark muestra TCP sin decodificar en el puerto 8082: Analyze > Decode As… > TCP port 8082 → HTTP.

Clic derecho en un paquete > *Follow > HTTP Stream* muestra la solicitud y la respuesta completas. Anotar: URL y método; cabeceras de autenticación, sin copiar su valor; formato del cuerpo; nombres y tipos de cada campo por `type`; campos opcionales; códigos de respuesta; y si hay callback o consulta de estado. Es el insumo del contrato compatible (ADR-1). La colección no muestra autenticación [POSTMAN]: la captura confirma si viaja alguna cabecera.

### 9.3 Capa sur (SMPP)

Si el puerto no es el estándar: Analyze > Decode As… > TCP port → SMPP.

| Para ver | Filtro |
|---|---|
| Todo el SMPP | `smpp` |
| Quién se conecta (binds) | `smpp.command_id == 0x00000002 \|\| smpp.command_id == 0x00000009 \|\| smpp.command_id == 0x00000001` |
| Envíos | `smpp.command_id == 0x00000004` |
| Respuesta del SMSC a cada envío | `smpp.command_id == 0x80000004` |
| Recibos y mensajes MO | `smpp.command_id == 0x00000005` |
| Solo OTA (PID de descarga a la SIM) | `smpp.command_id == 0x00000004 && smpp.protocol_id == 0x7f` |
| OTA con DCS clase 2 de 8 bits | `smpp.protocol_id == 0x7f && smpp.data_coding == 0xf6` |
| Solo la línea de prueba | `smpp.destination_addr == "<MSISDN_PRUEBA>"` |

Para comprobar los nombres de campo en la versión instalada: `tshark -G fields`, filtrando por `smpp` (`findstr /i smpp` en Windows, `grep -i smpp` en macOS).

Qué anotar por cada `submit_sm`:

- Cuántos `submit_sm` genera cada `UstkRequest` y en qué orden.
- `source_addr` y `destination_addr`. El origen interesa para OQ-8: qué orígenes autoriza el firewall mientras convivan Aircast y Nuevatel.
- `esm_class` (¿UDHI activo?), `protocol_id`, `data_coding`, `registered_delivery`, `validity_period`, y si el contenido viaja en `short_message` o en el TLV `message_payload`.
- `system_id` del enlace y la IP de origen de cada conexión (OQ-28, OQ-34). **No copiar la contraseña** del bind (C8).
- Tasa de envío: Statistics > I/O Graph con `smpp.command_id == 0x00000004`, como dato de TPS para OQ-8.

### 9.4 Cabecera OTA dentro de `short_message`

Wireshark decodifica SMPP y la capa SMS, pero no la cabecera de seguridad de 3GPP TS 23.048 / ETSI TS 102 225. Para eso está [decode_ota_header.py](decode_ota_header.py) (sección 9.6). Lo que se ve en claro aunque el paquete esté protegido:

| Campo | Qué responde |
|---|---|
| **TAR** | A qué aplicación va: `534054` S@T, `505348` PSH, `534C59` Sleepy, `B00010` SIM_RFM, `B20100` Admin Agent. Muestra qué usa hoy cada tipo de `UstkRequest` |
| **SPI** | Nivel de seguridad real, por ejemplo sin protección (`0000`) o checksum criptográfico con contador mayor (`1200`). Alimenta R11 y OQ-27 |
| **KIc / KID** | Algoritmo y número de llave de cada envío; el byte, nunca la llave |
| **CNTR** | Si el SPI indica que no hay cifrado, el contador va en claro y se ve cómo avanza entre envíos (OQ-4, OQ-33). Con cifrado no se ve |

Sleepy usa un formato propio con AES o 3DES [DOC]: se verá su TAR, pero el contenido seguirá opaco.

### 9.5 Retorno

En los `deliver_sm`, buscar el recibo de entrega y el paquete de respuesta de la SIM (UDH `02 71 00`). El decodificador muestra su código de estado; por ejemplo, `02 CNTR bajo` indica un rechazo por contador. Solo es legible si la respuesta no va cifrada.

### 9.6 Extracción a CSV y decodificación

El CSV contiene números de la línea de prueba: se guarda en la carpeta de capturas y se borra con ella (C7, C10).

Windows (`cmd.exe`):

```bat
"C:\Program Files\Wireshark\tshark.exe" -r "%USERPROFILE%\captures\aircast\<archivo>.pcap" ^
  -Y "smpp.command_id == 0x00000004" -T fields -E header=y -E separator=, -E quote=d ^
  -e frame.time_epoch -e ip.src -e ip.dst -e smpp.sequence_number ^
  -e smpp.source_addr -e smpp.destination_addr -e smpp.esm_class ^
  -e smpp.protocol_id -e smpp.data_coding -e smpp.registered_delivery ^
  -e smpp.short_message > "%USERPROFILE%\captures\aircast\submit_sm.csv"
```

macOS:

```bash
/Applications/Wireshark.app/Contents/MacOS/tshark -r ~/captures/aircast/<archivo>.pcap \
  -Y 'smpp.command_id == 0x00000004' -T fields -E header=y -E separator=, -E quote=d \
  -e frame.time_epoch -e ip.src -e ip.dst -e smpp.sequence_number \
  -e smpp.source_addr -e smpp.destination_addr -e smpp.esm_class \
  -e smpp.protocol_id -e smpp.data_coding -e smpp.registered_delivery \
  -e smpp.short_message > ~/captures/aircast/submit_sm.csv
```

El campo `smpp.password` no se extrae, a propósito. Antes de procesar todo, extraer un solo mensaje (`-c 1 -e smpp.short_message`) y comprobar que sale en hexadecimal; si sale texto, buscar el campo binario con `tshark -G fields`.

El decodificador solo usa la biblioteca estándar de Python, **no usa llaves** y se ejecuta desde la carpeta de este procedimiento. La opción `-I` aísla el intérprete al procesar datos capturados.

| Acción | Windows (`cmd.exe`) | macOS |
|---|---|---|
| Autoprueba | `py -3 -I decode_ota_header.py --selftest` | `python3 -I decode_ota_header.py --selftest` |
| Un mensaje (hex) | `py -3 -I decode_ota_header.py 02 70 00 ...` | `python3 -I decode_ota_header.py 02 70 00 ...` |
| Todo el CSV | `py -3 -I decode_ota_header.py --csv "%USERPROFILE%\captures\aircast\submit_sm.csv" --out "%USERPROFILE%\captures\aircast\ota_resumen.csv"` | `python3 -I decode_ota_header.py --csv ~/captures/aircast/submit_sm.csv --out ~/captures/aircast/ota_resumen.csv` |

El modo CSV entrega, por mensaje: TAR, aplicación, SPI, integridad, cifrado, modo de contador y el contador cuando es legible. Al final resume las combinaciones vistas y la secuencia del contador por destino y TAR. El destino sale enmascarado salvo con `--show-msisdn`.

**Estado de validación del decodificador:** se contrastó con dos implementaciones abiertas (pycrate y pySim) y se probó solo con paquetes sintéticos. Hasta pasar tráfico real de Aircast, su salida es una hipótesis. Si avisa que CPL no coincide o que hay bits reservados activos, el formato real es otro y hay que ajustarlo.

### 9.7 Registro de hallazgos

Los hallazgos se llevan al brief como agregados, con la etiqueta de fuente **[CAPTURA]**: formatos, cantidades, TAR y SPI observados. Nunca valores de llave ni identificadores reales. Con ellos se cierran o actualizan OQ-4, OQ-8, OQ-27, OQ-28, OQ-30, OQ-33, OQ-34 y el contrato de ADR-1.

## 10. Acta de captura (plantilla)

Una por ventana. Se guarda con la documentación de la Fase 0; no contiene números de abonados ni el contenido de la captura.

| Campo | Valor |
|---|---|
| Identificador del acta | |
| Ventana aprobada (fecha, inicio, fin) y aprobador de Seguridad | |
| Analista y cuenta SSH usada | |
| Estación (nombre, sistema, cifrado de disco verificado) | |
| Referencia interna de la línea y la SIM de prueba | |
| `campaignId` de prueba | |
| Ejecuciones (perfil, minutos, hora de inicio) | |
| Archivos (nombre, paquetes, duración, SHA-256) | |
| Informe de hallazgos (referencia) | |
| Borrado (fecha, hora, método, verificación) | |
| Revocación de llaves y regla sudo (fecha, responsable de Infraestructura) | |
| Verificación de Seguridad (fecha, nombre) | |

## 11. Solución de problemas

| Síntoma | Causa probable | Acción |
|---|---|---|
| `Permission denied (publickey)` | Llave no instalada, `IdentityFile` incorrecto, o la IP de la estación no coincide con `from=` (frecuente con VPN) | Revisar la configuración SSH; confirmar con Infraestructura la IP que ve el servidor |
| Aviso de huella cambiada (`REMOTE HOST IDENTIFICATION HAS CHANGED`) | La llave del servidor no es la esperada | **Detenerse** y avisar a Seguridad. No aceptar la nueva huella |
| `sudo: a password is required` | La cuenta no está en el grupo `aircast-cap` o la regla sudo no está instalada | Infraestructura revisa el grupo y `/etc/sudoers.d/aircast-capture` |
| `sudo: sorry, you must have a tty to run sudo` | `requiretty` activo y falta la excepción | Verificar la línea `Defaults!AIRCAST_CAP !requiretty` |
| `perfil smpp deshabilitado` | `SMSC_FILTRO` vacío | Infraestructura lo completa tras confirmar el nodo SMPP (6.1, punto 7) |
| Wireshark o `capinfos` no reconocen el archivo (Windows) | Se redirigió la salida desde Windows PowerShell 5.1, que la convierte en texto UTF-16 | Repetir la captura desde `cmd.exe` |
| Archivo de 24 bytes o con 0 paquetes | No hubo tráfico que coincidiera: no se enviaron las peticiones dentro de la ventana, el perfil no es el adecuado o el tráfico no pasa por este nodo | Revisar las horas del paso 3 y el perfil; consultar a Infraestructura por balanceadores u otros nodos |
| Puerto 8082 sin decodificar | Wireshark no asocia ese puerto con HTTP | Analyze > Decode As… > TCP port 8082 → HTTP |
| `tcpdump` sigue activo tras Ctrl+C | Sin terminal remota, el proceso termina con el siguiente paquete o al vencer los minutos | Comprobar con `pgrep -a tcpdump`; si la ventana cierra, Infraestructura lo detiene |

## 12. Pendientes antes de la primera ventana

- Firma de Infraestructura, Seguridad y el responsable de la Fase 0 (control del documento).
- Plazo máximo de conservación de las capturas (`<N>` en C10).
- Si Seguridad exige bastión SSH o VPN, y la IP para `from=`.
- Cuentas personales de los analistas y alta de sus llaves.
- Nodo, puerto y uso de TLS del enlace SMPP de Aircast, para el perfil `smpp`.
- Línea y SIM de prueba (idealmente del lote NTE04570) y `campaignId` de prueba.
- Si la prueba se hace en producción con línea de prueba o en un entorno de laboratorio (pregunta 1 del brief acotado).

## Anexo A. Contrato de la API según la colección [POSTMAN]

`POST http://10.40.35.118:8082/aircast-slave-api-rest-server-war/api/pub/v1/ustk/UstkRequest`, cuerpo JSON. La colección no define cabeceras ni autenticación y no incluye ejemplos de respuesta: la captura debe confirmarlo.

| `type` | Campos comunes | Campos propios |
|---|---|---|
| `TextRequest` | `type`, `msisdn`, `requestId`, `campaignId`, `requestDeliveryReport`, `text1` | `tpda`, `mo` |
| `UssdRequest` | ídem | `ussdString` (por ejemplo `*511#`) |
| `UrlRequest` | ídem | `title2`, `url`, `flashSmsText`, `smsText`, `alwaysSendSmsText` |
| `CallRequest` | ídem | `title2`, `tpda` |
| `MenuRequest` | ídem | `title2`, `items[]` con `text`, `value` y, opcionales, `tpda` y `mo` |

Notas: `requestId` aparece como número y una vez como texto. Ninguna petición lleva la URL del callback, así que ese destino estaría configurado en Aircast [INFERENCE]. `tpda` sería la dirección de destino del SMS MO o el número a llamar, y `mo` el texto de ese SMS cuando el abonado acepta [INFERENCE]. Estos cinco `type` son el mínimo que debe reproducir la API unificada (ADR-1).
