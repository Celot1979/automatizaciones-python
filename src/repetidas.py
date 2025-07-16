import os
import json
import shutil
import re

# Expresión regular para detectar copias de Ubuntu
PATRON_COPIA_UBUNTU = re.compile(r"^(?P<base>.+?) ?\((copia|otra copia|\d+\.ª copia)\)(?P<ext>\.[^.]+)$", re.IGNORECASE)

def encontrar_duplicados_por_nombre(directorio):
    archivos_por_base = {}
    copias_detectadas = []
    for root, _, files in os.walk(directorio):
        for f in files:
            if f.lower().endswith((
                '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.heif')):
                ruta = os.path.join(root, f)
                # Detectar si es copia de Ubuntu
                m = PATRON_COPIA_UBUNTU.match(f)
                if m:
                    base = m.group('base') + m.group('ext')
                    archivos_por_base.setdefault(base, []).append((ruta, f, True))
                else:
                    archivos_por_base.setdefault(f, []).append((ruta, f, False))
    # Recopilar copias (dejando solo el original de cada base)
    for base, lista in archivos_por_base.items():
        # Separar originales y copias
        originales = [item for item in lista if not item[2]]
        copias = [item for item in lista if item[2]]
        # Si hay original, solo las copias van a backup
        if originales:
            copias_detectadas.extend([item[0] for item in copias])
        # Si no hay original, dejar solo una copia y el resto a backup
        elif len(lista) > 1:
            copias_detectadas.extend([item[0] for item in lista[1:]])
    return copias_detectadas

def mover_duplicados_a_backup(duplicados, directorio):
    backup_dir = os.path.join(directorio, "__backup_repetidas__")
    os.makedirs(backup_dir, exist_ok=True)
    registro = []
    for archivo in duplicados:
        nombre = os.path.basename(archivo)
        destino = os.path.join(backup_dir, nombre)
        # Evitar sobrescribir en backup
        i = 1
        base, ext = os.path.splitext(nombre)
        while os.path.exists(destino):
            destino = os.path.join(backup_dir, f"{base}_dup{i}{ext}")
            i += 1
        try:
            shutil.move(archivo, destino)
            registro.append({"origen": archivo, "backup": destino})
        except Exception as e:
            registro.append({"origen": archivo, "backup": None, "error": str(e)})
    # Guardar registro
    with open(os.path.join(backup_dir, "backup_repetidas.json"), "w") as f:
        json.dump(registro, f)
    return backup_dir, registro

def deshacer_borrado_repetidas(directorio):
    backup_dir = os.path.join(directorio, "__backup_repetidas__")
    backup_file = os.path.join(backup_dir, "backup_repetidas.json")
    if not os.path.exists(backup_file):
        return False, "No se encontró backup para deshacer."
    with open(backup_file, "r") as f:
        registro = json.load(f)
    errores = []
    for item in registro:
        if item.get("backup") and os.path.exists(item["backup"]):
            destino = item["origen"]
            try:
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                shutil.move(item["backup"], destino)
            except Exception as e:
                errores.append((item["backup"], str(e)))
    # Limpiar backup
    try:
        os.remove(backup_file)
        os.rmdir(backup_dir)
    except Exception:
        shutil.rmtree(backup_dir, ignore_errors=True)
    if errores:
        return False, f"Algunos archivos no se pudieron restaurar: {errores}"
    return True, "Archivos restaurados correctamente." 