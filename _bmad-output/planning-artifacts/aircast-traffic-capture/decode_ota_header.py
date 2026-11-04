#!/usr/bin/env python3
"""Decodifica la cabecera de seguridad de un paquete OTA (SMS-PP) a partir del
`short_message` de un `submit_sm` SMPP capturado.

Qué hace
  * Lee el mensaje en hexadecimal (uno o varios, o la columna `smpp.short_message`
    de un CSV de tshark, ver runbook seccion 6).
  * Muestra TAR, SPI, KIc, KID, y, si el paquete NO va cifrado, el contador (CNTR).
  * Para paquetes de respuesta (PoR, UDH IEI 0x71) muestra el codigo de estado.

Qué NO hace
  * No descifra nada ni verifica checksums: no usa ni necesita llaves.
  * No imprime el contenido de los datos asegurados salvo con --data.
  * Por defecto enmascara los ultimos 4 digitos del destino en el modo CSV.

Estado de validacion (leer antes de confiar en la salida)
  * La estructura y los bits se cruzaron con dos implementaciones abiertas
    (pycrate, TS102225.py; pySim, ota.py), que coinciden entre si.
    No se pudo leer el texto del estandar (ETSI TS 102 225 / 3GPP TS 23.048).
  * NO se ha probado con trafico real de Aircast. Las pruebas de --selftest usan
    paquetes sinteticos construidos con la misma lectura del estandar, asi que
    solo comprueban coherencia interna, no la realidad.
  * Marco asumido (transporte SMS-PP): UDH con IEI 0x70 (comando) o 0x71
    (respuesta), CPL de 2 octetos, CHL de 1 octeto, sin CPI ni CHI.
    Si CPL no coincide con el largo real, el script lo avisa en vez de fallar:
    es la senal de que el marco real es otro.

Uso (Windows; -I aisla el interprete, recomendado con datos capturados)
  py -3.14 -I decode_ota_header.py 02700000 1A 15 ...        (hex, con o sin espacios)
  py -3.14 -I decode_ota_header.py --csv submit_sm.csv [--out resumen.csv]
  py -3.14 -I decode_ota_header.py --selftest
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone

# --- Tablas ----------------------------------------------------------------

# TAR conocidos. Fuente: Brief, addendum A (perfil 15.03) y K/L. Solo son
# nombres de ayuda; el valor hexadecimal es el dato real.
TAR_NAMES = {
    "000000": "RAM",
    "B00001": "USIM_RFM",
    "B00010": "SIM_RFM",
    "534054": "S@T Browser (Service Engine): pull, administracion, push de alta prioridad",
    "505348": "S@T PUSH (Service Engine PUSH): push de baja prioridad",
    "B20100": "Admin Agent (SCP81)",
    "534C59": "Sleepy (Mobiera)",
}

INTEGRITY = {0: "sin RC/CC/DS", 1: "RC (CRC)", 2: "CC (checksum criptografico)", 3: "DS (firma digital)"}
COUNTER = {
    0: "sin contador",
    1: "contador presente, sin verificacion de repeticion",
    2: "la tarjeta acepta solo si el contador es MAYOR que el suyo",
    3: "la tarjeta acepta solo si el contador es EXACTAMENTE +1",
}
POR_REQ = {0: "sin PoR", 1: "PoR siempre", 2: "PoR solo si hay error", 3: "reservado"}

DES_MODES = {0: "DES-CBC", 1: "3DES-CBC (2 llaves)", 2: "3DES-CBC (3 llaves)", 3: "DES-ECB"}


def status_text(code: int) -> str:
    known = {
        0x00: "PoR OK",
        0x01: "RC/CC/DS fallo",
        0x02: "CNTR bajo (contador del comando por debajo del de la tarjeta)",
        0x03: "CNTR alto (contador del comando por encima de lo aceptable)",
        0x04: "CNTR bloqueado",
        0x05: "error de cifrado",
        0x06: "error de seguridad no identificado",
        0x07: "memoria insuficiente",
        0x08: "se necesita mas tiempo (llegara otra respuesta)",
        0x09: "TAR desconocido",
        0x0A: "nivel de seguridad insuficiente",
    }
    if code in known:
        return known[code]
    if code in (0x0B, 0x0C):
        return "reservado 3GPP (TS 31.115)"
    if 0xC0 <= code <= 0xFE:
        return "propietario"
    return "reservado"


class DecodeError(ValueError):
    pass


# --- Utilidades --------------------------------------------------------------

def clean_hex(text: str) -> bytes:
    t = (text or "").strip().strip('"').strip()
    if t[:2].lower() == "0x":
        t = t[2:]
    for ch in " :-\t\r\n":
        t = t.replace(ch, "")
    if not t:
        raise DecodeError("campo vacio")
    if len(t) % 2:
        raise DecodeError("hex de largo impar")
    try:
        return bytes.fromhex(t)
    except ValueError:
        raise DecodeError(
            "no es hexadecimal (el campo pudo salir como texto; "
            "revisa el nombre con: tshark -G fields | findstr smpp)"
        ) from None


def _be(b: bytes) -> int:
    return int.from_bytes(b, "big")


def parse_udh(data: bytes):
    """Devuelve (lista de (iei, valor), offset tras la UDH) o None si no parece UDH."""
    if len(data) < 3:
        return None
    udhl = data[0]
    if udhl == 0 or udhl + 1 > len(data):
        return None
    end = 1 + udhl
    pos = 1
    ies = []
    while pos < end:
        if pos + 2 > end:
            return None
        iei, iedl = data[pos], data[pos + 1]
        if pos + 2 + iedl > end:
            return None
        ies.append((iei, data[pos + 2:pos + 2 + iedl]))
        pos += 2 + iedl
    return ies, end


def decode_key_byte(b: int, role: str) -> str:
    """role: 'kic' | 'kid_cc' | 'kid_rc'. Nibble bajo = algoritmo; alto = n.º de llave."""
    low, key = b & 0x0F, b >> 4
    fam, mode = low & 3, (low >> 2) & 3
    if role == "kid_rc":
        if fam == 0:
            alg = "implicito"
        elif fam == 1:
            alg = {0: "CRC-16", 1: "CRC-32"}.get(mode, "CRC reservado")
        elif fam == 3:
            alg = "propietario"
        else:
            alg = "reservado"
        return f"{alg}, version de llave {key}"
    if fam == 0:
        alg = "implicito (lo conocen ambas partes)"
    elif fam == 1:
        alg = DES_MODES[mode]
    elif fam == 2:
        if mode == 0:
            alg = "AES-CBC" if role == "kic" else "AES-CMAC"
        else:
            alg = "AES (modo reservado)"
    else:
        alg = "propietario"
    return f"{alg}, llave n.º {key}"


# --- Decodificacion -------------------------------------------------------------

def decode_packet(data: bytes, force_no_udh: bool = False, want_data: bool = False) -> dict:
    r = {"kind": "?", "warnings": [], "total_len": len(data)}
    start = 0
    ies = []
    if not force_no_udh:
        u = parse_udh(data)
        if u is not None:
            ies, start = u
    r["udh_ieis"] = [f"{iei:02X}" for iei, _ in ies]

    frag = None
    for iei, val in ies:
        if iei == 0x00 and len(val) == 3:
            frag = (val[2], val[1])  # (seq, total)
        elif iei == 0x08 and len(val) == 4:
            frag = (val[3], val[2])
    r["frag"] = frag
    if frag and frag[0] != 1:
        r["kind"] = "FRAG"
        r["warnings"].append(
            f"fragmento {frag[0]} de {frag[1]}: la cabecera OTA esta solo en el fragmento 1"
        )
        return r

    has70 = any(iei == 0x70 for iei, _ in ies)
    has71 = any(iei == 0x71 for iei, _ in ies)
    if has70:
        r["kind"] = "CMD"
    elif has71:
        r["kind"] = "RSP"
    elif ies:
        r["kind"] = "OTRO"
        r["warnings"].append("la UDH no trae IEI 0x70 ni 0x71: no parece un paquete OTA de 23.048")
        return r
    else:
        r["kind"] = "CMD"
        r["warnings"].append("sin UDH: se asume que el dato empieza en CPL (si es una respuesta, usa el IEI 0x71)")
    partial = bool(frag)
    if partial:
        r["warnings"].append(f"fragmento 1 de {frag[1]}: el paquete esta incompleto")

    if r["kind"] == "CMD":
        _decode_command(data, start, partial, r, want_data)
    else:
        _decode_response(data, start, partial, r, want_data)
    return r


def _tar_info(tar: bytes) -> dict:
    h = tar.hex().upper()
    ascii_ = tar.decode("ascii") if all(0x20 <= c <= 0x7E for c in tar) else ""
    return {"tar": h, "tar_ascii": ascii_, "tar_name": TAR_NAMES.get(h, "")}


def _check_len(r: dict, field: str, declared: int, data: bytes, start: int, partial: bool) -> None:
    remaining = len(data) - (start + 2)
    ok = declared >= remaining if partial else declared == remaining
    r[f"{field.lower()}_ok"] = ok
    if not ok:
        r["warnings"].append(
            f"{field}={declared} no coincide con lo que queda del mensaje ({remaining} octetos): "
            "el marco real puede ser otro (CPI/CHI, otro transporte) o el mensaje esta truncado"
        )


def _decode_command(data: bytes, start: int, partial: bool, r: dict, want_data: bool) -> None:
    if len(data) < start + 3:
        raise DecodeError("demasiado corto para CPL + CHL")
    cpl = _be(data[start:start + 2])
    chl = data[start + 2]
    r["cpl"], r["chl"] = cpl, chl
    _check_len(r, "CPL", cpl, data, start, partial)
    if chl < 13:
        raise DecodeError(f"CHL={chl} menor que 13 (SPI+KIc+KID+TAR+CNTR+PCNTR): no es un paquete de comando")
    h0 = start + 3
    if len(data) < h0 + chl:
        raise DecodeError("el mensaje termina antes del final de la cabecera (segun CHL)")
    h = data[h0:h0 + chl]
    spi1, spi2, kic, kid = h[0], h[1], h[2], h[3]
    r.update(_tar_info(h[4:7]))

    integrity = spi1 & 0x03
    ciphered = bool(spi1 & 0x04)
    counter = (spi1 >> 3) & 0x03
    por_req = spi2 & 0x03
    por_int = (spi2 >> 2) & 0x03
    por_cipher = bool(spi2 & 0x10)
    por_submit = bool(spi2 & 0x20)
    if spi1 & 0xE0 or spi2 & 0xC0:
        r["warnings"].append("SPI con bits reservados activos: revisar el marco")

    r.update(
        spi=f"{spi1:02X}{spi2:02X}",
        integrity=integrity, integrity_txt=INTEGRITY[integrity],
        ciphered=ciphered, counter_mode=counter, counter_txt=COUNTER[counter],
        por_req=por_req, por_req_txt=POR_REQ[por_req],
        por_integrity=por_int, por_integrity_txt=INTEGRITY[por_int],
        por_ciphered=por_cipher, por_via="SMS-SUBMIT" if por_submit else "SMS-DELIVER-REPORT",
        kic=f"{kic:02X}", kid=f"{kid:02X}",
    )
    r["kic_txt"] = decode_key_byte(kic, "kic") if ciphered else "no aplica (SPI sin cifrado)"
    if integrity == 0:
        r["kid_txt"] = "no aplica (SPI sin RC/CC/DS)"
    elif integrity == 1:
        r["kid_txt"] = decode_key_byte(kid, "kid_rc")
    elif integrity == 2:
        r["kid_txt"] = decode_key_byte(kid, "kid_cc")
    else:
        r["kid_txt"] = "firma digital (no decodificado)"

    sig_len = chl - 13
    secured = data[h0 + chl:]
    r["sig_len"], r["data_len"] = sig_len, len(secured)
    if integrity == 0 and sig_len:
        r["warnings"].append(f"SPI sin RC/CC/DS pero la cabecera reserva {sig_len} octetos")
    if integrity != 0 and sig_len == 0:
        r["warnings"].append("SPI pide RC/CC/DS pero la cabecera no reserva octetos")

    if ciphered:
        r["cntr"] = None
        r["pcntr"] = None
    else:
        r["cntr"] = _be(h[7:12])
        r["pcntr"] = h[12]
        if want_data:
            r["data_hex"] = secured.hex().upper()


def _decode_response(data: bytes, start: int, partial: bool, r: dict, want_data: bool) -> None:
    if len(data) < start + 6:
        raise DecodeError("demasiado corto para RPL + RHL + TAR")
    rpl = _be(data[start:start + 2])
    rhl = data[start + 2]
    r["rpl"], r["rhl"] = rpl, rhl
    _check_len(r, "RPL", rpl, data, start, partial)
    r.update(_tar_info(data[start + 3:start + 6]))
    if rhl < 10:
        raise DecodeError(f"RHL={rhl} menor que 10 (TAR+CNTR+PCNTR+estado): no es un paquete de respuesta")
    h0 = start + 3
    if len(data) < h0 + rhl:
        raise DecodeError("el mensaje termina antes del final de la cabecera (segun RHL)")
    h = data[h0:h0 + rhl]
    r["cntr"] = _be(h[3:8])
    r["pcntr"] = h[8]
    r["status"] = h[9]
    r["status_txt"] = status_text(h[9])
    r["sig_len"] = rhl - 10
    r["data_len"] = len(data) - (h0 + rhl)
    r["warnings"].append(
        "CNTR y estado solo tienen sentido si el PoR no va cifrado (bit 5 del 2.º octeto del SPI del comando)"
    )
    if want_data:
        r["data_hex"] = data[h0 + rhl:].hex().upper()


# --- Presentacion -----------------------------------------------------------------

def format_detail(r: dict) -> str:
    L = [f"Tipo: {r['kind']}   (UDH IEI: {' '.join(r['udh_ieis']) or 'ninguna'}; {r['total_len']} octetos)"]
    if r["kind"] in ("FRAG", "OTRO"):
        L += [f"  aviso: {w}" for w in r["warnings"]]
        return "\n".join(L)
    if r["kind"] == "CMD":
        L.append(f"CPL: {r['cpl']}  {'(coincide)' if r['cpl_ok'] else '(NO coincide)'}    CHL: {r['chl']}  (RC/CC/DS: {r['sig_len']} octetos)")
        L.append(f"SPI: {r['spi']}")
        L.append(f"  integridad: {r['integrity_txt']}")
        L.append(f"  cifrado:    {'SI' if r['ciphered'] else 'no'}")
        L.append(f"  contador:   {r['counter_txt']}")
        L.append(f"  PoR:        {r['por_req_txt']}; integridad {r['por_integrity_txt']}; "
                 f"{'cifrado' if r['por_ciphered'] else 'sin cifrar'}; via {r['por_via']}")
        L.append(f"KIc: {r['kic']}  {r['kic_txt']}")
        L.append(f"KID: {r['kid']}  {r['kid_txt']}")
    else:
        L.append(f"RPL: {r['rpl']}  {'(coincide)' if r['rpl_ok'] else '(NO coincide)'}    RHL: {r['rhl']}  (RC/CC/DS: {r['sig_len']} octetos)")
    tar = f"TAR: {r['tar']}"
    if r["tar_ascii"]:
        tar += f' ("{r["tar_ascii"]}")'
    if r["tar_name"]:
        tar += f"  {r['tar_name']}"
    L.append(tar)
    if r["kind"] == "CMD" and r["ciphered"]:
        L.append("CNTR / PCNTR / RC-CC-DS / datos: CIFRADOS, no legibles sin la llave KIc")
    else:
        L.append(f"CNTR: {r['cntr']}   PCNTR: {r['pcntr']}")
        if r["kind"] == "RSP":
            L.append(f"Estado: {r['status']:02X}  {r['status_txt']}")
    L.append(f"Datos asegurados: {r['data_len']} octetos")
    if "data_hex" in r:
        L.append(f"  {r['data_hex']}")
    L += [f"aviso: {w}" for w in r["warnings"]]
    return "\n".join(L)


def mask_msisdn(s: str) -> str:
    s = (s or "").strip()
    if len(s) <= 4:
        return "****" if s else ""
    return s[:-4] + "****"


COLUMNS = ["fila", "hora_utc", "seq", "destino", "tipo", "tar", "aplicacion", "spi",
           "integridad", "cifrado", "modo_contador", "cntr", "estado", "avisos"]


def summary_row(r: dict, meta: dict) -> dict:
    row = dict(meta)
    row["tipo"] = r["kind"]
    row["tar"] = r.get("tar", "")
    row["aplicacion"] = r.get("tar_name", "").split(":")[0].split(" (")[0]
    if r["kind"] == "CMD":
        row["spi"] = r["spi"]
        row["integridad"] = r["integrity_txt"].split(" (")[0]
        row["cifrado"] = "si" if r["ciphered"] else "no"
        row["modo_contador"] = {0: "ninguno", 1: "sin verif.", 2: "mayor", 3: "+1"}[r["counter_mode"]]
        row["cntr"] = "" if r["cntr"] is None else r["cntr"]
    elif r["kind"] == "RSP":
        row["cntr"] = r["cntr"]
        row["estado"] = f"{r['status']:02X} {r['status_txt'].split(' (')[0]}"
    row["avisos"] = len(r["warnings"]) if r["kind"] != "RSP" else max(0, len(r["warnings"]) - 1)
    return row


def run_csv(path: str, args) -> int:
    rows = []
    groups = {}  # (destino, tar) -> [(hora, cntr)]
    with open(path, newline="", encoding="utf-8-sig") as f:
        rd = csv.DictReader(f)
        if rd.fieldnames is None or args.col_msg not in rd.fieldnames:
            print(f"error: el CSV no tiene la columna '{args.col_msg}'. Columnas: {rd.fieldnames}", file=sys.stderr)
            return 2
        for n, rec in enumerate(rd, start=2):
            dst = (rec.get(args.col_dst) or "").strip()
            ts = ""
            raw_ts = (rec.get(args.col_time) or "").strip()
            if raw_ts:
                try:
                    ts = datetime.fromtimestamp(float(raw_ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    ts = raw_ts
            meta = {c: "" for c in COLUMNS}
            meta.update(fila=n, hora_utc=ts, seq=(rec.get(args.col_seq) or "").strip(),
                        destino=dst if args.show_msisdn else mask_msisdn(dst))
            try:
                r = decode_packet(clean_hex(rec.get(args.col_msg, "")), args.no_udh)
                row = summary_row(r, meta)
                if r["kind"] == "CMD" and r.get("cntr") is not None:
                    groups.setdefault((dst, r["tar"]), []).append((ts, r["cntr"]))
            except DecodeError as e:
                meta.update(tipo="ERROR", estado=str(e))
                row = meta
            rows.append(row)

    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in rows)) if rows else len(c) for c in COLUMNS}
    line = lambda r: "  ".join(str(r.get(c, "")).ljust(widths[c]) for c in COLUMNS).rstrip()
    print(line({c: c for c in COLUMNS}))
    for r in rows:
        print(line(r))

    ok = [r for r in rows if r["tipo"] not in ("ERROR",)]
    print(f"\n{len(rows)} filas, {len(ok)} decodificadas, {len(rows) - len(ok)} con error.")
    if ok:
        by = {}
        for r in ok:
            k = (r["tipo"], r["tar"], r["spi"], r["cifrado"], r["modo_contador"])
            by[k] = by.get(k, 0) + 1
        print("\nCombinaciones vistas (tipo, TAR, SPI, cifrado, modo de contador): cantidad")
        for k, v in sorted(by.items(), key=lambda kv: -kv[1]):
            print(f"  {k}: {v}")
    seqs = {k: sorted(v) for k, v in groups.items() if len(v) >= 2}
    if seqs:
        print("\nContador visible por destino y TAR (orden por hora):")
        for (dst, tar), v in seqs.items():
            nums = [c for _, c in v]
            steps = sorted({b - a for a, b in zip(nums, nums[1:])})
            shown = dst if args.show_msisdn else mask_msisdn(dst)
            print(f"  {shown} TAR {tar}: {' -> '.join(map(str, nums))}   pasos: {steps}")
    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as g:
            w = csv.DictWriter(g, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(rows)
        print(f"\nResumen escrito en {args.out}. Guardalo fuera del repositorio y de OneDrive.")
    return 0


# --- Autoprueba (paquetes sinteticos) -------------------------------------------------

def _build_cmd(spi: str, kic: int, kid: int, tar: str, cntr: int, pcntr: int,
               rc: bytes, data: bytes, udh: bytes = b"\x02\x70\x00") -> bytes:
    body = (bytes([13 + len(rc)]) + bytes.fromhex(spi) + bytes([kic, kid]) + bytes.fromhex(tar)
            + cntr.to_bytes(5, "big") + bytes([pcntr]) + rc + data)
    return udh + len(body).to_bytes(2, "big") + body


def _build_rsp(tar: str, cntr: int, pcntr: int, status: int, rc: bytes, data: bytes) -> bytes:
    body = bytes([10 + len(rc)]) + bytes.fromhex(tar) + cntr.to_bytes(5, "big") + bytes([pcntr, status]) + rc + data
    return b"\x02\x71\x00" + len(body).to_bytes(2, "big") + body


def selftest() -> int:
    fails = []

    def check(name: str, cond: bool) -> None:
        if not cond:
            fails.append(name)

    cc = bytes([0xAA] * 8)
    t1 = _build_cmd("1200", 0x00, 0x15, "534054", 5, 0, cc, bytes.fromhex("A0A40000"))
    r = decode_packet(t1)
    check("t1 tipo", r["kind"] == "CMD")
    check("t1 cpl", r["cpl_ok"] is True)
    check("t1 integridad CC", r["integrity"] == 2)
    check("t1 sin cifrado", r["ciphered"] is False)
    check("t1 contador mayor", r["counter_mode"] == 2)
    check("t1 TAR", r["tar"] == "534054" and r["tar_ascii"] == "S@T")
    check("t1 CNTR", r["cntr"] == 5)
    check("t1 KID 3DES", "3DES-CBC (2 llaves)" in r["kid_txt"] and "llave n.º 1" in r["kid_txt"])
    check("t1 largos", r["sig_len"] == 8 and r["data_len"] == 4)
    check("t1 sin avisos", r["warnings"] == [])

    t2 = _build_cmd("1E09", 0x15, 0x15, "B00010", 123456, 0, cc, bytes(8))
    r = decode_packet(t2)
    check("t2 cifrado", r["ciphered"] is True and r["cntr"] is None)
    check("t2 contador +1", r["counter_mode"] == 3)
    check("t2 PoR", r["por_req"] == 1 and r["por_integrity"] == 2 and r["por_ciphered"] is False
          and r["por_via"] == "SMS-DELIVER-REPORT")
    check("t2 TAR nombre", "SIM_RFM" in r["tar_name"])
    check("t2 KIc 3DES", "3DES-CBC (2 llaves)" in r["kic_txt"])

    t3 = _build_cmd("0000", 0, 0, "534C59", 0, 0, b"", bytes.fromhex("0102030405"))
    r = decode_packet(t3)
    check("t3 sin seguridad", r["integrity"] == 0 and r["counter_mode"] == 0 and r["sig_len"] == 0)
    check("t3 TAR SLY", r["tar_ascii"] == "SLY" and "Sleepy" in r["tar_name"])
    check("t3 sin avisos", r["warnings"] == [])

    t4 = _build_rsp("B00010", 7, 0, 0x02, cc, bytes.fromhex("0000"))
    r = decode_packet(t4)
    check("t4 respuesta", r["kind"] == "RSP" and r["status"] == 2 and "CNTR bajo" in r["status_txt"])
    check("t4 cpl", r["rpl_ok"] is True and r["cntr"] == 7)

    bad = bytearray(t1)
    bad[4] += 1  # CPL + 1
    r = decode_packet(bytes(bad))
    check("t5 CPL distinto avisa", r["cpl_ok"] is False and r["warnings"])

    frag = bytes.fromhex("050003AB0302") + b"\x00\x01\x02"
    r = decode_packet(frag)
    check("t6 fragmento 2", r["kind"] == "FRAG")

    r = decode_packet(t1[3:])
    check("t7 sin UDH", r["kind"] == "CMD" and r["tar"] == "534054" and r["warnings"])

    check("t8 hex limpio", clean_hex("0x1A:2B 3c") == bytes([0x1A, 0x2B, 0x3C]))
    for bad_hex in ("", "ABC", "zz"):
        try:
            clean_hex(bad_hex)
            check(f"t8 error {bad_hex!r}", False)
        except DecodeError:
            pass

    check("t9 mascara", mask_msisdn("59100000001") == "5910000****" and mask_msisdn("123") == "****")

    if fails:
        print("FALLAN:", ", ".join(fails))
        return 1
    print("autoprueba OK (paquetes sinteticos: comprueba coherencia interna, no trafico real)")
    return 0


# --- main ------------------------------------------------------------------------

def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    ap = argparse.ArgumentParser(description="Decodifica la cabecera de seguridad OTA de un short_message SMPP.")
    ap.add_argument("hex", nargs="*", help="mensaje(s) en hexadecimal")
    ap.add_argument("--csv", help="CSV de tshark (runbook seccion 6)")
    ap.add_argument("--col-msg", default="smpp.short_message")
    ap.add_argument("--col-time", default="frame.time_epoch")
    ap.add_argument("--col-dst", default="smpp.destination_addr")
    ap.add_argument("--col-seq", default="smpp.sequence_number")
    ap.add_argument("--no-udh", action="store_true", help="el dato no lleva UDH: empieza en CPL")
    ap.add_argument("--data", action="store_true", help="imprimir tambien los datos asegurados (si no van cifrados)")
    ap.add_argument("--show-msisdn", action="store_true", help="no enmascarar el destino (modo CSV)")
    ap.add_argument("--out", help="escribir el resumen en CSV (modo CSV)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if args.csv:
        return run_csv(args.csv, args)
    if not args.hex:
        ap.print_help()
        return 2
    # Varios argumentos sueltos se unen: permite pegar el hex con espacios sin comillas.
    items = [" ".join(args.hex)]
    rc = 0
    for it in items:
        try:
            print(format_detail(decode_packet(clean_hex(it), args.no_udh, args.data)))
        except DecodeError as e:
            print(f"error: {e}", file=sys.stderr)
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
