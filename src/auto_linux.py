import os
import shutil
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from PyPDF2 import PdfReader
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Obtener la ruta desde los argumentos o usar la ruta por defecto
if len(sys.argv) > 1:
    ruta = sys.argv[1]
else:
    ruta = "/home/dani/Documentos/Directorio prubeas script"

# Diccionario de extensiones y nombres de carpetas
extensiones = {
    "Imágenes": [".jpg", ".png", ".bmp", ".heif"],
    "PDFs": [".pdf"],
    "Vídeos": [".mp4", ".mov", ".avi"],
    "Documentos": [".doc", ".docx", ".xls", ".xlsx"],
    "Documentos_txt": [".txt"],
    "Documentos_docx": [".docx"]
}

def obtener_dispositivo_y_fecha(archivo, ext):
    dispositivo = "Desconocido"
    fecha = None
    ruta_archivo = os.path.join(ruta, archivo)
    ext = ext.lower()
    # Imágenes
    if ext in [".jpg", ".jpeg", ".png", ".bmp", ".heif"]:
        try:
            imagen = Image.open(ruta_archivo)
            exif_data = imagen.getexif()
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == "Model" and value:
                        dispositivo = str(value).replace("/", "_")
                    if tag == "DateTimeOriginal" and value:
                        fecha = value.split(" ")[0].replace(":", "-")
            if not fecha:
                # Si no hay fecha en EXIF, usar fecha de modificación
                timestamp = os.path.getmtime(ruta_archivo)
                fecha = datetime.fromtimestamp(timestamp).strftime("%d-%m-%Y")
        except Exception:
            timestamp = os.path.getmtime(ruta_archivo)
            fecha = datetime.fromtimestamp(timestamp).strftime("%d-%m-%Y")
    # PDFs
    elif ext == ".pdf":
        try:
            reader = PdfReader(ruta_archivo)
            info = reader.metadata
            if info:
                # Dispositivo (producer)
                producer = getattr(info, 'producer', None)
                if producer:
                    dispositivo = str(producer).replace("/", "_")
                # Fecha de creación
                creation_date = getattr(info, 'creation_date', None)
                if creation_date:
                    if isinstance(creation_date, datetime):
                        fecha = creation_date.strftime("%d-%m-%Y")
                    elif isinstance(creation_date, str):
                        raw = creation_date
                        if raw.startswith("D:"):
                            raw = raw[2:]
                        if len(raw) >= 8:
                            fecha = f"{raw[6:8]}-{raw[4:6]}-{raw[0:4]}"
            if not fecha:
                timestamp = os.path.getmtime(ruta_archivo)
                fecha = datetime.fromtimestamp(timestamp).strftime("%d-%m-%Y")
        except Exception:
            timestamp = os.path.getmtime(ruta_archivo)
            fecha = datetime.fromtimestamp(timestamp).strftime("%d-%m-%Y")
    # Otros archivos
    else:
        timestamp = os.path.getmtime(ruta_archivo)
        fecha = datetime.fromtimestamp(timestamp).strftime("%d-%m-%Y")
    if not dispositivo:
        dispositivo = "Desconocido"
    if not fecha:
        fecha = "Desconocido"
    return dispositivo, fecha

# Escanear extensiones presentes en el directorio
extensiones_presentes = set()
archivos_encontrados = []
for archivo in os.listdir(ruta):
    ruta_archivo = os.path.join(ruta, archivo)
    if os.path.isfile(ruta_archivo):
        archivos_encontrados.append(archivo)
        _, ext = os.path.splitext(archivo)
        for carpeta, exts in extensiones.items():
            if ext.lower() in exts:
                extensiones_presentes.add(carpeta)

# Crear solo los directorios principales necesarios
for carpeta in extensiones_presentes:
    ruta_carpeta = os.path.join(ruta, carpeta)
    if not os.path.exists(ruta_carpeta):
        os.makedirs(ruta_carpeta)

# Mover archivos a sus subcarpetas correspondientes
for archivo in archivos_encontrados:
    _, ext = os.path.splitext(archivo)
    for carpeta, exts in extensiones.items():
        if carpeta in extensiones_presentes and ext.lower() in exts:
            dispositivo, fecha = obtener_dispositivo_y_fecha(archivo, ext)
            subcarpeta = os.path.join(ruta, carpeta, dispositivo, fecha)
            if not os.path.exists(subcarpeta):
                os.makedirs(subcarpeta)
            shutil.move(os.path.join(ruta, archivo), os.path.join(subcarpeta, archivo))
            break