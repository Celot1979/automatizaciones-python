# Gestor de Archivos con Tkinter

Este proyecto es una aplicación de Python con interfaz gráfica utilizando Tkinter, diseñada para automatizar tareas de organización y gestión de archivos. La aplicación permite organizar directorios como `Descargas`, creando subdirectorios específicos para diferentes tipos de archivos según sus extensiones.

## Características

- **Organización Automática de Archivos**: Analiza los archivos en un directorio seleccionado y los organiza en carpetas según sus extensiones (Imágenes, PDFs, Vídeos, Documentos, Documentos.txt, Documentos_Docx, etc.).
- **Registro de Actividades**: Permite ver los registros de las actividades realizadas a través de la interfaz de usuario y también guarda un registro en un archivo de texto en el directorio raíz seleccionado.
- **Renombrado Masivo de Archivos**: Facilita el renombrado masivo de archivos en un subdirectorio, útil para renombrar múltiples archivos de manera eficiente (ejemplo: "foto1, foto2, foto3, etc.").
- **Unificación de Archivos**: Permite seleccionar archivos de diferentes ubicaciones del sistema y unificarlos en un directorio específico bajo un nombre común.
- **Observador de Directorios**: Mientras la aplicación está abierta, observa el directorio seleccionado y automáticamente mueve los archivos a la carpeta correspondiente según su extensión.

## Requisitos

Para clonar el repositorio y ejecutar el proyecto, sigue estos pasos:

1. Clona el repositorio en tu máquina local.
2. Crea un entorno virtual para el proyecto.
3. Instala las dependencias necesarias utilizando el archivo `requirements.txt` o instala las librerías manualmente.

```bash
git clone <URL-del-repositorio>
cd <directorio-del-repositorio>
python -m venv venv
source venv/bin/activate  # En sistemas Unix
venv\Scripts\activate  # En sistemas Windows
pip install -r requirements.txt

