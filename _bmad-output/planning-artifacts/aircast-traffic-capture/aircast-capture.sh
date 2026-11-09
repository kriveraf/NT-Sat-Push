#!/bin/bash
# aircast-capture: captura acotada del trafico de Aircast para la Fase 0.
#
# Se instala en el servidor 10.40.35.118 como /usr/local/sbin/aircast-capture,
# propietario root:root, permisos 0755, y se invoca solo a traves de sudo
# (ver aircast-capture.sudoers). Escribe la captura en formato pcap por la
# salida estandar: el analista la recibe por SSH y NADA se guarda en el disco
# del servidor.
#
# El analista no puede cambiar el filtro ni las opciones de tcpdump: solo elige
# un perfil de la lista y una duracion de 1 a 120 minutos. Por eso no se concede
# "sudo tcpdump" generico (tcpdump -z permite ejecutar comandos como root).
#
# Uso:
#   aircast-capture check
#   aircast-capture <api|clientes|smpp> <minutos 1-120>

set -euo pipefail

# Ruta de tcpdump en este servidor (comprobar con: command -v tcpdump).
TCPDUMP=/usr/sbin/tcpdump

# Filtro del enlace SMPP. Infraestructura lo completa cuando confirme el nodo,
# la IP del SMSC y el puerto, por ejemplo: 'host 10.x.x.x and tcp port 2775'.
# Vacio = perfil smpp deshabilitado.
SMSC_FILTRO=''

USO="uso: aircast-capture check | aircast-capture <api|clientes|smpp> <minutos 1-120>"

# Se rechaza cualquier argumento adicional: nunca se pasa nada a tcpdump.
if (( $# > 2 )); then
  echo "$USO" >&2
  exit 2
fi

perfil="${1:-}"
minutos="${2:-}"

case "$perfil" in
  check)
    exec "$TCPDUMP" --version
    ;;
  api)
    filtro='tcp port 8082 or (host 10.45.56.53 and tcp port 8980)'
    ;;
  clientes)
    filtro='tcp dst port 8082 and tcp[tcpflags] == tcp-syn'
    ;;
  smpp)
    if [ -z "$SMSC_FILTRO" ]; then
      echo "perfil smpp deshabilitado: Infraestructura debe definir SMSC_FILTRO" >&2
      exit 2
    fi
    filtro="$SMSC_FILTRO"
    ;;
  *)
    echo "$USO" >&2
    exit 2
    ;;
esac

if ! [[ "$minutos" =~ ^[1-9][0-9]{0,2}$ ]] || (( minutos > 120 )); then
  echo "minutos: entero entre 1 y 120" >&2
  exit 2
fi

logger -t aircast-capture "inicio usuario=${SUDO_USER:-desconocido} perfil=$perfil minutos=$minutos"

# -i any: todas las interfaces; -n: sin resolucion de nombres; -s 0: paquete
# completo; -U: escribe paquete a paquete; -w -: pcap por la salida estandar.
exec timeout --signal=TERM "$(( minutos * 60 ))" "$TCPDUMP" -i any -n -s 0 -U -w - "$filtro"
