# interfaz_renombrar.py
import tkinter as tk
from tkinter import filedialog, messagebox
from logica_renombrar import renombrar_archivos_en_masa

def abrir_ventana_renombrar(parent=None):
    ventana_renombrar = tk.Toplevel(parent) if parent else tk.Tk()
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
        resultados = renombrar_archivos_en_masa(dir_base, nombre_base)
        errores = [r for r in resultados if r[1] is None]
        if errores:
            messagebox.showerror("Error", f"Errores al renombrar: {errores}")
        else:
            messagebox.showinfo("Éxito", f"Se renombraron {len(resultados)} archivos.")
        ventana_renombrar.destroy()
    tk.Button(ventana_renombrar, text="Renombrar", command=ejecutar_renombrado).grid(row=2, column=1, pady=10)
    if not parent:
        ventana_renombrar.mainloop() 