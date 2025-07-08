import os
import shutil

#Ruta donde están los archivos a ordenar
ruta = "/Users/danielgil/Documents/Venta del ordenador"

#Crear carpetas en destino sí no existen

tipos=["Imágenes","PDFs","Vídeos","Documentos", "Documentos_txt", "Documentos_docx"]

for carpeta in tipos:
    ruta_carpeta= os.path.join(ruta,carpeta)
    if not os.path.exists(ruta_carpeta):
        os.makedirs(ruta_carpeta)



for archivo in os.listdir(ruta):
    if archivo.endswith(".jpg") or archivo.endswith(".png") or archivo.endswith(".bmp") or archivo.endswith(".heif") or archivo.endswith(".jpg"):
        shutil.move(os.path.join(ruta, archivo), os.path.join(ruta, "Imágenes", archivo))
    elif archivo.endswith(".pdf"):
        shutil.move(os.path.join(ruta, archivo), os.path.join(ruta, "PDFs", archivo))
    elif archivo.endswith(".mp4") or archivo.endswith(".mov") or archivo.endswith(".avi"):
       shutil.move(os.path.join(ruta,archivo),os.path.join(ruta,"Vídeos",archivo)) 
    elif archivo.endswith(".doc") or archivo.endswith(".docx") or archivo.endswith(".xls") or archivo.endswith(".xlsx"):
        shutil.move(os.path.join(ruta,archivo),os.path.join(ruta,"Documentos",archivo))

