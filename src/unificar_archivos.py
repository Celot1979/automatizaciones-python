import os
import shutil
import json

def unificar_archivos(archivos_seleccionados, carpeta_destino, nombre_carpeta, nombre_base):
    # Crear la carpeta de unificación
    ruta_unificacion = os.path.join(carpeta_destino, nombre_carpeta)
    os.makedirs(ruta_unificacion, exist_ok=True)
    backup = []
    for i, (ruta_original, archivo) in enumerate(archivos_seleccionados, start=1):
        extension = os.path.splitext(archivo)[1]
        nuevo_nombre = f"{nombre_base}_{i}{extension}"
        ruta_nueva = os.path.join(ruta_unificacion, nuevo_nombre)
        origen_absoluto = os.path.join(ruta_original, archivo)
        # Mensaje de depuración
        print(f"Copiando: {origen_absoluto} -> {ruta_nueva}")
        if not os.path.isfile(origen_absoluto):
            raise FileNotFoundError(f"No se encontró el archivo: {origen_absoluto}")
        try:
            shutil.copy2(origen_absoluto, ruta_nueva)
        except Exception as e:
            raise RuntimeError(f"Error copiando {origen_absoluto} a {ruta_nueva}: {e}")
        backup.append({
            "origen": ruta_original,
            "archivo_original": archivo,
            "ruta_nueva": ruta_unificacion,
            "archivo_nuevo": nuevo_nombre
        })
    # Guardar backup en la carpeta de unificación
    with open(os.path.join(ruta_unificacion, "backup_unificacion.json"), "w") as f:
        json.dump(backup, f)
    return ruta_unificacion, backup

def rehacer_unificacion(ruta_unificacion):
    backup_path = os.path.join(ruta_unificacion, "backup_unificacion.json")
    if not os.path.exists(backup_path):
        return False, "No se encontró el backup para rehacer el proceso."
    with open(backup_path, "r") as f:
        backup = json.load(f)
    for item in backup:
        archivo_nuevo = os.path.join(item["ruta_nueva"], item["archivo_nuevo"])
        archivo_original = os.path.join(item["origen"], item["archivo_original"])
        if os.path.exists(archivo_nuevo):
            shutil.move(archivo_nuevo, archivo_original)
    # Borrar la carpeta de unificación
    try:
        os.remove(backup_path)
        os.rmdir(ruta_unificacion)
    except Exception:
        shutil.rmtree(ruta_unificacion, ignore_errors=True)
    return True, "Proceso de unificación deshecho y carpeta eliminada." 