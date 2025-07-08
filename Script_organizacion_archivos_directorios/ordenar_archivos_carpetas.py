import os
import shutil

# Ruta donde están los archivos a ordenar
ruta = "/Users/danielgil/Documents/Venta del ordenador"

# Diccionario que mapea extensiones a carpetas
extensiones_a_carpetas = {
    "Imágenes": [".jpg", ".jpeg", ".png", ".bmp", ".heif"],
    "PDFs": [".pdf"],
    "Vídeos": [".mp4", ".mov", ".avi"],
    "Documentos": [".doc", ".xls", ".xlsx"],
    "Documentos_txt": [".txt"],
    "Documentos_docx": [".docx"]
}

# Crear carpetas en destino si no existen
for carpeta in extensiones_a_carpetas.keys():
    ruta_carpeta = os.path.join(ruta, carpeta)
    if not os.path.exists(ruta_carpeta):
        os.makedirs(ruta_carpeta)

# Crear carpeta para archivos no clasificados
carpeta_no_clasificados = "No clasificados"
ruta_no_clasificados = os.path.join(ruta, carpeta_no_clasificados)
if not os.path.exists(ruta_no_clasificados):
    os.makedirs(ruta_no_clasificados)

# Recorrer archivos en la ruta
for archivo in os.listdir(ruta):
    ruta_archivo = os.path.join(ruta, archivo)
    # Ignorar carpetas
    if os.path.isdir(ruta_archivo):
        continue
    # Obtener extensión en minúsculas
    _, extension = os.path.splitext(archivo)
    extension = extension.lower()
    movido = False
    for carpeta, extensiones in extensiones_a_carpetas.items():
        if extension in extensiones:
            destino = os.path.join(ruta, carpeta, archivo)
            # Manejar conflicto de nombres
            if os.path.exists(destino):
                base, ext = os.path.splitext(archivo)
                i = 1
                while True:
                    nuevo_nombre = f"{base}_({i}){ext}"
                    destino = os.path.join(ruta, carpeta, nuevo_nombre)
                    if not os.path.exists(destino):
                        break
                    i += 1
            try:
                shutil.move(ruta_archivo, destino)
            except Exception as e:
                print(f"Error al mover {archivo}: {e}")
            movido = True
            break
    if not movido:
        # Mover a 'No clasificados'
        destino = os.path.join(ruta_no_clasificados, archivo)
        if os.path.exists(destino):
            base, ext = os.path.splitext(archivo)
            i = 1
            while True:
                nuevo_nombre = f"{base}_({i}){ext}"
                destino = os.path.join(ruta_no_clasificados, nuevo_nombre)
                if not os.path.exists(destino):
                    break
                i += 1
        try:
            shutil.move(ruta_archivo, destino)
        except Exception as e:
            print(f"Error al mover {archivo} a 'No clasificados': {e}")

