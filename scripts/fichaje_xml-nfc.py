#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import threading
import subprocess
import xmlrpc.client

import tkinter as tk
from tkinter import messagebox

from smartcard.System import readers
from smartcard.Exceptions import CardConnectionException

from flask import Flask, request, jsonify
from write_nfc import write_to_card  # tu función ya existente

# ============================================================
#  VARIABLES GLOBALES
# ============================================================

grabando = False   # Pausa el fichaje cuando se está grabando una tarjeta


# ============================================================
#  POPUP PARA MENSAJES EMERGENTES
# ============================================================

def popup(title, message):
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    messagebox.showinfo(title, message)
    root.destroy()


# ============================================================
#  ARRANCAMOS SERVICIO pcscd (LECTOR NFC)
# ============================================================

def start_pcscd():
    try:
        subprocess.run(["sudo", "systemctl", "enable", "pcscd"], check=False)
        subprocess.run(["sudo", "systemctl", "start", "pcscd"], check=False)
        print("Servicio pcscd iniciado correctamente.")
    except Exception as e:
        print("No se pudo iniciar pcscd:", e)


# ============================================================
#  CONFIGURACIÓN ODOO (FICHAJES)
# ============================================================

ODOO_URL = "http://localhost:8069"
ODOO_DB = "time_tracking_db"
ODOO_USER = "nfc_reader"
ODOO_PASSWORD = "nfc_reader210526"

common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")


def fichar_en_odoo(barcode):
    try:
        return models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'time_tracking.record',
            'nfc_register',
            [barcode]
        )
    except Exception as e:
        print("Error llamando a Odoo:", e)
        return {
            'status': 'error_read',
            'title': 'Error lectura tarjeta',
            'message': 'Error de lectura de tarjeta.'
        }


# ============================================================
#  CONFIGURACIÓN NFC (LECTURA FICHAJES)
# ============================================================

CLASSIC_KEY_A = [0xFF] * 6

GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
READ_BLOCK_16 = lambda block: [0xFF, 0xB0, 0x00, block, 0x10]
LOAD_KEY = [0xFF, 0x82, 0x00, 0x00, 0x06] + CLASSIC_KEY_A
AUTH_BLOCK = lambda block: [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, block, 0x60, 0x00]


def is_sw_success(sw1, sw2):
    return (sw1, sw2) == (0x90, 0x00)


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


def card_present(conn):
    try:
        conn.connect()
        return True
    except:
        return False


# ============================================================
#  BUCLE DE FICHAJES (LECTURA CONTINUA)
# ============================================================

def fichaje_loop():
    global grabando

    rlist = readers()
    if not rlist:
        print("No se detectan lectores PC/SC.")
        return

    reader = next((r for r in rlist if "ACR122U" in str(r)), rlist[0])
    print("Lector detectado:", reader)
    print("Esperando tarjetas... Ctrl+C para salir.")

    while True:

        if grabando:
            time.sleep(0.2)
            continue

        connection = reader.createConnection()

        if card_present(connection):
            try:
                barcode = read_block_4(connection)
                if not barcode:
                    popup("Fichajes empleado", "Error de lectura de tarjeta.")

                    while card_present(connection):
                        time.sleep(0.2)
                    continue

                print(f"Código leído: {barcode}")

                result = fichar_en_odoo(barcode)
                popup(result['title'], result['message'])

                while card_present(connection):
                    time.sleep(0.2)

            except Exception as e:
                print("Error durante lectura:", e)

            finally:
                try:
                    connection.disconnect()
                    print("Tarjeta retirada. Esperando nueva tarjeta...")
                except:
                    pass

        time.sleep(0.2)


# ============================================================
#  SERVICIO FLASK (ESCRITURA DESDE ODOO)
# ============================================================

app = Flask(__name__)


@app.post("/write_card")
def write_card():
    global grabando
    data = request.get_json()
    code = data.get("code")

    try:
        grabando = True  # Pausar fichajes

        rlist = readers()
        if not rlist:
            grabando = False
            return jsonify({"status": "error", "message": "No se detectan lectores PC/SC."})

        reader = next((r for r in rlist if "ACR122U" in str(r)), rlist[0])
        connection = reader.createConnection()

        # Esperar tarjeta
        print("Esperando tarjeta para grabar...")
        while True:
            try:
                connection.connect()
                break
            except:
                time.sleep(0.2)

        print("Tarjeta detectada. Grabando...")
        write_to_card(code)

        # Esperar retirada
        while True:
            try:
                connection.connect()
                time.sleep(0.2)
            except:
                break

        grabando = False
        print("Grabación completada.")
        return jsonify({"status": "ok"})

    except Exception as e:
        grabando = False
        return jsonify({"status": "error", "message": str(e)})


def run_flask():
    app.run(host="0.0.0.0", port=5001)


# ============================================================
#  MAIN UNIFICADO
# ============================================================

if __name__ == "__main__":
    try:
        start_pcscd()

        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        print("Servicio Flask NFC /write_card escuchando en puerto 5001.")

        fichaje_loop()

    except KeyboardInterrupt:
        print("\nPrograma terminado.")

