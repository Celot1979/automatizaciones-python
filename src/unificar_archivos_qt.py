import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import shutil
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton, QFileDialog,
    QLineEdit, QHBoxLayout, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt
from unificar_archivos import unificar_archivos, rehacer_unificacion

class DropListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.ExtendedSelection)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():  # type: ignore
            event.setDropAction(Qt.CopyAction)  # type: ignore
            event.accept()  # type: ignore
        else:
            event.ignore()  # type: ignore

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():  # type: ignore
            event.setDropAction(Qt.CopyAction)  # type: ignore
            event.accept()  # type: ignore
        else:
            event.ignore()  # type: ignore

    def dropEvent(self, event):
        if event.mimeData().hasUrls():  # type: ignore
            event.setDropAction(Qt.CopyAction)  # type: ignore
            event.accept()  # type: ignore
            for url in event.mimeData().urls():  # type: ignore
                path = url.toLocalFile()  # type: ignore
                if os.path.isfile(path):
                    if not self.findItems(path, Qt.MatchExactly):  # type: ignore
                        self.addItem(path)
                elif os.path.isdir(path):
                    for root, _, files in os.walk(path):
                        for f in files:
                            full_path = os.path.join(root, f)
                            if not self.findItems(full_path, Qt.MatchExactly):  # type: ignore
                                self.addItem(full_path)
        else:
            event.ignore()  # type: ignore

class UnificarArchivosWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unificar archivos (selección práctica)")
        self.setGeometry(100, 100, 700, 650)
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Selecciona archivos y carpetas para unificar:"))
        btns_layout = QHBoxLayout()
        btn_add_files = QPushButton("Añadir archivos")
        btn_add_files.clicked.connect(self.anadir_archivos)
        btns_layout.addWidget(btn_add_files)
        btn_add_folder = QPushButton("Añadir carpeta")
        btn_add_folder.clicked.connect(self.anadir_carpeta)
        btns_layout.addWidget(btn_add_folder)
        layout.addLayout(btns_layout)

        self.drop_list = DropListWidget()
        layout.addWidget(self.drop_list)

        btn_quitar = QPushButton("Quitar seleccionado(s)")
        btn_quitar.clicked.connect(self.quitar_seleccionados)
        layout.addWidget(btn_quitar)

        layout.addWidget(QLabel("Carpeta de destino:"))
        dest_layout = QHBoxLayout()
        self.dest_entry = QLineEdit()
        dest_layout.addWidget(self.dest_entry)
        btn_dest = QPushButton("Seleccionar carpeta")
        btn_dest.clicked.connect(self.seleccionar_destino)
        dest_layout.addWidget(btn_dest)
        # Eliminar el botón de crear nueva carpeta
        layout.addLayout(dest_layout)

        layout.addWidget(QLabel("Nombre de la nueva carpeta de unificación:"))
        self.nombre_carpeta = QLineEdit()
        layout.addWidget(self.nombre_carpeta)

        layout.addWidget(QLabel("Nombre base para los archivos unificados:"))
        self.nombre_base = QLineEdit()
        layout.addWidget(self.nombre_base)

        btn_unificar = QPushButton("Unificar archivos")
        btn_unificar.clicked.connect(self.unificar)
        layout.addWidget(btn_unificar)

        btn_rehacer = QPushButton("Rehacer el proceso")
        btn_rehacer.clicked.connect(self.rehacer)
        layout.addWidget(btn_rehacer)

        self.setLayout(layout)

    def anadir_archivos(self):
        archivos, _ = QFileDialog.getOpenFileNames(self, "Selecciona archivos para unificar")
        for path in archivos:
            if not self.drop_list.findItems(path, Qt.MatchExactly):  # type: ignore
                self.drop_list.addItem(path)

    def anadir_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Selecciona una carpeta para unificar")
        if carpeta:
            for root, _, files in os.walk(carpeta):
                for f in files:
                    full_path = os.path.join(root, f)
                    if not self.drop_list.findItems(full_path, Qt.MatchExactly):  # type: ignore
                        self.drop_list.addItem(full_path)

    def quitar_seleccionados(self):
        for item in self.drop_list.selectedItems():
            self.drop_list.takeItem(self.drop_list.row(item))

    def seleccionar_destino(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Selecciona la carpeta de destino")
        if carpeta:
            self.dest_entry.setText(carpeta)

    def crear_nueva_carpeta(self):
        base = QFileDialog.getExistingDirectory(self, "Selecciona la ubicación para la nueva carpeta")
        if base:
            nombre, ok = QInputDialog.getText(self, "Nombre de la carpeta", "Introduce el nombre de la nueva carpeta:")
            if ok and nombre:
                nueva = os.path.join(base, nombre)
                try:
                    os.makedirs(nueva, exist_ok=False)
                    self.dest_entry.setText(nueva)
                    QMessageBox.information(self, "Éxito", f"Carpeta creada: {nueva}")
                except FileExistsError:
                    QMessageBox.warning(self, "Error", "La carpeta ya existe.")
                except Exception as e:
                    QMessageBox.warning(self, "Error", str(e))

    def unificar(self):
        archivos = []
        for i in range(self.drop_list.count()):
            item = self.drop_list.item(i)
            if item is not None:
                archivos.append(item.text())
        if not archivos:
            QMessageBox.warning(self, "Error", "Selecciona archivos o carpetas para unificar.")
            return
        carpeta_destino = self.dest_entry.text().strip()
        if not carpeta_destino:
            QMessageBox.warning(self, "Error", "Selecciona la carpeta de destino.")
            return
        nombre_carpeta = self.nombre_carpeta.text().strip()
        if not nombre_carpeta:
            QMessageBox.warning(self, "Error", "Introduce el nombre de la nueva carpeta.")
            return
        nombre_base = self.nombre_base.text().strip()
        if not nombre_base:
            QMessageBox.warning(self, "Error", "Introduce el nombre base para los archivos.")
            return
        archivos_a_unificar = [(os.path.dirname(ruta), os.path.basename(ruta)) for ruta in archivos]
        # Mensaje de depuración
        debug_msg = f"Archivos a unificar ({len(archivos_a_unificar)}):\n" + "\n".join([os.path.join(d, f) for d, f in archivos_a_unificar])
        QMessageBox.information(self, "Depuración", debug_msg)
        try:
            ruta_unificacion, backup = unificar_archivos(archivos_a_unificar, carpeta_destino, nombre_carpeta, nombre_base)
            QMessageBox.information(self, "Éxito", f"Archivos unificados en: {ruta_unificacion}")
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            QMessageBox.warning(self, "Error", f"{str(e)}\n\n{tb}")

    def rehacer(self):
        carpeta_destino = self.dest_entry.text().strip()
        nombre_carpeta = self.nombre_carpeta.text().strip()
        if not carpeta_destino or not nombre_carpeta:
            QMessageBox.warning(self, "Error", "Debes indicar la carpeta de destino y el nombre de la carpeta de unificación.")
            return
        ruta_unificacion = os.path.join(carpeta_destino, nombre_carpeta)
        exito, mensaje = rehacer_unificacion(ruta_unificacion)
        if exito:
            QMessageBox.information(self, "Éxito", mensaje)
        else:
            QMessageBox.warning(self, "Error", mensaje)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = UnificarArchivosWindow()
    window.show()
    sys.exit(app.exec_()) 