# Suite de Organización y Gestión de Archivos para Linux

Este proyecto proporciona utilidades gráficas para organizar, renombrar, unificar y limpiar archivos (especialmente fotos) en Linux, con opciones de backup y deshacer.

## Estructura del proyecto

```
script_Linux/
├── src/                  # Scripts principales
│   ├── interfaz_auto_linux.py
│   ├── renombrar_masivo.py
│   ├── unificar_archivos.py
│   ├── repetidas.py
│   ├── repetidas_qt.py
│   └── ...otros scripts...
├── assets/               # Recursos opcionales (imágenes, iconos)
├── requirements.txt      # Dependencias Python
├── setup.sh              # Instalador automático
├── README.md             # Este archivo
├── .gitignore            # Ignora venv y archivos temporales
```

## Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/tuusuario/script_Linux.git
cd script_Linux
```

2. Ejecuta el instalador automático:

```bash
./setup.sh
```

## Uso

Activa el entorno virtual y ejecuta la interfaz principal:

```bash
source venv/bin/activate
python3 src/interfaz_auto_linux.py
```

Desde la ventana principal podrás acceder a las utilidades de:
- Organización automática de archivos
- Renombrado masivo
- Unificación de archivos
- Detección y borrado de fotos repetidas

## Notas
- Si usas recursos adicionales (imágenes, iconos), colócalos en la carpeta `assets/`.
- El entorno virtual y archivos temporales están ignorados por `.gitignore`.
- Si tienes dudas o encuentras errores, abre un issue en el repositorio. 