import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

# Diccionario que mapea extensiones a carpetas
EXTENSIONES_A_CARPETAS = {
    "Imágenes": [".jpg", ".jpeg", ".png", ".bmp", ".heif"],
    "PDFs": [".pdf"],
    "Vídeos": [".mp4", ".mov", ".avi"],
    "Documentos": [".doc", ".xls", ".xlsx"],
    "Documentos_txt": [".txt"],
    "Documentos_docx": [".docx"]
}

class OrganizadorArchivosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Organizador de Archivos")
        self.ruta = tk.StringVar()
        self.check_vars = {tipo: tk.BooleanVar(value=True) for tipo in EXTENSIONES_A_CARPETAS}
        self._crear_widgets()

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

    def seleccionar_carpeta(self):
        carpeta = filedialog.askdirectory()
        if carpeta:
            self.ruta.set(carpeta)

    def organizar(self):
        ruta = self.ruta.get()
        if not ruta:
            messagebox.showerror("Error", "Por favor selecciona una carpeta.")
            return
        # Filtrar los tipos seleccionados
        tipos_seleccionados = {k: v for k, v in EXTENSIONES_A_CARPETAS.items() if self.check_vars[k].get()}
        if not tipos_seleccionados:
            messagebox.showerror("Error", "Selecciona al menos un tipo de archivo.")
            return
        # Crear carpetas de destino
        for carpeta in tipos_seleccionados.keys():
            ruta_carpeta = os.path.join(ruta, carpeta)
            if not os.path.exists(ruta_carpeta):
                os.makedirs(ruta_carpeta)
        # Crear carpeta para no clasificados
        carpeta_no_clasificados = "No clasificados"
        ruta_no_clasificados = os.path.join(ruta, carpeta_no_clasificados)
        if not os.path.exists(ruta_no_clasificados):
            os.makedirs(ruta_no_clasificados)
        # Recorrer archivos
        for archivo in os.listdir(ruta):
            ruta_archivo = os.path.join(ruta, archivo)
            if os.path.isdir(ruta_archivo):
                continue
            _, extension = os.path.splitext(archivo)
            extension = extension.lower()
            movido = False
            for carpeta, extensiones in tipos_seleccionados.items():
                if extension in extensiones:
                    destino = self._obtener_nombre_disponible(os.path.join(ruta, carpeta), archivo)
                    try:
                        shutil.move(ruta_archivo, destino)
                    except Exception as e:
                        print(f"Error al mover {archivo}: {e}")
                    movido = True
                    break
            if not movido:
                destino = self._obtener_nombre_disponible(ruta_no_clasificados, archivo)
                try:
                    shutil.move(ruta_archivo, destino)
                except Exception as e:
                    print(f"Error al mover {archivo} a 'No clasificados': {e}")
        messagebox.showinfo("Éxito", "Operación realizada con éxito")

if __name__ == "__main__":
    root = tk.Tk()
    app = OrganizadorArchivosApp(root)
    root.mainloop() 