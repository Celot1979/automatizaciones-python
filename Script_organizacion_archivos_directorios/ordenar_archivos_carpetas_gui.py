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
        # Botón para ver el registro
        tk.Button(frame, text="Ver registro de movimientos", command=self.ver_registro).grid(row=4+len(EXTENSIONES_A_CARPETAS), column=0, pady=(5,0))

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.ruta.set(carpeta)
            self._iniciar_observer(carpeta)

    def organizar_archivo_individual(self, ruta_archivo):
        import time
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
        if not tipos_seleccionados:
            return
        archivo = os.path.basename(ruta_archivo)
        _, extension = os.path.splitext(archivo)
        extension = extension.lower()
        subdir_metadatos = self._obtener_subdirectorio_metadatos(ruta_archivo, extension)
        movido = False
        ruta_log = os.path.join(ruta, "registro_movimientos.txt")
        for carpeta, extensiones in tipos_seleccionados.items():
            if extension in extensiones:
                ruta_carpeta_fecha = os.path.join(ruta, carpeta, subdir_metadatos)
                if not os.path.exists(ruta_carpeta_fecha):
                    os.makedirs(ruta_carpeta_fecha)
                destino = self._obtener_nombre_disponible(ruta_carpeta_fecha, archivo)
                try:
                    shutil.move(ruta_archivo, destino)
                    destino_log = destino.replace('\\', '/')
                    with open(ruta_log, "a", encoding="utf-8") as f:
                        f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Movido: {archivo} -> {destino_log}\n")
                    messagebox.showinfo("Archivo organizado", f"Se organizó el archivo:\n{archivo}\n\nUbicación final:\n{destino_log}")
                    print(f"[Organizador] Movido: {archivo} -> {destino_log}")
                except Exception as e:
                    print(f"Error al mover {archivo}: {e}")
                movido = True
                break
        if not movido:
            carpeta_no_clasificados = "No clasificados"
            ruta_no_clasificados = os.path.join(ruta, carpeta_no_clasificados, subdir_metadatos)
            if not os.path.exists(ruta_no_clasificados):
                os.makedirs(ruta_no_clasificados)
            destino = self._obtener_nombre_disponible(ruta_no_clasificados, archivo)
            try:
                shutil.move(ruta_archivo, destino)
                destino_log = destino.replace('\\', '/')
                with open(ruta_log, "a", encoding="utf-8") as f:
                    f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Movido: {archivo} -> {destino_log}\n")
                messagebox.showinfo("Archivo organizado", f"Se organizó el archivo:\n{archivo}\n\nUbicación final:\n{destino_log}")
                print(f"[Organizador] Movido: {archivo} -> {destino_log}")
            except Exception as e:
                print(f"Error al mover {archivo} a 'No clasificados': {e}")

    def organizar(self):
        ruta = self.ruta.get()
        if not ruta:
            messagebox.showerror("Error", "Por favor selecciona una carpeta.")
            return
        tipos_seleccionados = {k: v for k, v in EXTENSIONES_A_CARPETAS.items() if self.check_vars[k].get()}
        if not tipos_seleccionados:
            messagebox.showerror("Error", "Selecciona al menos un tipo de archivo.")
            return
        for carpeta in tipos_seleccionados.keys():
            ruta_carpeta = os.path.join(ruta, carpeta)
            if not os.path.exists(ruta_carpeta):
                os.makedirs(ruta_carpeta)
        carpeta_no_clasificados = "No clasificados"
        ruta_no_clasificados = os.path.join(ruta, carpeta_no_clasificados)
        if not os.path.exists(ruta_no_clasificados):
            os.makedirs(ruta_no_clasificados)
        ruta_log = os.path.join(ruta, "registro_movimientos.txt")
        usuario = getpass.getuser()
        for archivo in os.listdir(ruta):
            ruta_archivo = os.path.join(ruta, archivo)
            if os.path.isdir(ruta_archivo):
                continue
            _, extension = os.path.splitext(archivo)
            extension = extension.lower()
            movido = False
            subdir_metadatos = self._obtener_subdirectorio_metadatos(ruta_archivo, extension)
            for carpeta, extensiones in tipos_seleccionados.items():
                if extension in extensiones:
                    ruta_carpeta_fecha = os.path.join(ruta, carpeta, subdir_metadatos)
                    if not os.path.exists(ruta_carpeta_fecha):
                        os.makedirs(ruta_carpeta_fecha)
                    destino = self._obtener_nombre_disponible(ruta_carpeta_fecha, archivo)
                    try:
                        shutil.move(ruta_archivo, destino)
                        destino_log = destino.replace('\\', '/')
                        with open(ruta_log, "a", encoding="utf-8") as f:
                            f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Movido: {archivo} -> {destino_log}\n")
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
                    with open(ruta_log, "a", encoding="utf-8") as f:
                        f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Movido: {archivo} -> {destino_log}\n")
                except Exception as e:
                    print(f"Error al mover {archivo} a 'No clasificados': {e}")
        messagebox.showinfo("Éxito", "Operación realizada con éxito")

    def ver_registro(self):
        import tkinter.ttk as ttk
        from datetime import datetime as dt
        import re
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
        # Parsear líneas del log: 'YYYY-MM-DD HH:MM:SS - Movido: archivo -> ruta'
        datos = []
        patron = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - Movido: (.+?) -> (.+)$")
        for linea in lineas:
            m = patron.match(linea.strip())
            if m:
                fecha, nombre, ruta_destino = m.groups()
                datos.append([fecha, nombre, ruta_destino])
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

if __name__ == "__main__":
    root = tk.Tk()
    app = OrganizadorArchivosApp(root)
    root.mainloop() 