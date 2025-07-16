import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
import getpass
import datetime
import re
import threading
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    Observer = None
    FileSystemEventHandler = object

# Diccionario que mapea extensiones a carpetas
EXTENSIONES_A_CARPETAS = {
    "Imágenes": [".jpg", ".jpeg", ".png", ".bmp", ".heif", ".HEIC"],
    "PDFs": [".pdf"],
    "Vídeos": [".mp4", ".mov", ".avi"],
    "Documentos": [".doc", ".xls", ".xlsx"],
    "Documentos_txt": [".txt"],
    "Documentos_docx": [".docx"]
}

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    Image = None
    TAGS = None
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None
try:
    import docx
except ImportError:
    docx = None
try:
    from hachoir.parser import createParser
    from hachoir.metadata import extractMetadata
except ImportError:
    createParser = None
    extractMetadata = None

from interfaz_renombrar import abrir_ventana_renombrar
from interfaz_unificar import abrir_ventana_unificar
from interfaz_borrar_duplicados import abrir_ventana_borrar_duplicados

class OrganizadorObserver(FileSystemEventHandler):
    def __init__(self, app):
        self.app = app
        super().__init__()
    def on_created(self, event):
        if event.is_directory:
            return
        # Excluir el archivo de log
        if os.path.basename(event.src_path) == 'registro_movimientos.txt':
            print(f"[Observer] Ignorado: {event.src_path}")
            return
        # Solo organizar si el archivo está en la raíz
        if os.path.dirname(event.src_path) != self.app.ruta.get():
            print(f"[Observer] Ignorado (no en raíz): {event.src_path}")
            return
        # Esperar a que el archivo termine de copiarse
        import time
        time.sleep(1)
        print(f"[Observer] Detectado nuevo archivo: {event.src_path}")
        self.app.organizar_archivo_individual(event.src_path)

class OrganizadorArchivosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Organizador de Archivos")
        self.ruta = tk.StringVar()
        self.check_vars = {tipo: tk.BooleanVar(value=True) for tipo in EXTENSIONES_A_CARPETAS}
        self._crear_widgets()
        self.observer = None
        self.observer_thread = None
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _iniciar_observer(self, ruta):
        if Observer is None:
            print("Watchdog no está instalado. El observer no funcionará.")
            return
        if self.observer:
            self.observer.stop()
            self.observer.join()
        event_handler = OrganizadorObserver(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, ruta, recursive=False)
        self.observer_thread = threading.Thread(target=self.observer.start, daemon=True)
        self.observer_thread.start()
        print(f"Observer iniciado en: {ruta}")

    def _on_close(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
        self.root.destroy()

    def _obtener_nombre_disponible(self, carpeta_destino, nombre_archivo):
        """
        Dado un nombre de archivo y una carpeta destino, devuelve un nombre disponible
        agregando _(<número>) antes de la extensión si es necesario.
        """
        base, ext = os.path.splitext(nombre_archivo)
        destino = os.path.join(carpeta_destino, nombre_archivo)
        i = 1
        while os.path.exists(destino):
            nuevo_nombre = f"{base}_({i}){ext}"
            destino = os.path.join(carpeta_destino, nuevo_nombre)
            i += 1
        return destino

    def _obtener_fecha_archivo(self, ruta_archivo):
        # Intenta obtener la fecha de creación, si no, la de modificación
        try:
            timestamp = os.path.getctime(ruta_archivo)
        except Exception:
            timestamp = os.path.getmtime(ruta_archivo)
        return datetime.datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y')

    def _obtener_subdirectorio_metadatos(self, ruta_archivo, extension):
        extension = extension.lower()
        # Imágenes
        if extension in ['.jpg', '.jpeg', '.png', '.bmp', '.heif'] and Image is not None and TAGS is not None:
            try:
                img = Image.open(ruta_archivo)
                exif_data = img._getexif()
                marca = modelo = fecha = None
                if exif_data:
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        if tag == 'Make':
                            marca = str(value).replace(' ', '_')
                        elif tag == 'Model':
                            modelo = str(value).replace(' ', '_')
                        elif tag == 'DateTimeOriginal':
                            fecha = value.split(' ')[0].replace(':', '-')
                partes = [p for p in [marca, modelo, fecha] if p]
                if partes:
                    return '_'.join(partes)
            except Exception:
                pass
        # PDFs
        if extension == '.pdf' and PyPDF2 is not None:
            try:
                with open(ruta_archivo, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    info = reader.metadata
                    autor = info.author if info and info.author else None
                    fecha = None
                    if info and info.creation_date:
                        fecha = str(info.creation_date)
                        # Formato: D:20240101123456Z
                        m = re.match(r"D:(\d{4})(\d{2})(\d{2})", fecha)
                        if m:
                            fecha = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
                        else:
                            fecha = None
                    partes = [p for p in [autor, fecha] if p]
                    if partes:
                        return '_'.join(partes)
            except Exception:
                pass
        # Vídeos
        if extension in ['.mp4', '.mov', '.avi'] and createParser is not None and extractMetadata is not None:
            try:
                parser = createParser(ruta_archivo)
                if parser:
                    metadata = extractMetadata(parser)
                    dispositivo = metadata.get('device manufacturer') if metadata and metadata.has('device manufacturer') else None
                    fecha = None
                    if metadata and metadata.has('creation_date'):
                        fecha = metadata.get('creation_date').strftime('%d-%m-%Y')
                    partes = [p for p in [dispositivo, fecha] if p]
                    if partes:
                        return '_'.join(partes)
            except Exception:
                pass
        # Documentos docx
        if extension == '.docx' and docx is not None:
            try:
                doc = docx.Document(ruta_archivo)
                props = doc.core_properties
                autor = props.author if props.author else None
                fecha = None
                if props.created:
                    fecha = props.created.strftime('%d-%m-%Y')
                partes = [p for p in [autor, fecha] if p]
                if partes:
                    return '_'.join(partes)
            except Exception:
                pass
        # Si no hay metadatos, usar solo la fecha del sistema
        return self._obtener_fecha_archivo(ruta_archivo)

    def _escribir_registro_tabla(self, ruta_log, movimientos):
        # movimientos: lista de [fecha, nombre, ruta_destino]
        # Calcular anchos de columna
        encabezados = ["Fecha", "Nombre", "Ruta destino"]
        cols = list(zip(*([encabezados] + movimientos)))
        anchos = [max(len(str(item)) for item in col) for col in cols]
        def fila_tabla(fila):
            return "* " + " * ".join(str(item).ljust(anchos[i]) for i, item in enumerate(fila)) + " *"
        separador = "*" + "*".join(["".ljust(anchos[i]+2, "*") for i in range(len(anchos))]) + "*"
        lineas = [separador, fila_tabla(encabezados), separador]
        for mov in movimientos:
            lineas.append(fila_tabla(mov))
        lineas.append(separador)
        with open(ruta_log, "w", encoding="utf-8") as f:
            f.write("\n".join(lineas) + "\n")

    def _crear_widgets(self):
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)

        tk.Label(frame, text="Selecciona la carpeta a organizar:").grid(row=0, column=0, sticky="w")
        tk.Entry(frame, textvariable=self.ruta, width=40, state="readonly").grid(row=1, column=0, padx=(0,10))
        tk.Button(frame, text="Explorar", command=self.seleccionar_carpeta).grid(row=1, column=1)

        tk.Label(frame, text="Selecciona los tipos de archivos a organizar:").grid(row=2, column=0, sticky="w", pady=(10,0))
        for i, tipo in enumerate(EXTENSIONES_A_CARPETAS):
            tk.Checkbutton(frame, text=tipo, variable=self.check_vars[tipo]).grid(row=3+i, column=0, sticky="w")

        tk.Button(frame, text="Organizar", command=self.organizar).grid(row=3+len(EXTENSIONES_A_CARPETAS), column=0, pady=(15,0))
        tk.Button(frame, text="Ver registro de movimientos", command=self.ver_registro).grid(row=4+len(EXTENSIONES_A_CARPETAS), column=0, pady=(5,0))

        # --- Botón para renombrar archivos en masa en la ventana principal ---
        tk.Button(frame, text="Renombrar archivos en masa", command=lambda: abrir_ventana_renombrar(self.root)).grid(row=5+len(EXTENSIONES_A_CARPETAS), column=0, pady=(10,0))

        # --- Botón para unificar archivos en la ventana principal ---
        tk.Button(frame, text="Unificar archivos", command=lambda: abrir_ventana_unificar(self.root)).grid(row=6+len(EXTENSIONES_A_CARPETAS), column=0, pady=(10,0))

        # --- Botón para escanear y borrar archivos duplicados ---
        tk.Button(frame, text="Escanear archivos repetidos", command=lambda: abrir_ventana_borrar_duplicados(self.root)).grid(row=7+len(EXTENSIONES_A_CARPETAS), column=0, pady=(10,0))

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.ruta.set(carpeta)
            self._iniciar_observer(carpeta)

    def organizar_archivo_individual(self, ruta_archivo):
        import time
        import os
        # Excluir el archivo de log
        if os.path.basename(ruta_archivo) == 'registro_movimientos.txt':
            print(f"[Organizador] Ignorado: {ruta_archivo}")
            return
        # Solo organizar si el archivo está en la raíz
        if os.path.dirname(ruta_archivo) != self.ruta.get():
            print(f"[Organizador] Ignorado (no en raíz): {ruta_archivo}")
            return
        # Esperar si el archivo está siendo copiado
        for _ in range(10):
            try:
                with open(ruta_archivo, 'rb'):
                    break
            except Exception:
                time.sleep(0.5)
        ruta = self.ruta.get()
        if not ruta:
            return
        tipos_seleccionados = {k: v for k, v in EXTENSIONES_A_CARPETAS.items() if self.check_vars[k].get()}
        archivo = os.path.basename(ruta_archivo)
        _, extension = os.path.splitext(archivo)
        extension = extension.lower()
        # Si la extensión no está reflejada, crear directorio EXT_<EXT>
        if not any(extension in v for v in EXTENSIONES_A_CARPETAS.values()):
            nombre_dir = f"EXT_{extension[1:].upper()}"
            tipos_seleccionados[nombre_dir] = [extension]
        subdir_metadatos = self._obtener_subdirectorio_metadatos(ruta_archivo, extension)
        movido = False
        ruta_log = os.path.join(ruta, "registro_movimientos.txt")
        for carpeta, extensiones in tipos_seleccionados.items():
            if extension in extensiones:
                ruta_carpeta = os.path.join(ruta, carpeta)
                if not os.path.exists(ruta_carpeta):
                    os.makedirs(ruta_carpeta)
                ruta_carpeta_fecha = os.path.join(ruta, carpeta, subdir_metadatos)
                if not os.path.exists(ruta_carpeta_fecha):
                    os.makedirs(ruta_carpeta_fecha)
                destino = self._obtener_nombre_disponible(ruta_carpeta_fecha, archivo)
                try:
                    shutil.move(ruta_archivo, destino)
                    destino_log = destino.replace('\\', '/')
                    # Leer movimientos previos
                    movimientos = []
                    if os.path.exists(ruta_log):
                        with open(ruta_log, "r", encoding="utf-8") as f:
                            for linea in f:
                                if linea.startswith("*") and not linea.strip().startswith("* Fecha") and not set(linea.strip()) <= {'*'}:
                                    partes = [p.strip() for p in linea.strip().strip('*').split('*')]
                                    if len(partes) == 3:
                                        movimientos.append(partes)
                    # Agregar nuevo movimiento
                    base_folder = os.path.basename(ruta.rstrip(os.sep))
                    ruta_relativa = os.path.relpath(destino_log, ruta)
                    ruta_mostrar = f"{base_folder}/{ruta_relativa}".replace("\\", "/")
                    movimientos.append([
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        archivo,
                        ruta_mostrar
                    ])
                    self._escribir_registro_tabla(ruta_log, movimientos)
                    messagebox.showinfo("Archivo organizado", f"Se organizó el archivo:\n{archivo}\n\nUbicación final:\n{ruta_mostrar}")
                    print(f"[Organizador] Movido: {archivo} -> {ruta_mostrar}")
                except Exception as e:
                    print(f"Error al mover {archivo}: {e}")
                movido = True
                break
        if not movido:
            carpeta_no_clasificados = "No clasificados"
            ruta_no_clasificados = os.path.join(ruta, carpeta_no_clasificados)
            if not os.path.exists(ruta_no_clasificados):
                os.makedirs(ruta_no_clasificados)
            ruta_no_clasificados_fecha = os.path.join(ruta_no_clasificados, subdir_metadatos)
            if not os.path.exists(ruta_no_clasificados_fecha):
                os.makedirs(ruta_no_clasificados_fecha)
            destino = self._obtener_nombre_disponible(ruta_no_clasificados_fecha, archivo)
            try:
                shutil.move(ruta_archivo, destino)
                destino_log = destino.replace('\\', '/')
                movimientos = []
                if os.path.exists(ruta_log):
                    with open(ruta_log, "r", encoding="utf-8") as f:
                        for linea in f:
                            if linea.startswith("*") and not linea.strip().startswith("* Fecha") and not set(linea.strip()) <= {'*'}:
                                partes = [p.strip() for p in linea.strip().strip('*').split('*')]
                                if len(partes) == 3:
                                    movimientos.append(partes)
                base_folder = os.path.basename(ruta.rstrip(os.sep))
                ruta_relativa = os.path.relpath(destino_log, ruta)
                ruta_mostrar = f"{base_folder}/{ruta_relativa}".replace("\\", "/")
                movimientos.append([
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    archivo,
                    ruta_mostrar
                ])
                self._escribir_registro_tabla(ruta_log, movimientos)
                messagebox.showinfo("Archivo organizado", f"Se organizó el archivo:\n{archivo}\n\nUbicación final:\n{ruta_mostrar}")
                print(f"[Organizador] Movido: {archivo} -> {ruta_mostrar}")
            except Exception as e:
                print(f"Error al mover {archivo} a 'No clasificados': {e}")

    def organizar(self):
        ruta = self.ruta.get()
        if not ruta:
            messagebox.showerror("Error", "Por favor selecciona una carpeta.")
            return
        archivos_en_raiz = [f for f in os.listdir(ruta) if os.path.isfile(os.path.join(ruta, f))]
        extensiones_presentes = set(os.path.splitext(f)[1].lower() for f in archivos_en_raiz)
        tipos_detectados = {k: v for k, v in EXTENSIONES_A_CARPETAS.items() if any(ext in extensiones_presentes for ext in v)}
        # Detectar extensiones no reflejadas
        extensiones_no_reflejadas = extensiones_presentes - set(e for v in EXTENSIONES_A_CARPETAS.values() for e in v)
        for ext in extensiones_no_reflejadas:
            if ext:
                nombre_dir = f"EXT_{ext[1:].upper()}"
                tipos_detectados[nombre_dir] = [ext]
        if not tipos_detectados:
            messagebox.showinfo("Sin archivos", "No se detectaron archivos compatibles para organizar en la carpeta seleccionada.")
            return
        for carpeta in tipos_detectados.keys():
            ruta_carpeta = os.path.join(ruta, carpeta)
            if not os.path.exists(ruta_carpeta):
                os.makedirs(ruta_carpeta)
        carpeta_no_clasificados = "No clasificados"
        ruta_no_clasificados = os.path.join(ruta, carpeta_no_clasificados)
        if not os.path.exists(ruta_no_clasificados):
            os.makedirs(ruta_no_clasificados)
        ruta_log = os.path.join(ruta, "registro_movimientos.txt")
        usuario = getpass.getuser()
        movimientos = []
        # Leer movimientos previos si existen
        if os.path.exists(ruta_log):
            with open(ruta_log, "r", encoding="utf-8") as f:
                for linea in f:
                    if linea.startswith("*") and not linea.strip().startswith("* Fecha") and not set(linea.strip()) <= {'*'}:
                        partes = [p.strip() for p in linea.strip().strip('*').split('*')]
                        if len(partes) == 3:
                            movimientos.append(partes)
        for archivo in archivos_en_raiz:
            ruta_archivo = os.path.join(ruta, archivo)
            _, extension = os.path.splitext(archivo)
            extension = extension.lower()
            movido = False
            subdir_metadatos = self._obtener_subdirectorio_metadatos(ruta_archivo, extension)
            for carpeta, extensiones in tipos_detectados.items():
                if extension in extensiones:
                    ruta_carpeta_fecha = os.path.join(ruta, carpeta, subdir_metadatos)
                    if not os.path.exists(ruta_carpeta_fecha):
                        os.makedirs(ruta_carpeta_fecha)
                    destino = self._obtener_nombre_disponible(ruta_carpeta_fecha, archivo)
                    try:
                        shutil.move(ruta_archivo, destino)
                        destino_log = destino.replace('\\', '/')
                        base_folder = os.path.basename(ruta.rstrip(os.sep))
                        ruta_relativa = os.path.relpath(destino_log, ruta)
                        ruta_mostrar = f"{base_folder}/{ruta_relativa}".replace("\\", "/")
                        movimientos.append([
                            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            archivo,
                            ruta_mostrar
                        ])
                    except Exception as e:
                        print(f"Error al mover {archivo}: {e}")
                    movido = True
                    break
            if not movido:
                ruta_no_clasificados_fecha = os.path.join(ruta_no_clasificados, subdir_metadatos)
                if not os.path.exists(ruta_no_clasificados_fecha):
                    os.makedirs(ruta_no_clasificados_fecha)
                destino = self._obtener_nombre_disponible(ruta_no_clasificados_fecha, archivo)
                try:
                    shutil.move(ruta_archivo, destino)
                    destino_log = destino.replace('\\', '/')
                    base_folder = os.path.basename(ruta.rstrip(os.sep))
                    ruta_relativa = os.path.relpath(destino_log, ruta)
                    ruta_mostrar = f"{base_folder}/{ruta_relativa}".replace("\\", "/")
                    movimientos.append([
                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        archivo,
                        ruta_mostrar
                    ])
                except Exception as e:
                    print(f"Error al mover {archivo} a 'No clasificados': {e}")
        self._escribir_registro_tabla(ruta_log, movimientos)
        messagebox.showinfo("Éxito", "Operación realizada con éxito")

    def ver_registro(self):
        import tkinter.ttk as ttk
        from datetime import datetime as dt
        import os
        ruta = self.ruta.get()
        if not ruta:
            messagebox.showerror("Error", "Por favor selecciona una carpeta para ver su registro.")
            return
        ruta_log = os.path.join(ruta, "registro_movimientos.txt")
        if not os.path.exists(ruta_log):
            messagebox.showinfo("Registro", "No existe ningún registro de movimientos en esta carpeta.")
            return
        with open(ruta_log, "r", encoding="utf-8") as f:
            lineas = f.readlines()
        if not lineas:
            messagebox.showinfo("Registro", "El registro está vacío.")
            return
        # Parsear la tabla: ignorar separadores y encabezado, extraer filas de datos
        datos = []
        for linea in lineas:
            l = linea.strip()
            if l.startswith("*") and not set(l) <= {'*'}:
                partes = [p.strip() for p in l.strip('*').split('*')]
                # Saltar encabezado
                if partes and partes[0] == "Fecha":
                    continue
                # Saltar filas vacías
                if len(partes) == 3 and partes[0] and partes[1] and partes[2]:
                    datos.append(partes)
        if not datos:
            messagebox.showinfo("Registro", "No hay registros válidos para mostrar.")
            return
        encabezados = ["Fecha", "Nombre", "Ruta destino"]
        ventana = tk.Toplevel(self.root)
        ventana.title("Registro de movimientos")
        # --- Filtros ---
        frame_filtros = tk.Frame(ventana)
        frame_filtros.pack(fill="x", padx=5, pady=5)
        tk.Label(frame_filtros, text="Nombre:").grid(row=0, column=0)
        entry_nombre = tk.Entry(frame_filtros, width=15)
        entry_nombre.grid(row=0, column=1, padx=2)
        tk.Label(frame_filtros, text="Extensión:").grid(row=0, column=2)
        entry_ext = tk.Entry(frame_filtros, width=8)
        entry_ext.grid(row=0, column=3, padx=2)
        tk.Label(frame_filtros, text="Fecha desde (YYYY-MM-DD):").grid(row=0, column=4)
        entry_fecha_desde = tk.Entry(frame_filtros, width=12)
        entry_fecha_desde.grid(row=0, column=5, padx=2)
        tk.Label(frame_filtros, text="Fecha hasta (YYYY-MM-DD):").grid(row=0, column=6)
        entry_fecha_hasta = tk.Entry(frame_filtros, width=12)
        entry_fecha_hasta.grid(row=0, column=7, padx=2)
        # --- Tabla ---
        tree = ttk.Treeview(ventana, columns=encabezados, show="headings")
        for col in encabezados:
            tree.heading(col, text=col)
            tree.column(col, width=220 if col=="Ruta destino" else 140, anchor="w")
        tree.pack(expand=True, fill="both")
        # Scrollbars
        scroll_y = tk.Scrollbar(ventana, orient="vertical", command=tree.yview)
        scroll_y.pack(side="right", fill="y")
        tree.config(yscrollcommand=scroll_y.set)
        scroll_x = tk.Scrollbar(ventana, orient="horizontal", command=tree.xview)
        scroll_x.pack(side="bottom", fill="x")
        tree.config(xscrollcommand=scroll_x.set)
        def cargar_tabla(filas):
            for i in tree.get_children():
                tree.delete(i)
            for fila in filas:
                tree.insert("", "end", values=fila)
        cargar_tabla(datos)
        def filtrar():
            nombre = entry_nombre.get().strip().lower()
            ext = entry_ext.get().strip().lower()
            fecha_desde = entry_fecha_desde.get().strip()
            fecha_hasta = entry_fecha_hasta.get().strip()
            filtrados = []
            for fila in datos:
                nombre_ok = True
                ext_ok = True
                fecha_ok = True
                # Filtrar por nombre
                if nombre:
                    if nombre not in fila[1].lower():
                        nombre_ok = False
                # Filtrar por extensión
                if ext:
                    if not fila[1].lower().endswith(ext):
                        ext_ok = False
                # Filtrar por fechas
                if fecha_desde or fecha_hasta:
                    try:
                        fecha_fila = dt.strptime(fila[0], "%Y-%m-%d %H:%M:%S")
                        if fecha_desde:
                            fecha_ini = dt.strptime(fecha_desde, "%Y-%m-%d")
                            if fecha_fila < fecha_ini:
                                fecha_ok = False
                        if fecha_hasta:
                            fecha_fin = dt.strptime(fecha_hasta, "%Y-%m-%d")
                            if fecha_fila > fecha_fin.replace(hour=23, minute=59, second=59):
                                fecha_ok = False
                    except Exception:
                        fecha_ok = False
                if nombre_ok and ext_ok and fecha_ok:
                    filtrados.append(fila)
            cargar_tabla(filtrados)
        tk.Button(frame_filtros, text="Filtrar", command=filtrar).grid(row=0, column=8, padx=5)

        # --- Botón para renombrar archivos en masa ---
        def abrir_ventana_renombrar():
            ventana_renombrar = tk.Toplevel(ventana)
            ventana_renombrar.title("Renombrar archivos en masa")
            tk.Label(ventana_renombrar, text="Selecciona el directorio base:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
            entry_dir = tk.Entry(ventana_renombrar, width=40)
            entry_dir.grid(row=0, column=1, padx=5, pady=5)
            def seleccionar_dir():
                carpeta = filedialog.askdirectory()
                if carpeta:
                    entry_dir.delete(0, tk.END)
                    entry_dir.insert(0, carpeta)
            tk.Button(ventana_renombrar, text="Explorar", command=seleccionar_dir).grid(row=0, column=2, padx=5, pady=5)
            tk.Label(ventana_renombrar, text="Nombre base para renombrar:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
            entry_nombre = tk.Entry(ventana_renombrar, width=30)
            entry_nombre.grid(row=1, column=1, padx=5, pady=5)
            def ejecutar_renombrado():
                dir_base = entry_dir.get().strip()
                nombre_base = entry_nombre.get().strip()
                if not dir_base or not nombre_base:
                    messagebox.showerror("Error", "Debes seleccionar un directorio y un nombre base.")
                    return
                archivos = []
                for root, _, files in os.walk(dir_base):
                    for f in files:
                        archivos.append(os.path.join(root, f))
                archivos.sort()  # Para consistencia
                contador = 1
                for archivo in archivos:
                    dir_actual = os.path.dirname(archivo)
                    _, ext = os.path.splitext(archivo)
                    nuevo_nombre = f"{nombre_base}{contador}{ext}"
                    nuevo_path = os.path.join(dir_actual, nuevo_nombre)
                    # Evitar sobrescribir
                    while os.path.exists(nuevo_path):
                        contador += 1
                        nuevo_nombre = f"{nombre_base}{contador}{ext}"
                        nuevo_path = os.path.join(dir_actual, nuevo_nombre)
                    try:
                        os.rename(archivo, nuevo_path)
                    except Exception as e:
                        messagebox.showerror("Error", f"No se pudo renombrar {archivo}: {e}")
                        return
                    contador += 1
                messagebox.showinfo("Éxito", f"Se renombraron {len(archivos)} archivos.")
                ventana_renombrar.destroy()
            tk.Button(ventana_renombrar, text="Renombrar", command=ejecutar_renombrado).grid(row=2, column=1, pady=10)
        tk.Button(ventana, text="Renombrar archivos en masa", command=abrir_ventana_renombrar).pack(pady=8)

if __name__ == "__main__":
    root = tk.Tk()
    app = OrganizadorArchivosApp(root)
    root.mainloop() 