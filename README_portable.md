# Script Automatización Linux (Modo Portable)

Este proyecto te permite organizar, renombrar, unificar y limpiar archivos (especialmente fotos) en Linux, con interfaz gráfica, **sin necesidad de instalar nada en el sistema**.

## ¿Cómo usarlo en modo portable?

### 1. Descarga o clona el proyecto

```bash
git clone https://github.com/tuusuario/script_Linux.git
cd script_Linux
```

### 2. Crea y activa un entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instala las dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Lanza la aplicación principal

```bash
python3 src/interfaz_auto_linux.py
```

---

## Notas
- **No necesitas permisos de superusuario.**
- Puedes mover la carpeta a cualquier sitio o a otro ordenador (solo necesitas Python 3).
- Si quieres desinstalar, simplemente borra la carpeta.
- Si tienes dudas o encuentras errores, abre un issue en el repositorio.

---

¡Disfruta de la automatización de archivos en Linux de forma sencilla y portable! 