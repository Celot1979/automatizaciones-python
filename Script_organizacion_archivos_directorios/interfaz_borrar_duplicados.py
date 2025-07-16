# interfaz_borrar_duplicados.py
import tkinter as tk
from tkinter import filedialog, messagebox
from logica_borrar_archivos_duplicados import buscar_duplicados, borrar_archivos, deshacer_borrado_duplicados
import os

def abrir_ventana_borrar_duplicados(parent=None):
    ventana = tk.Toplevel(parent) if parent else tk.Tk()
    ventana.title("Borrar archivos duplicados")
    ventana.geometry("700x500")
    tk.Label(ventana, text="Selecciona los directorios a escanear:").pack(anchor="w", padx=10, pady=5)
    frame_dirs = tk.Frame(ventana)
    frame_dirs.pack(fill="x", padx=10)
    listbox_dirs = tk.Listbox(frame_dirs, height=4)
    listbox_dirs.pack(side="left", fill="x", expand=True)
    dirs_seleccionados = []
    def agregar_directorio():
        carpeta = filedialog.askdirectory()
        if carpeta and carpeta not in dirs_seleccionados:
            dirs_seleccionados.append(carpeta)
            listbox_dirs.insert(tk.END, carpeta)
    def eliminar_directorio():
        seleccion = listbox_dirs.curselection()
        for i in reversed(seleccion):
            dirs_seleccionados.pop(i)
            listbox_dirs.delete(i)
    tk.Button(frame_dirs, text="Agregar directorio", command=agregar_directorio).pack(side="left", padx=5)
    tk.Button(frame_dirs, text="Eliminar directorio", command=eliminar_directorio).pack(side="left", padx=5)
    frame_resultados = tk.Frame(ventana)
    frame_resultados.pack(fill="both", expand=True, padx=10, pady=10)
    listbox_duplicados = tk.Listbox(frame_resultados, selectmode=tk.MULTIPLE)
    listbox_duplicados.pack(fill="both", expand=True)
    duplicados = {}
    def escanear():
        listbox_duplicados.delete(0, tk.END)
        if not dirs_seleccionados:
            messagebox.showerror("Error", "Selecciona al menos un directorio.")
            return
        nonlocal duplicados
        duplicados = buscar_duplicados(dirs_seleccionados)
        total = 0
        for original, copias in duplicados.items():
            for copia in copias:
                listbox_duplicados.insert(tk.END, f"{copia}")
                total += 1
        if total == 0:
            messagebox.showinfo("Sin duplicados", "No se encontraron archivos duplicados.")
    tk.Button(ventana, text="Escanear duplicados", command=escanear).pack(pady=5)
    def borrar_seleccionados():
        seleccion = listbox_duplicados.curselection()
        archivos_a_borrar = [listbox_duplicados.get(i) for i in seleccion]
        if not archivos_a_borrar:
            messagebox.showerror("Error", "Selecciona al menos un archivo para borrar.")
            return
        resultados = borrar_archivos(archivos_a_borrar)
        errores = [r for r in resultados if not r[1]]
        if errores:
            messagebox.showerror("Error", f"Errores al borrar: {errores}")
        else:
            messagebox.showinfo("Éxito", f"Se borraron {len(archivos_a_borrar)} archivos duplicados.")
        escanear()
    tk.Button(ventana, text="Borrar seleccionados", command=borrar_seleccionados).pack(pady=5)
    # --- Botón de deshacer ---
    def deshacer():
        if not dirs_seleccionados:
            messagebox.showerror("Error", "Selecciona al menos un directorio para deshacer.")
            return
        # Solo se permite deshacer en el primer directorio seleccionado
        ok, msg = deshacer_borrado_duplicados(dirs_seleccionados[0])
        if ok:
            messagebox.showinfo("Deshacer", msg)
        else:
            messagebox.showerror("Deshacer", msg)
        escanear()
    tk.Button(ventana, text="Deshacer último borrado", command=deshacer).pack(pady=5)
    if not parent:
        ventana.mainloop() 