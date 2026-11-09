---
title: "Brief acotado: Fase 0 de la Nuevatel SAT Platform"
status: draft
created: 2026-11-04
updated: 2026-11-04
---

# Brief acotado: Fase 0 de la Nuevatel SAT Platform

> Para discutir con el cliente el alcance de la Fase 0 (diagnóstico y pruebas piloto), con la dirección y los responsables técnicos de Nuevatel/VIVA [ASSUMPTION]. Resume esa fase del brief completo (`brief-sat-push-2026-10-22`, versión del 2026-10-30); OQ-n y Rn remiten a sus preguntas abiertas y riesgos. Sin llaves ni números de abonados. **Nada se ha validado todavía en una SIM real.** Fuentes: **[DOC]** documento; **[POSTMAN]** colección de la API de Aircast; **[INFERENCE]** inferencia sin probar; **[ASSUMPTION]** supuesto a confirmar.

## Resumen ejecutivo

Nuevatel (VIVA) administra hoy sus SIM a distancia a través de Aircast y Sleepy (ambos de Mobiera) y de los fabricantes de SIM. El proyecto propone internalizar esa capacidad. Antes de construir nada, la **Fase 0** determina con evidencia si es viable con las SIM y los contratos que Nuevatel tiene.

No construye la plataforma. Observa qué envía realmente Aircast (captura de tráfico acotada), prueba en laboratorio una SIM del lote NTE04570, mide cuántas SIM de la base son alcanzables y reúne las decisiones y accesos que el proyecto no puede tomar solo. Termina en un **punto de decisión (gate)** para pasar a las Fases 3 y 4; las Fases 1 y 2 conservan valor aunque el gate falle y pueden empezar ya.

Cuatro condiciones deciden la viabilidad: validación en laboratorio por familia de SIM, documentación completa del fabricante, una decisión sobre Sleepy y cobertura de llaves en la base activa. Hoy **ninguna está cerrada**, y la cobertura de llaves es el mayor riesgo: solo el lote NTE04570 (10.000 SIM) tiene archivos de salida en mano, sin validez probada [DOC].

**Se pide al cliente** acordar este alcance, nombrar al dueño de negocio y a quienes aprueban el gate, autorizar la captura en líneas de prueba y facilitar los accesos y SIM de prueba.

## Alcance: las dos pruebas piloto

### Prueba 1. Captura acotada del tráfico de Aircast

**Qué se hace.** Desde una línea de prueba se envía una petición de cada tipo a la API de Aircast (texto, menú, URL, llamada y USSD) y se captura el tráfico de la API REST, que va por HTTP sin TLS [POSTMAN], y el del enlace SMPP hacia el SMSC si sale del mismo servidor. Según lo acordado con Infraestructura y Seguridad, la captura es remota: se hace desde la estación Windows o macOS del analista, por SSH, con un script fijo en el servidor y sin guardar nada en su disco. El análisis no usa llaves; el procedimiento formal y las herramientas están en el addendum D.

**Qué responde.**

- El contrato real de la API, con campos y respuestas de los cinco tipos. Es la base de la API de envío unificada, compatible con Aircast.
- Qué aplicación de la SIM (TAR) recibe cada tipo de petición y con qué nivel de seguridad (SPI), incluida la exposición de Sleepy y de S@T a push sin protección (R11, OQ-27).
- Si el contador de la tarjeta es visible y cómo avanza entre envíos consecutivos (OQ-4, OQ-33).

El addendum B detalla el resto: SMS por petición, quién llama a la API y ruta hacia el SMSC.

**Límites y condiciones.** No entrega la llave de Sleepy ni mide la cobertura de llaves. Si el SMPP usa TLS o corre en otro nodo hace falta otro punto de captura; con el paquete cifrado, el contador no se ve. Solo líneas de prueba, con autorización escrita. Las capturas se guardan solo en la estación, con disco cifrado y fuera de carpetas sincronizadas, y se borran al terminar, porque el SMPP puede llevar usuario y contraseña en claro.

### Prueba 2. Laboratorio con una SIM del lote NTE04570

**Qué se hace.** Con una SIM de prueba y un lector: una lectura RFM (gestión remota de archivos) con prueba de recepción y un push a los TAR 505348 (PSH) y 534054 (S@T), con y sin seguridad. Usa solo las llaves de las SIM de prueba, bajo doble control y fuera del repositorio.

**Qué responde y límite.** Si la SIM acepta los comandos, con qué seguridad y si acepta un push sin protección; así se sabe si el push S@T (Fase 5) es viable en esa familia. Es una prueba de un solo lote y **no cumple** la condición de validación por familia de SIM. Antes hay que obtener los estándares 3GPP TS 23.048 y ETSI TS 102 225/226, que faltan en la carpeta del proyecto [DOC].

## El resto del diagnóstico

Además, la Fase 0 remedia los archivos de salida en texto plano (primera acción), mide la cobertura de llaves por lote, define la ruta del contador, revisa el contrato con Mobiera, el SMSC y el firewall, confirma la solicitud al fabricante y reúne lo necesario para decidir sobre Sleepy, el equipo, el HSM y el caso de negocio. El addendum E lo detalla con sus preguntas abiertas.

## Fuera de alcance

- Construir el motor OTA, el servicio de llaves o la API de envío unificada (Fases 1 a 4).
- Enviar a abonados reales, modificar SIM en producción o cambiar la configuración de Aircast.
- Rotar llaves, instalar un applet propio, migrar tráfico desde Aircast o incluir eSIM.

## Cómo sabremos que terminó

**Entregables de las pruebas piloto:** un informe de la captura (contrato de la API y tabla de TAR y SPI por tipo de petición), los resultados del laboratorio por TAR y la constancia de que las capturas se borraron.

**Gate de salida (propuesta del brief completo):** cobertura de llaves medida por lote; documentación del fabricante recibida; decisión sobre Sleepy; ruta del contador decidida (exportación contratada o salto superado); decisión de construir, contratar o aliarse; dueño y caso de negocio aprobados; y un plan alterno para las Fases 5 y 6. Sin ruta de contador, el motor sirve solo lotes nuevos; si el push S@T no se prueba en una familia, esa familia se queda en Aircast.

## Qué necesitamos del cliente

- **Gobierno:** dueño de negocio y aprobadores del gate (OQ-11).
- **Autorización y acceso:** permiso escrito para la captura remota sobre el servidor de la API de Aircast (10.40.35.118) y, si corresponde, sobre el nodo del enlace SMPP; acceso SSH desde la estación del analista y el script de captura instalado por Infraestructura.
- **Pruebas:** línea de prueba, SIM NTE04570, lector de tarjetas, un teléfono de prueba y un `campaignId` válido.
- **Accesos:** operador de Aircast, extracto directo del CRM y responsables de SMSC y firewall.
- **Legal:** contrato con Mobiera (vencido en julio de 2022 [DOC]) y requisitos de ATT (OQ-13).
- **Calendario y presupuesto:** no existen datos (OQ-12, OQ-14). La duración depende de autorizaciones y terceros más que del trabajo técnico [ASSUMPTION].

## Riesgos principales

- **Push sin protección alcanzable por terceros (R11).** Sleepy opera sin seguridad (MSL 0) y S@T podría compartir la exposición [INFERENCE]. Las pruebas pueden confirmarlo, así que sus resultados son confidenciales.
- **Autenticación de la API por confirmar.** La colección no muestra autenticación ni TLS en la API de Aircast [POSTMAN]; puede haber controles de red que no refleja. La captura lo aclara.

La base inalcanzable y los contadores bloqueados en Aircast (R1, R2) son criterios del gate. El addendum F los detalla, junto con los datos de abonados en la captura y el bloqueo de las Fases 5 y 6 por terceros (R13).

## Preguntas para decidir con el cliente

1. ¿Autoriza la captura en el servidor de producción con una línea de prueba, o prefiere un entorno de laboratorio?
2. ¿El piloto se limita al lote NTE04570 o incluye desde el inicio las familias Idemia y G+D? Un solo lote no basta para decidir por familia.
3. ¿Hasta dónde permite el contrato con Mobiera probar la exportación de contadores?
4. ¿Quién remedia los archivos en texto plano y para cuándo?
5. ¿Se aprueba lanzar ya las Fases 1 y 2, que no tienen bloqueo externo?
