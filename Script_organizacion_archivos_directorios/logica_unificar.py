# logica_unificar.py
"""
Funciones de lógica para unificar archivos seleccionados en un directorio destino.
Incluye soporte para deshacer la última operación.
"""
import os
import shutil
import datetime
import json

HISTORIAL_UNIFICACION = "_historial_unificacion.json"

def _expandir_archivos_y_directorios(rutas):
    """
    Dada una lista de rutas (archivos y/o carpetas), devuelve una lista de todos los archivos.
    """
    archivos = []
    for ruta in rutas:
        if os.path.isfile(ruta):
            archivos.append(ruta)
        elif os.path.isdir(ruta):
            for root, _, files in os.walk(ruta):
                for f in files:
                    archivos.append(os.path.join(root, f))
    return archivos

def unificar_archivos(rutas_seleccionadas, destino, nombre_base):
    """
    Unifica archivos y/o directorios en la carpeta destino, renombrando con nombre_base.
    Guarda un historial para poder deshacer la operación.
    """
    if not os.path.exists(destino):
        os.makedirs(destino)
    archivos = _expandir_archivos_y_directorios(rutas_seleccionadas)
    contador = 1
    movimientos = []
    archivos_copiados = []
    ruta_log = os.path.join(destino, "registro_movimientos.txt")
    base_folder = os.path.basename(destino.rstrip(os.sep))
    for archivo in archivos:
        nombre_original = os.path.basename(archivo)
        _, ext = os.path.splitext(archivo)
        nuevo_nombre = f"{nombre_base}{contador}{ext}"
        nuevo_path = os.path.join(destino, nuevo_nombre)
        ruta_relativa = f"{base_folder}/{nuevo_nombre}"
        while os.path.exists(nuevo_path):
            contador += 1
            nuevo_nombre = f"{nombre_base}{contador}{ext}"
            nuevo_path = os.path.join(destino, nuevo_nombre)
            ruta_relativa = f"{base_folder}/{nuevo_nombre}"
        try:
            shutil.copy2(archivo, nuevo_path)
            movimientos.append([
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                nombre_original,
                ruta_relativa
            ])
            archivos_copiados.append(nuevo_path)
        except Exception as e:
            movimientos.append([
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                nombre_original,
                f"ERROR: {e}"
            ])
            continue
        contador += 1
    # Guardar historial para deshacer
    historial_path = os.path.join(destino, HISTORIAL_UNIFICACION)
    with open(historial_path, "w", encoding="utf-8") as f:
        json.dump({"archivos": archivos_copiados}, f)
    return movimientos

def deshacer_ultima_unificacion(destino):
    """
    Borra los archivos copiados en la última operación de unificación.
    """
    historial_path = os.path.join(destino, HISTORIAL_UNIFICACION)
    if not os.path.exists(historial_path):
        return False, "No hay historial para deshacer."
    with open(historial_path, "r", encoding="utf-8") as f:
        datos = json.load(f)
    archivos = datos.get("archivos", [])
    errores = []
    for archivo in archivos:
        try:
            if os.path.exists(archivo):
                os.remove(archivo)
        except Exception as e:
            errores.append((archivo, str(e)))
    os.remove(historial_path)
    if errores:
        return False, f"Errores al borrar: {errores}"
    return True, f"Se deshicieron {len(archivos)} archivos copiados." 