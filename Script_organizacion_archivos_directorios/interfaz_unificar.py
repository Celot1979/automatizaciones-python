# interfaz_unificar.py
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from logica_unificar import unificar_archivos, deshacer_ultima_unificacion
import os

def abrir_ventana_unificar(parent=None):
    ventana_unificar = tk.Toplevel(parent) if parent else tk.Tk()
    ventana_unificar.title("Unificar archivos")
    ventana_unificar.geometry("850x650")
    frame_principal = tk.Frame(ventana_unificar)
    frame_principal.pack(fill="both", expand=True, padx=10, pady=10)
    frame_controles = tk.Frame(frame_principal)
    frame_controles.pack(fill="x", pady=(0, 10))
    tk.Label(frame_controles, text="Agregar archivos o directorios:").grid(row=0, column=0, sticky="w", padx=(0, 10))
    listbox_items = tk.Listbox(frame_principal, height=6, selectmode=tk.MULTIPLE)
    listbox_items.pack(fill="x")
    items_seleccionados = []  # Puede contener archivos y carpetas
    def agregar_archivo():
        archivos = filedialog.askopenfilenames()
        for archivo in archivos:
            if archivo not in items_seleccionados:
                items_seleccionados.append(archivo)
                listbox_items.insert(tk.END, archivo)
    def agregar_directorio():
        carpeta = filedialog.askdirectory()
        if carpeta and carpeta not in items_seleccionados:
            items_seleccionados.append(carpeta)
            listbox_items.insert(tk.END, carpeta)
    def eliminar_item():
        seleccion = listbox_items.curselection()
        for i in reversed(seleccion):
            items_seleccionados.pop(i)
            listbox_items.delete(i)
    tk.Button(frame_controles, text="Agregar archivo(s)", command=agregar_archivo).grid(row=0, column=1, padx=5)
    tk.Button(frame_controles, text="Agregar directorio", command=agregar_directorio).grid(row=0, column=2, padx=5)
    tk.Button(frame_controles, text="Eliminar seleccionado(s)", command=eliminar_item).grid(row=0, column=3, padx=5)
    # --- Carpeta destino ---
    frame_destino = tk.Frame(frame_principal)
    frame_destino.pack(fill="x", pady=(10, 0))
    tk.Label(frame_destino, text="Directorio destino:").grid(row=0, column=0, sticky="w", padx=(0, 10))
    entry_destino = tk.Entry(frame_destino, width=40)
    entry_destino.grid(row=0, column=1, padx=5)
    def seleccionar_destino():
        carpeta = filedialog.askdirectory()
        if carpeta:
            entry_destino.delete(0, tk.END)
            entry_destino.insert(0, carpeta)
    def crear_carpeta_destino():
        carpeta_base = entry_destino.get().strip() or filedialog.askdirectory(title="Selecciona carpeta base para crear nueva")
        if not carpeta_base:
            return
        nombre_nueva = simpledialog.askstring("Nueva carpeta", "Nombre de la nueva carpeta:")
        if not nombre_nueva:
            return
        nueva_ruta = os.path.join(carpeta_base, nombre_nueva)
        try:
            os.makedirs(nueva_ruta, exist_ok=True)
            entry_destino.delete(0, tk.END)
            entry_destino.insert(0, nueva_ruta)
            messagebox.showinfo("Éxito", f"Carpeta creada: {nueva_ruta}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear la carpeta: {e}")
    tk.Button(frame_destino, text="Explorar", command=seleccionar_destino).grid(row=0, column=2, padx=5)
    tk.Button(frame_destino, text="Crear nueva carpeta", command=crear_carpeta_destino).grid(row=0, column=3, padx=5)
    tk.Label(frame_destino, text="Nombre base:").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(5, 0))
    entry_nombre = tk.Entry(frame_destino, width=30)
    entry_nombre.grid(row=1, column=1, padx=5, pady=(5, 0))
    # --- Botón de unificación ---
    def ejecutar_unificacion():
        destino = entry_destino.get().strip()
        nombre_base = entry_nombre.get().strip()
        if not items_seleccionados or not destino or not nombre_base:
            messagebox.showerror("Error", "Debes seleccionar al menos un archivo/directorio, un destino y un nombre base.")
            return
        movimientos = unificar_archivos(items_seleccionados, destino, nombre_base)
        errores = [m for m in movimientos if "ERROR" in m[2]]
        if errores:
            messagebox.showwarning("Finalizado con errores", f"Se copiaron algunos archivos, pero hubo errores:\n{errores}")
        else:
            messagebox.showinfo("Éxito", f"Se unificaron {len(movimientos)} archivos en {destino}.")
    tk.Button(frame_destino, text="Unificar archivos/directorios seleccionados", command=ejecutar_unificacion).grid(row=2, column=1, pady=10)
    # --- Botón de deshacer ---
    def deshacer():
        destino = entry_destino.get().strip()
        if not destino:
            messagebox.showerror("Error", "Debes indicar el directorio destino para deshacer.")
            return
        ok, msg = deshacer_ultima_unificacion(destino)
        if ok:
            messagebox.showinfo("Deshacer", msg)
        else:
            messagebox.showerror("Deshacer", msg)
    tk.Button(frame_destino, text="Deshacer última unificación", command=deshacer).grid(row=2, column=2, pady=10, padx=10)
    if not parent:
        ventana_unificar.mainloop() 