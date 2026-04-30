#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from smartcard.System import readers
from smartcard.Exceptions import CardConnectionException
from smartcard.util import toHexString

# CONFIGURACIÓN
CLASSIC_KEY_A = [0xFF] * 6   # Clave por defecto FF FF FF FF FF FF (configurable).

# APDUs comunes para MIFARE Classic
GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]  # Comando para leer UID.
READ_BLOCK_16 = lambda block: [0xFF, 0xB0, 0x00, block, 0x10]  # Leer 16 bytes de un bloque.
LOAD_KEY = [0xFF, 0x82, 0x00, 0x00, 0x06] + CLASSIC_KEY_A      # Cargar clave A en el lector.
AUTH_BLOCK = lambda block: [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, block, 0x60, 0x00]  # Autenticar bloque.
WRITE_CLASSIC_16 = lambda block, data16: [0xFF, 0xD6, 0x00, block, 0x10] + data16  # Escribir 16 bytes en bloque.

# Validar si la respuesta APDU fue exitosa (SW1 SW2 = 0x90 0x00).
def is_sw_success(sw1, sw2):
    return (sw1, sw2) == (0x90, 0x00)

# Clasificar tarjeta Classic (la utilizada por nosotros).
def classify_tag(connection):
    try:
        # Cargar clave por defecto.
        _, sw1, sw2 = connection.transmit(LOAD_KEY)  # Envía LOAD_KEY; si no éxito, 'unknown'.
        if not is_sw_success(sw1, sw2):
            return 'unknown'
        # Autenticar bloque 4 con Key A.
        _, sw1, sw2 = connection.transmit(AUTH_BLOCK(4))
        if not is_sw_success(sw1, sw2):  # Si falla, 'unknown'.
            return 'unknown'
        # Leer bloque 4 esperando 16 bytes.
        resp, sw1, sw2 = connection.transmit(READ_BLOCK_16(4))
        if is_sw_success(sw1, sw2) and len(resp) == 16:  # Si éxito y longitud 16, 'classic'.
            return 'classic'
    except Exception:
        pass
    
    # La tarjeta no pertenece a Classic o no se pudo autenticar.
    return 'unknown'

# Escribir un string en un bloque de 16 bytes de una MIFARE Classic y verificar.
def write_code_classic(connection, code_str, block=4):
    if len(code_str) > 16:
        raise ValueError("El texto excede 16 caracteres para Classic.")  # Validación de longitud.
    data16 = [ord(c) for c in code_str.ljust(16, '\x00')]  # Rellena el string a 16 caracteres con \x00 y convierte a lista de códigos ASCII (data16).
    
    # Envía LOAD_KEY; si no éxito, lanza RuntimeError.
    _, sw1, sw2 = connection.transmit(LOAD_KEY)
    if not is_sw_success(sw1, sw2):
        raise RuntimeError(f"LOAD_KEY fallo: SW1={hex(sw1)}, SW2={hex(sw2)}")

    # Envía AUTH_BLOCK(block) con Key A; si falla, lanza error.
    _, sw1, sw2 = connection.transmit(AUTH_BLOCK(block))
    if not is_sw_success(sw1, sw2):
        raise RuntimeError(f"AUTH fallo en bloque {block}: SW1={hex(sw1)}, SW2={hex(sw2)}")

    # Envía WRITE_CLASSIC_16(block, data16); si falla, error.
    _, sw1, sw2 = connection.transmit(WRITE_CLASSIC_16(block, data16))
    if not is_sw_success(sw1, sw2):
        raise RuntimeError(f"WRITE fallo en bloque {block}: SW1={hex(sw1)}, SW2={hex(sw2)}")

    # Lee el mismo bloque con READ_BLOCK_16(block); si éxito, imprime hex y ascii.
    resp, sw1, sw2 = connection.transmit(READ_BLOCK_16(block))
    if not is_sw_success(sw1, sw2):
        raise RuntimeError(f"READ verificación fallo: SW1={hex(sw1)}, SW2={hex(sw2)}")
    print("Classic leído (hex):", toHexString(resp))
    try:  # El ascii se decodifica con utf-8 ignorando errores y se hace strip('\x00') para limpiar el relleno.
        print("Classic leído (ascii):", bytes(resp).decode('utf-8', errors='ignore').strip('\x00'))
    except Exception:
        pass

# Detectar lector, conectar, leer UID, escribir y verificar, y desconectar limpiamente.
def write_to_card(code):
    
    # Detecta lectores: Usa smartcard.System.readers(). Si no hay, informa y sale.
    rlist = readers()
    if not rlist:
        raise RuntimeError("No se detectan lectores PC/SC.")
        
    # Selecciona lector: busca ACR122U, si no lo encuentra usa el primero.
    reader = next((r for r in rlist if "ACR122U" in str(r)), rlist[0])
    print("Lector detectado:", reader)

    # Crea connection y llama a connect(). Si no hay tarjeta o falla, informa y sale.
    connection = reader.createConnection()
    try:
        connection.connect()
    except CardConnectionException:
        raise RuntimeError("No hay tarjeta presente o no se pudo conectar.")

    # Intenta GET_UID. Si éxito, imprime el UID en hex; si no, loguea fallo.
    try:
        uid, sw1, sw2 = connection.transmit(GET_UID)
        if is_sw_success(sw1, sw2):
            print("UID:", toHexString(uid))
    except Exception as e:
        print("Error leyendo UID:", e)

    # Llama a classify_tag(connection) y muestra el tipo deducido.
    tag_type = classify_tag(connection)
    print("Tipo deducido:", tag_type)

    # Escritura del código nuevo de tarjeta.
    if tag_type != 'classic':
        raise RuntimeError("La tarjeta no es MIFARE Classic o no se pudo autenticar.")

    # Escribir código
    write_code_classic(connection, code_str=code, block=4)

    # Desconexión reforzada. Intenta disconnect() y borra la conexión para liberar recursos del lector.
    try:
        connection.disconnect()
        del connection
    except Exception:
        pass
        
    return True


