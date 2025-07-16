import os
import json

def renombrar_archivos(archivos, nombre_base, directorio, callback_progreso=None):
    nombres_originales = {}
    total = len(archivos)
    for i, archivo in enumerate(archivos, start=1):
        ruta_original = os.path.join(directorio, archivo)
        extension = os.path.splitext(archivo)[1]
        nuevo_nombre = f"{nombre_base}_{i}{extension}"
        ruta_nueva = os.path.join(directorio, nuevo_nombre)
        os.rename(ruta_original, ruta_nueva)
        nombres_originales[nuevo_nombre] = archivo
        if callback_progreso:
            callback_progreso(i, total)
    # Guardar los nombres originales en un archivo json
    with open(os.path.join(directorio, "nombres_originales.json"), "w") as f:
        json.dump(nombres_originales, f)
    return nombres_originales

def restaurar_nombres(directorio):
    import os, json
    json_path = os.path.join(directorio, "nombres_originales.json")
    if not os.path.exists(json_path):
        return False, "No se encontró el archivo de nombres originales."
    with open(json_path, "r") as f:
        nombres_originales = json.load(f)
    errores = []
    restaurados = []
    for nuevo_nombre, original in nombres_originales.items():
        ruta_nueva = os.path.join(directorio, nuevo_nombre)
        ruta_original = os.path.join(directorio, original)
        if os.path.exists(ruta_nueva):
            try:
                if os.path.exists(ruta_original):
                    os.remove(ruta_original)
                os.rename(ruta_nueva, ruta_original)
                restaurados.append(original)
            except Exception as e:
                errores.append(f"No se pudo restaurar {nuevo_nombre} -> {original}: {e}")
    os.remove(json_path)
    if errores:
        return False, "Algunos archivos no se restauraron:\n" + "\n".join(errores)
    if not restaurados:
        return False, "No se restauró ningún archivo. ¿Quizá ya estaban restaurados?"
    return True, f"Nombres restaurados correctamente: {', '.join(restaurados)}" 