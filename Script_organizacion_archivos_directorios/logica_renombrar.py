# logica_renombrar.py
"""
Funciones de lógica para renombrar archivos en masa.
"""
import os

def renombrar_archivos_en_masa(dir_base, nombre_base):
    archivos = []
    for root, _, files in os.walk(dir_base):
        for f in files:
            archivos.append(os.path.join(root, f))
    archivos.sort()
    contador = 1
    resultados = []
    for archivo in archivos:
        dir_actual = os.path.dirname(archivo)
        _, ext = os.path.splitext(archivo)
        nuevo_nombre = f"{nombre_base}{contador}{ext}"
        nuevo_path = os.path.join(dir_actual, nuevo_nombre)
        while os.path.exists(nuevo_path):
            contador += 1
            nuevo_nombre = f"{nombre_base}{contador}{ext}"
            nuevo_path = os.path.join(dir_actual, nuevo_nombre)
        try:
            os.rename(archivo, nuevo_path)
            resultados.append((archivo, nuevo_path))
        except Exception as e:
            resultados.append((archivo, None, str(e)))
            continue
        contador += 1
    return resultados 