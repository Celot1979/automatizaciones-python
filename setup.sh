#!/bin/bash
set -e

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

echo "\n¡Instalación completada!"
echo "Para ejecutar la aplicación principal, usa:"
echo "source venv/bin/activate && python3 src/interfaz_auto_linux.py" 