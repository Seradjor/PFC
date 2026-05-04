#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import threading
import subprocess
import xmlrpc.client
import tkinter as tk
from tkinter import messagebox
from smartcard.System import readers
from flask import Flask, request, jsonify


# ============================================================
#  CONFIGURACIÓN GLOBAL
# ============================================================

writing_card = False  # Pausa el fichaje cuando se está grabando una tarjeta

# Odoo
ODOO_URL = "http://localhost:8069"
ODOO_DB = "time_tracking_db"
ODOO_USER = "nfc_reader"
ODOO_PASSWORD = "nfc_reader210526"

# NFC
CLASSIC_KEY_A = [0xFF] * 6
READ_BLOCK_16 = lambda block: [0xFF, 0xB0, 0x00, block, 0x10] # Lee 16 bytes del bloque indicado (MIFARE Classic).
LOAD_KEY = [0xFF, 0x82, 0x00, 0x00, 0x06] + CLASSIC_KEY_A # Carga en el lector la clave configurada.
AUTH_BLOCK = lambda block: [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, block, 0x60, 0x00] # Autentica el bloque con Key A previamente cargada.


# ============================================================
#  UTILIDADES
# ============================================================

# Muestra un popup modal en primer plano.
def popup(title, message):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    messagebox.showinfo(title, message)
    root.destroy()

# Arranca el servicio pcscd si no está activo.
def start_pcscd():
    try:
        subprocess.run(["sudo", "systemctl", "enable", "pcscd"], check=False)
        subprocess.run(["sudo", "systemctl", "start", "pcscd"], check=False)
        print("Servicio pcscd iniciado correctamente.")
    except Exception as e:
        print("No se pudo iniciar pcscd:", e)


# Devuelve el lector NFC disponible.
def get_reader():
    rlist = readers()
    if not rlist:
        return None
    return next((r for r in rlist if "ACR122U" in str(r)), rlist[0])


# Devuelve True si hay tarjeta presente.
def card_present(connection):
    try:
        connection.connect()
        return True
    except:
        return False


# Verifica si el estado SW1/SW2 devuelto por el lector indica éxito. El par 0x90/0x00 se interpreta como operación correcta.
def is_sw_success(sw1, sw2):
    return (sw1, sw2) == (0x90, 0x00)


# ============================================================
#  LECTURA NFC
# ============================================================

# Lee el bloque 4 de una tarjeta MIFARE Classic.
def read_block_4(connection):
    _, sw1, sw2 = connection.transmit(LOAD_KEY)
    if not is_sw_success(sw1, sw2):
        return None

    _, sw1, sw2 = connection.transmit(AUTH_BLOCK(4))
    if not is_sw_success(sw1, sw2):
        return None

    resp, sw1, sw2 = connection.transmit(READ_BLOCK_16(4))
    if not is_sw_success(sw1, sw2):
        return None

    return bytes(resp).decode('ascii', errors='ignore').rstrip('\x00')


# ============================================================
#  ESCRITURA NFC
# ============================================================

# Escribe el código en el bloque 4 de una tarjeta MIFARE Classic.
def write_to_card(connection, code):

    # Cargar clave A
    _, sw1, sw2 = connection.transmit(LOAD_KEY)
    if not is_sw_success(sw1, sw2):
        raise Exception("Error cargando clave A.")

    # Autenticar bloque 4
    _, sw1, sw2 = connection.transmit(AUTH_BLOCK(4))
    if not is_sw_success(sw1, sw2):
        raise Exception("Error autenticando bloque 4.")

    # Preparar datos (16 bytes)
    data_bytes = list(code.encode("ascii"))
    data_bytes += [0x00] * (16 - len(data_bytes))

    # Escribir bloque 4
    write_cmd = [0xFF, 0xD6, 0x00, 0x04, 0x10] + data_bytes
    _, sw1, sw2 = connection.transmit(write_cmd)

    if not is_sw_success(sw1, sw2):
        raise Exception("Error escribiendo en la tarjeta.")

    return True


# ============================================================
#  ODOO
# ============================================================

# Autenticación inicial con Odoo.
def odoo_connect():
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    return uid, models

UID, MODELS = odoo_connect()

# Envía el código leído a Odoo.
def register_new_record(id_time_tracking):
    try:
        return MODELS.execute_kw(
            ODOO_DB, UID, ODOO_PASSWORD,
            'time_tracking.record',
            'nfc_register',
            [id_time_tracking]
        )
    except Exception as e:
        print("Error llamando a Odoo:", e)
        return {
            'status': 'error_read',
            'title': 'Error lectura tarjeta',
            'message': 'Error de lectura de tarjeta.'
        }


# ============================================================
#  BUCLE DE FICHAJES
# ============================================================

# Bucle principal de lectura continua.
def records_loop():
    global writing_card

    reader = get_reader()
    if not reader:
        print("No se detectan lectores PC/SC.")
        return

    print("Lector detectado:", reader)
    print("Esperando tarjetas... Ctrl+C para salir.")

    while True:
        if writing_card:
            time.sleep(0.2)
            continue

        connection = reader.createConnection()

        if card_present(connection):
            try:
                id_time_tracking = read_block_4(connection)

                if not id_time_tracking:
                    popup("Fichajes empleado", "No se ha detectado ningún ID de empleado.")
                    while card_present(connection):
                        time.sleep(0.2)
                    continue

                print(f"Código leído: {id_time_tracking}")

                result = register_new_record(id_time_tracking)
                popup(result['title'], result['message'])

                while card_present(connection):
                    time.sleep(0.2)

            except Exception as e:
                print("Error durante lectura:", e)

            finally:
                try:
                    connection.disconnect()
                except:
                    pass

                print("Tarjeta retirada. Esperando nueva tarjeta...")

        time.sleep(0.2)


# ============================================================
#  SERVICIO FLASK (ESCRITURA)
# ============================================================

app = Flask(__name__)

# Endpoint para grabar tarjetas desde Odoo.
@app.post("/write_card")
def write_card():
    global writing_card
    data = request.get_json()
    code = data.get("code")

    try:
        writing_card = True

        reader = get_reader()
        if not reader:
            writing_card = False
            return jsonify({"status": "error", "message": "No se detectan lectores PC/SC."})

        connection = reader.createConnection()

        print("Esperando tarjeta para grabar...")
        while not card_present(connection):
            time.sleep(0.2)

        print("Tarjeta detectada. Grabando...")
        write_to_card(connection, code)

        while card_present(connection):
            time.sleep(0.2)

        print("Grabación completada.")
        return jsonify({"status": "ok"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

    finally:
        writing_card = False


def run_flask():
    app.run(host="0.0.0.0", port=5001)


# ============================================================
#  MAIN
# ============================================================

if __name__ == "__main__":
    try:
        start_pcscd()

        threading.Thread(target=run_flask, daemon=True).start()
        print("Servicio Flask NFC /write_card escuchando en puerto 5001.")

        records_loop()

    except KeyboardInterrupt:
        print("\nPrograma terminado.")

