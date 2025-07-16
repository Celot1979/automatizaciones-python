# logica_organizar.py
"""
Funciones de lógica para organizar archivos.
"""
import os
import shutil
import datetime
import getpass
import re

def obtener_nombre_disponible(carpeta_destino, nombre_archivo):
    base, ext = os.path.splitext(nombre_archivo)
    destino = os.path.join(carpeta_destino, nombre_archivo)
    i = 1
    while os.path.exists(destino):
        nuevo_nombre = f"{base}_({i}){ext}"
        destino = os.path.join(carpeta_destino, nuevo_nombre)
        i += 1
    return destino

def obtener_fecha_archivo(ruta_archivo):
    try:
        timestamp = os.path.getctime(ruta_archivo)
    except Exception:
        timestamp = os.path.getmtime(ruta_archivo)
    return datetime.datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y')

def escribir_registro_tabla(ruta_log, movimientos):
    encabezados = ["Fecha", "Nombre", "Ruta destino"]
    cols = list(zip(*([encabezados] + movimientos)))
    anchos = [max(len(str(item)) for item in col) for col in cols]
    def fila_tabla(fila):
        return "* " + " * ".join(str(item).ljust(anchos[i]) for i, item in enumerate(fila)) + " *"
    separador = "*" + "*".join(["".ljust(anchos[i]+2, "*") for i in range(len(anchos))]) + "*"
    lineas = [separador, fila_tabla(encabezados), separador]
    for mov in movimientos:
        lineas.append(fila_tabla(mov))
    lineas.append(separador)
    with open(ruta_log, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas) + "\n") 