import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QTextEdit, QMessageBox
)
from repetidas import encontrar_duplicados_por_nombre, mover_duplicados_a_backup, deshacer_borrado_repetidas

class RepetidasWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Escanear fotos repetidas por nombre")
        self.setGeometry(100, 100, 600, 400)
        layout = QVBoxLayout()

        self.label_dir = QLabel("Selecciona un directorio para buscar duplicados:")
        layout.addWidget(self.label_dir)

        self.btn_select = QPushButton("Seleccionar directorio")
        self.btn_select.clicked.connect(self.seleccionar_directorio)
        layout.addWidget(self.btn_select)

        self.btn_scan = QPushButton("Escanear duplicados")
        self.btn_scan.clicked.connect(self.escanear)
        self.btn_scan.setEnabled(False)
        layout.addWidget(self.btn_scan)

        self.textarea = QTextEdit()
        self.textarea.setReadOnly(True)
        layout.addWidget(self.textarea)

        self.btn_borrar = QPushButton("Eliminar duplicados")
        self.btn_borrar.clicked.connect(self.borrar)
        self.btn_borrar.setEnabled(False)
        layout.addWidget(self.btn_borrar)

        self.btn_deshacer = QPushButton("Deshacer borrado")
        self.btn_deshacer.clicked.connect(self.deshacer)
        self.btn_deshacer.setEnabled(False)
        layout.addWidget(self.btn_deshacer)

        self.directorio = None
        self.duplicados = []
        self.setLayout(layout)

    def seleccionar_directorio(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Selecciona un directorio")
        if carpeta:
            self.directorio = carpeta
            self.label_dir.setText(f"Directorio seleccionado: {carpeta}")
            self.btn_scan.setEnabled(True)
            self.textarea.clear()
            self.btn_borrar.setEnabled(False)
            self.btn_deshacer.setEnabled(self.hay_backup())

    def escanear(self):
        if not self.directorio:
            return
        self.duplicados = encontrar_duplicados_por_nombre(self.directorio)
        if self.duplicados:
            self.textarea.setPlainText("\n".join(self.duplicados))
            self.btn_borrar.setEnabled(True)
        else:
            self.textarea.setPlainText("No se encontraron archivos duplicados por nombre.")
            self.btn_borrar.setEnabled(False)
        self.btn_deshacer.setEnabled(self.hay_backup())

    def borrar(self):
        if not self.duplicados:
            return
        confirm = QMessageBox.question(self, "Confirmar borrado", f"¿Seguro que quieres mover {len(self.duplicados)} archivos duplicados a backup?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            backup_dir, registro = mover_duplicados_a_backup(self.duplicados, self.directorio)
            errores = [r for r in registro if r.get("error")]
            if errores:
                msg = "Algunos archivos no se pudieron mover:\n" + "\n".join(f"{r['origen']}: {r['error']}" for r in errores)
                QMessageBox.warning(self, "Errores al mover", msg)
            else:
                QMessageBox.information(self, "Éxito", f"Duplicados movidos a backup: {backup_dir}")
            self.escanear()

    def deshacer(self):
        if not self.directorio:
            return
        exito, mensaje = deshacer_borrado_repetidas(self.directorio)
        if exito:
            QMessageBox.information(self, "Éxito", mensaje)
        else:
            QMessageBox.warning(self, "Error", mensaje)
        self.escanear()

    def hay_backup(self):
        if not self.directorio:
            return False
        backup_file = os.path.join(self.directorio, "__backup_repetidas__", "backup_repetidas.json")
        return os.path.exists(backup_file)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RepetidasWindow()
    window.show()
    sys.exit(app.exec_()) 