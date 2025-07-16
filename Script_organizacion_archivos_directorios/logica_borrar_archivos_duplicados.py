# logica_borrar_archivos_duplicados.py
"""
Funciones de lógica para detectar y borrar archivos duplicados según el patrón de nombres especificado.
Incluye función para deshacer el borrado.
"""
import os
import re
import shutil
import json

HISTORIAL_BORRADO = "_historial_borrado_duplicados.json"

def buscar_duplicados(directorios):
    """
    Busca archivos duplicados en los directorios dados según el patrón:
    original: nombre.ext
    copia: nombre copia.ext, nombre copia 2.ext, nombre 2.ext, ...
    Devuelve un diccionario: {archivo_original: [lista de copias]}
    """
    patron = re.compile(r"^(.*?)( copia(?: \d+)?| \d+)?(\.[^.]+)$", re.IGNORECASE)
    archivos_encontrados = {}
    for directorio in directorios:
        for root, _, files in os.walk(directorio):
            for f in files:
                m = patron.match(f)
                if m:
                    base = m.group(1)
                    sufijo = m.group(2)
                    ext = m.group(3)
                    clave = f"{base}{ext}"
                    if sufijo:
                        # Es copia
                        archivos_encontrados.setdefault(clave, []).append(os.path.join(root, f))
                    else:
                        # Es original
                        archivos_encontrados.setdefault(clave, [])
    # Solo dejar los que tienen copias
    return {k: v for k, v in archivos_encontrados.items() if v}

def borrar_archivos(archivos):
    """
    Borra los archivos dados en la lista.
    Guarda un historial para deshacer el borrado.
    Devuelve una lista de (archivo, True/False, error)
    """
    resultados = []
    borrados = []
    for archivo in archivos:
        try:
            # Guardar copia temporal para deshacer
            temp_dir = os.path.join(os.path.dirname(archivo), ".borrados_temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, os.path.basename(archivo))
            shutil.copy2(archivo, temp_path)
            os.remove(archivo)
            resultados.append((archivo, True, None))
            borrados.append((archivo, temp_path))
        except Exception as e:
            resultados.append((archivo, False, str(e)))
    # Guardar historial
    if borrados:
        historial_path = os.path.join(os.path.dirname(borrados[0][0]), HISTORIAL_BORRADO)
        with open(historial_path, "w", encoding="utf-8") as f:
            json.dump({"borrados": borrados}, f)
    return resultados

def deshacer_borrado_duplicados(directorio):
    """
    Restaura los archivos borrados en la última operación.
    """
    historial_path = os.path.join(directorio, HISTORIAL_BORRADO)
    if not os.path.exists(historial_path):
        return False, "No hay historial para deshacer."
    with open(historial_path, "r", encoding="utf-8") as f:
        datos = json.load(f)
    borrados = datos.get("borrados", [])
    errores = []
    for original, temp_path in borrados:
        try:
            shutil.move(temp_path, original)
        except Exception as e:
            errores.append((original, str(e)))
    # Limpiar
    try:
        os.remove(historial_path)
    except Exception:
        pass
    if errores:
        return False, f"Errores al restaurar: {errores}"
    return True, f"Se restauraron {len(borrados)} archivos borrados." 