#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import xmlrpc.client
import subprocess
import tkinter as tk
from tkinter import messagebox
from smartcard.System import readers

# ============================================================
#  POPUP PARA MENSAJES EMERGENTES
# ============================================================
def popup(title, message):
    root = tk.Tk()
    root.withdraw()  # Oculta la ventana principal
    root.attributes('-topmost', True)  # Para que aparezca delante.
    messagebox.showinfo(title, message)
    root.destroy()


# ============================================================
#  ARRANCAMOS LECTOR NFC
# ============================================================
try:
    subprocess.run(["sudo", "systemctl", "enable", "pcscd"], check=False)
    subprocess.run(["sudo", "systemctl", "start", "pcscd"], check=False)
    print("Servicio pcscd iniciado correctamente.")
except Exception as e:
    print("No se pudo iniciar pcscd:", e)

# ============================================================
#  CONFIGURACIÓN ODOO
# ============================================================

ODOO_URL = "http://localhost:8069"
ODOO_DB = "time_tracking_db"
ODOO_USER = "nfc_reader"
ODOO_PASSWORD = "nfc_reader210526"

# Autenticación XML-RPC
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common") # Conecta al servicio de autenticación.
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {}) # Inicia sesión en Odoo.
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object") # Permite llamar métodos de modelos Odoo.

def fichar_en_odoo(barcode):
    """
    Llama al método nfc_register del modelo time_tracking.record.
    Siempre devuelve un diccionario con:
    - status
    - title
    - message
    """
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
#  CONFIGURACIÓN NFC
# ============================================================

CLASSIC_KEY_A = [0xFF] * 6  # Clave por defecto FF FF FF FF FF FF. Se puede cambiar.

# APDUs (Application Protocol Data Unit) comunes
GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]  # Solicita al lector el UID de la tarjeta presente.
READ_BLOCK_16 = lambda block: [0xFF, 0xB0, 0x00, block, 0x10]  # Lee 16 bytes del bloque indicado (MIFARE Classic).
LOAD_KEY = [0xFF, 0x82, 0x00, 0x00, 0x06] + CLASSIC_KEY_A      # Carga en el lector la clave configurada.
AUTH_BLOCK = lambda block: [0xFF, 0x86, 0x00, 0x00, 0x05, 0x01, 0x00, block, 0x60, 0x00]  # Autentica el bloque con Key A previamente cargada.

# Verifica si el estado SW1/SW2 devuelto por el lector indica éxito. El par 0x90/0x00 se interpreta como operación correcta.
def is_sw_success(sw1, sw2):

    return (sw1, sw2) == (0x90, 0x00)

# Lee el bloque 4 de una MIFARE Classic. Devuelve el texto ASCII (barcode) o None si falla.
def read_block_4(connection):

    # Carga la clave
    _, sw1, sw2 = connection.transmit(LOAD_KEY)
    if not is_sw_success(sw1, sw2):
        return None

    # Autentica el bloque 4
    _, sw1, sw2 = connection.transmit(AUTH_BLOCK(4))
    if not is_sw_success(sw1, sw2):
        return None

    # Lee el bloque 4
    resp, sw1, sw2 = connection.transmit(READ_BLOCK_16(4))
    if not is_sw_success(sw1, sw2):
        return None

    # Convierte los 16 bytes a ASCII ignorando errores y elimina relleno nulo del final con rstrip('\x00').
    texto = bytes(resp).decode('ascii', errors='ignore').rstrip('\x00')
    return texto

# Comprueba si hay una tarjeta en el lector.
def card_present(conn):
    try:
        conn.connect()
        return True
    except:
        return False

# ============================================================
#  PROGRAMA PRINCIPAL
# ============================================================

def main():
    # Obtiene la lista de lectores PC/SC con readers(). Si no hay, informa y termina.
    rlist = readers()
    if not rlist:
        print("No se detectan lectores PC/SC.")
        return

    # Selecciona lector: busca ACR122U, si no lo encuentra usa el primero.
    reader = next((r for r in rlist if "ACR122U" in str(r)), rlist[0])
    print("Lector detectado:", reader)
    print("Esperando tarjetas... Ctrl+C para salir.")

    connection = reader.createConnection()

    while True:
        # Si card_present(reader) es True y antes era False, la marca como detectada, crea una conexión y entra en el flujo de lectura.
        if card_present(connection):
                

            try:

                # Leemos bloque 4 (barcode)
                barcode = read_block_4(connection)
                if not barcode:
                    popup("Fichajes empleado", "Error de lectura de tarjeta.")
                    
                    while card_present(connection):
                        time.sleep(0.2)

                    continue

                print(f"Código leído: {barcode}")

                # Enviar a Odoo
                result = fichar_en_odoo(barcode)

                # Mostrar wireframe
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

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nPrograma terminado.")

