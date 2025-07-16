import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import subprocess
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import shutil
from renombrar_masivo import renombrar_archivos, restaurar_nombres
from unificar_archivos import unificar_archivos, rehacer_unificacion

class AutoLinuxGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Organizador de Archivos Linux")
        self.root.geometry("500x300")
        self.ruta = tk.StringVar()

        tk.Label(root, text="Selecciona la carpeta a organizar:").pack(pady=10)
        frame = tk.Frame(root)
        frame.pack(pady=5)
        self.entry = tk.Entry(frame, textvariable=self.ruta, width=40)
        self.entry.pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Examinar", command=self.seleccionar_ruta).pack(side=tk.LEFT)
        tk.Button(root, text="Organizar", command=self.organizar).pack(pady=10)
        tk.Button(root, text="Renombrar archivos en masa", command=self.abrir_ventana_renombrar).pack(pady=10)
        tk.Button(root, text="Unificar archivos", command=self.abrir_ventana_unificar).pack(pady=10)
        tk.Button(root, text="Escanear fotos repetidas", command=self.abrir_repetidas).pack(pady=10)

    def seleccionar_ruta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.ruta.set(carpeta)

    def organizar(self):
        ruta = self.ruta.get()
        if not ruta or not os.path.isdir(ruta):
            messagebox.showerror("Error", "Selecciona una carpeta válida.")
            return
        try:
            ruta_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_linux.py")
            resultado = subprocess.run([
                sys.executable, ruta_script, ruta
            ], capture_output=True, text=True)
            if resultado.returncode == 0:
                messagebox.showinfo("Éxito", "Archivos organizados correctamente.")
            else:
                messagebox.showerror("Error", f"Ocurrió un error:\n{resultado.stderr}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def abrir_ventana_renombrar(self):
        RenombrarVentana(self.root)

    def abrir_ventana_unificar(self):
        ruta_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unificar_archivos_qt.py")
        subprocess.Popen([sys.executable, ruta_script])

    def abrir_repetidas(self):
        ruta_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "repetidas_qt.py")
        subprocess.Popen([sys.executable, ruta_script])

class RenombrarVentana:
    def __init__(self, master):
        self.top = tk.Toplevel(master)
        self.top.title("Renombrar archivos en masa")
        self.top.geometry("600x420")
        self.archivos = []
        self.directorio = ""
        self.nombre_base = tk.StringVar()

        tk.Label(self.top, text="Selecciona la carpeta con los archivos a renombrar:").pack(pady=10)
        frame = tk.Frame(self.top)
        frame.pack(pady=5)
        self.entry_dir = tk.Entry(frame, width=40)
        self.entry_dir.pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Examinar", command=self.seleccionar_archivos).pack(side=tk.LEFT)

        self.listbox = tk.Listbox(self.top, selectmode=tk.BROWSE, width=70, height=10)
        self.listbox.pack(pady=10)

        tk.Label(self.top, text="Nombre base para renombrar:").pack(pady=5)
        tk.Entry(self.top, textvariable=self.nombre_base, width=30).pack(pady=5)
        tk.Button(self.top, text="Renombrar todos", command=self.renombrar_todos).pack(pady=5)
        tk.Button(self.top, text="Restaurar nombres originales", command=self.restaurar_y_cerrar).pack(pady=5)

        # Barra de progreso (Tkinter)
        # self.progress = None

    def seleccionar_archivos(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.directorio = carpeta
            self.entry_dir.delete(0, tk.END)
            self.entry_dir.insert(0, carpeta)
            archivos = os.listdir(carpeta)
            archivos = [f for f in archivos if os.path.isfile(os.path.join(carpeta, f))]
            self.archivos = archivos
            self.listbox.delete(0, tk.END)
            for archivo in archivos:
                self.listbox.insert(tk.END, archivo)

    def renombrar_todos(self):
        if not self.archivos:
            messagebox.showerror("Error", "No hay archivos para renombrar.")
            return
        nombre_base = self.nombre_base.get().strip()
        if not nombre_base:
            messagebox.showerror("Error", "Introduce un nombre base.")
            return
        total = len(self.archivos)
        def actualizar_progreso(i, total):
            pass
        try:
            from renombrar_masivo import renombrar_archivos
            renombrar_archivos(self.archivos, nombre_base, self.directorio, callback_progreso=actualizar_progreso)
            messagebox.showinfo("Éxito", "Archivos renombrados correctamente.")
            self.seleccionar_archivos()  # Refrescar lista
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def restaurar_y_cerrar(self):
        if not self.directorio:
            messagebox.showerror("Error", "Selecciona primero una carpeta.")
            return
        exito, mensaje = restaurar_nombres(self.directorio)
        if exito:
            messagebox.showinfo("Éxito", mensaje)
            self.top.destroy()
        else:
            messagebox.showerror("Error", mensaje)

class UnificarVentana:
    def __init__(self, master):
        self.top = tk.Toplevel(master)
        self.top.title("Unificar archivos de diferentes carpetas")
        self.top.geometry("800x700")
        self.directorios = []
        self.directorios_completos = []  # NUEVO: directorios completos a unificar
        self.archivos_por_directorio = {}  # {directorio: [archivo, ...]}
        self.archivos_seleccionados = set()  # set de rutas absolutas
        self.carpeta_destino = ""
        self.nombre_carpeta = tk.StringVar()
        self.nombre_base = tk.StringVar()
        self.progress = None  # Eliminar cualquier referencia a barra de progreso

        # Sección: Unificar directorios completos
        tk.Label(self.top, text="Unificar directorios completos (todos los archivos):").pack(pady=5)
        frame_dircomp = tk.Frame(self.top)
        frame_dircomp.pack(pady=2)
        tk.Button(frame_dircomp, text="Añadir directorio completo", command=self.anadir_directorio_completo).pack(side=tk.LEFT)
        tk.Button(frame_dircomp, text="Quitar directorio completo", command=self.quitar_directorio_completo).pack(side=tk.LEFT)
        self.listbox_dircomp = tk.Listbox(self.top, selectmode=tk.SINGLE, width=60, height=3)
        self.listbox_dircomp.pack(pady=2)

        # Sección: Selección de directorios y archivos individuales
        tk.Label(self.top, text="Selecciona los directorios de origen para archivos individuales:").pack(pady=5)
        frame_dirs = tk.Frame(self.top)
        frame_dirs.pack(pady=2)
        tk.Button(frame_dirs, text="Añadir directorio", command=self.anadir_directorio).pack(side=tk.LEFT)
        tk.Button(frame_dirs, text="Quitar directorio", command=self.quitar_directorio).pack(side=tk.LEFT)
        self.listbox_dirs = tk.Listbox(self.top, selectmode=tk.SINGLE, width=60, height=3)
        self.listbox_dirs.pack(pady=2)
        tk.Button(self.top, text="Mostrar archivos del directorio seleccionado", command=self.mostrar_archivos_directorio).pack(pady=2)

        # Frame para checkboxes de archivos del directorio
        self.frame_archivos_dir = tk.Frame(self.top)
        self.frame_archivos_dir.pack(pady=2)
        self.check_vars = []
        self.check_buttons = []

        # Añadir archivos sueltos
        tk.Button(self.top, text="Añadir archivos sueltos", command=self.anadir_archivos_sueltos).pack(pady=5)

        # Lista resumen de archivos seleccionados
        tk.Label(self.top, text="Archivos seleccionados para unificar:").pack(pady=5)
        self.listbox_resumen = tk.Listbox(self.top, selectmode=tk.BROWSE, width=90, height=8)
        self.listbox_resumen.pack(pady=2)
        tk.Button(self.top, text="Quitar archivo de la lista", command=self.quitar_archivo_resumen).pack(pady=2)

        # Selección de carpeta de destino
        tk.Label(self.top, text="Selecciona la carpeta de destino para la unificación:").pack(pady=5)
        frame_dest = tk.Frame(self.top)
        frame_dest.pack(pady=2)
        self.entry_dest = tk.Entry(frame_dest, width=40)
        self.entry_dest.pack(side=tk.LEFT, padx=5)
        tk.Button(frame_dest, text="Examinar", command=self.seleccionar_destino).pack(side=tk.LEFT)
        tk.Button(frame_dest, text="Crear nueva carpeta", command=self.crear_nueva_carpeta).pack(side=tk.LEFT)

        # Nombre de la nueva carpeta
        tk.Label(self.top, text="Nombre de la nueva carpeta:").pack(pady=5)
        tk.Entry(self.top, textvariable=self.nombre_carpeta, width=30).pack(pady=2)

        # Nombre base para los archivos
        tk.Label(self.top, text="Nombre base para los archivos unificados:").pack(pady=5)
        tk.Entry(self.top, textvariable=self.nombre_base, width=30).pack(pady=2)

        # Botones de acción
        tk.Button(self.top, text="Unificar archivos", command=self.unificar).pack(pady=10)
        tk.Button(self.top, text="Rehacer el proceso", command=self.rehacer).pack(pady=2)

    def anadir_directorio_completo(self):
        carpeta = filedialog.askdirectory()
        if carpeta and carpeta not in self.directorios_completos:
            self.directorios_completos.append(carpeta)
            self.listbox_dircomp.insert(tk.END, carpeta)
            # Añadir todos los archivos de este directorio a la lista de archivos seleccionados
            for archivo in os.listdir(carpeta):
                ruta_abs = os.path.join(carpeta, archivo)
                if os.path.isfile(ruta_abs):
                    self.archivos_seleccionados.add(ruta_abs)
            self.actualizar_resumen()

    def quitar_directorio_completo(self):
        seleccion = self.listbox_dircomp.curselection()
        if seleccion:
            idx = seleccion[0]
            carpeta = self.directorios_completos.pop(idx)
            self.listbox_dircomp.delete(idx)
            # Quitar todos los archivos de este directorio de la lista de archivos seleccionados
            for archivo in os.listdir(carpeta):
                ruta_abs = os.path.join(carpeta, archivo)
                if ruta_abs in self.archivos_seleccionados:
                    self.archivos_seleccionados.remove(ruta_abs)
            self.actualizar_resumen()

    def anadir_directorio(self):
        carpeta = filedialog.askdirectory()
        if carpeta and carpeta not in self.directorios:
            self.directorios.append(carpeta)
            self.archivos_por_directorio[carpeta] = [f for f in os.listdir(carpeta) if os.path.isfile(os.path.join(carpeta, f))]
            self.listbox_dirs.insert(tk.END, carpeta)

    def quitar_directorio(self):
        seleccion = self.listbox_dirs.curselection()
        if seleccion:
            idx = seleccion[0]
            carpeta = self.directorios.pop(idx)
            self.archivos_por_directorio.pop(carpeta, None)
            self.listbox_dirs.delete(idx)
            self.limpiar_checkboxes()

    def mostrar_archivos_directorio(self):
        self.limpiar_checkboxes()
        seleccion = self.listbox_dirs.curselection()
        if not seleccion:
            return
        carpeta = self.directorios[seleccion[0]]
        archivos = self.archivos_por_directorio.get(carpeta, [])
        self.check_vars = []
        self.check_buttons = []
        for archivo in archivos:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.frame_archivos_dir, text=archivo, variable=var,
                                 command=lambda a=archivo, c=carpeta, v=var: self.toggle_archivo(a, c, v))
            chk.pack(anchor='w')
            self.check_vars.append(var)
            self.check_buttons.append(chk)

    def limpiar_checkboxes(self):
        for chk in self.check_buttons:
            chk.destroy()
        self.check_vars = []
        self.check_buttons = []

    def toggle_archivo(self, archivo, carpeta, var):
        ruta_abs = os.path.join(carpeta, archivo)
        if var.get():
            self.archivos_seleccionados.add(ruta_abs)
        else:
            self.archivos_seleccionados.discard(ruta_abs)
        self.actualizar_resumen()

    def anadir_archivos_sueltos(self):
        archivos = filedialog.askopenfilenames()
        for ruta in archivos:
            self.archivos_seleccionados.add(ruta)
        self.actualizar_resumen()

    def actualizar_resumen(self):
        self.listbox_resumen.delete(0, tk.END)
        for ruta in sorted(self.archivos_seleccionados):
            self.listbox_resumen.insert(tk.END, ruta)

    def quitar_archivo_resumen(self):
        seleccion = self.listbox_resumen.curselection()
        if seleccion:
            idx = seleccion[0]
            ruta = self.listbox_resumen.get(idx)
            self.archivos_seleccionados.discard(ruta)
            self.actualizar_resumen()

    def seleccionar_destino(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.carpeta_destino = carpeta
            self.entry_dest.delete(0, tk.END)
            self.entry_dest.insert(0, carpeta)

    def crear_nueva_carpeta(self):
        carpeta_base = filedialog.askdirectory(title="Selecciona la ubicación para la nueva carpeta")
        if carpeta_base:
            nombre = simpledialog.askstring("Nombre de la carpeta", "Introduce el nombre de la nueva carpeta:")
            if nombre:
                nueva_ruta = os.path.join(carpeta_base, nombre)
                try:
                    os.makedirs(nueva_ruta, exist_ok=False)
                    self.carpeta_destino = nueva_ruta
                    self.entry_dest.delete(0, tk.END)
                    self.entry_dest.insert(0, nueva_ruta)
                    messagebox.showinfo("Éxito", f"Carpeta creada: {nueva_ruta}")
                except FileExistsError:
                    messagebox.showerror("Error", "La carpeta ya existe.")
                except Exception as e:
                    messagebox.showerror("Error", str(e))

    def unificar(self):
        if not self.archivos_seleccionados:
            messagebox.showerror("Error", "Selecciona al menos un archivo para unificar.")
            return
        if not self.carpeta_destino:
            messagebox.showerror("Error", "Selecciona la carpeta de destino.")
            return
        nombre_carpeta = self.nombre_carpeta.get().strip()
        if not nombre_carpeta:
            messagebox.showerror("Error", "Introduce el nombre de la nueva carpeta.")
            return
        nombre_base = self.nombre_base.get().strip()
        if not nombre_base:
            messagebox.showerror("Error", "Introduce el nombre base para los archivos.")
            return
        archivos_a_unificar = [(os.path.dirname(ruta), os.path.basename(ruta)) for ruta in sorted(self.archivos_seleccionados)]
        total = len(archivos_a_unificar)
        try:
            from unificar_archivos import unificar_archivos
            ruta_unificacion = os.path.join(self.carpeta_destino, self.nombre_carpeta.get().strip())
            os.makedirs(ruta_unificacion, exist_ok=True)
            backup = []
            for i, (ruta_original, archivo) in enumerate(archivos_a_unificar, start=1):
                extension = os.path.splitext(archivo)[1]
                nuevo_nombre = f"{nombre_base}_{i}{extension}"
                ruta_nueva = os.path.join(ruta_unificacion, nuevo_nombre)
                origen_absoluto = os.path.join(ruta_original, archivo)
                shutil.copy2(origen_absoluto, ruta_nueva)
                backup.append({
                    "origen": ruta_original,
                    "archivo_original": archivo,
                    "ruta_nueva": ruta_unificacion,
                    "archivo_nuevo": nuevo_nombre
                })
            import json
            with open(os.path.join(ruta_unificacion, "backup_unificacion.json"), "w") as f:
                json.dump(backup, f)
            messagebox.showinfo("Éxito", f"Archivos unificados en: {ruta_unificacion}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def rehacer(self):
        if not self.carpeta_destino or not self.nombre_carpeta.get().strip():
            messagebox.showerror("Error", "Debes indicar la carpeta de destino y el nombre de la carpeta de unificación.")
            return
        ruta_unificacion = os.path.join(self.carpeta_destino, self.nombre_carpeta.get().strip())
        exito, mensaje = rehacer_unificacion(ruta_unificacion)
        if exito:
            messagebox.showinfo("Éxito", mensaje)
            self.top.destroy()
        else:
            messagebox.showerror("Error", mensaje)

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoLinuxGUI(root)
    root.mainloop() 