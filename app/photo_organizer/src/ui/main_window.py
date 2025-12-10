import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QProgressBar,
    QRadioButton,
    QButtonGroup,
    QMessageBox,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QStackedWidget,
    QGroupBox,
    QFrame
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QSize
from PySide6.QtGui import QIcon, QFont
from ..core.scanner import Scanner
from ..core.organizer import OrganizerEngine
from ..data.database import SessionDatabase
from .styles import DARK_THEME

class WorkerThread(QThread):
    progress = Signal(str)
    progress_int = Signal(int, int)
    finished = Signal()

    def __init__(self, task_func, *args):
        super().__init__()
        self.task_func = task_func
        self.args = args

    def run(self):
        self.task_func(*self.args, self)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Organizer Foto Pro")
        self.resize(1100, 800)
        
        # Init Backend
        self.db = SessionDatabase("session.db")
        self.scanner = Scanner(self.db)
        self.organizer = OrganizerEngine(self.db)
        
        # Main Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        self.layout.addWidget(self.stack)
        
        # Init Pages
        self.init_page_selection()
        self.init_page_preview()
        self.init_page_progress()

        # Apply Status Bar
        self.statusBar().showMessage("Pronto")
        
    def init_page_selection(self):
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # Header
        lbl_title = QLabel("Configurazione Riordino")
        lbl_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #3d8ec9; margin-bottom: 10px;")
        main_layout.addWidget(lbl_title)
        
        # 1. Source Selection Group
        group_source = QGroupBox("1. Sorgenti")
        layout_source = QVBoxLayout(group_source)
        
        self.source_list = QTreeWidget()
        self.source_list.setHeaderLabels(["Percorso Cartella"])
        self.source_list.setRootIsDecorated(False)
        layout_source.addWidget(self.source_list)
        
        btn_add = QPushButton("Aggiungi Cartella")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self.add_source_folder)
        layout_source.addWidget(btn_add, alignment=Qt.AlignRight)
        
        main_layout.addWidget(group_source)
        
        # 2. Options Group
        group_opts = QGroupBox("2. Opzioni")
        layout_opts = QVBoxLayout(group_opts)
        
        self.radio_date = QRadioButton("Struttura Cronologica Standard (Es: 2023/08/15/foto.jpg)")
        self.radio_type = QRadioButton("Dividi per Tipo (Es: Foto/2023/... e Video/2023/...)")
        self.radio_date.setChecked(True)
        
        layout_opts.addWidget(self.radio_date)
        layout_opts.addWidget(self.radio_type)
        main_layout.addWidget(group_opts)
        
        # 3. Destination Group
        group_dest = QGroupBox("3. Destinazione")
        layout_dest = QHBoxLayout(group_dest)
        
        self.lbl_dest = QLabel("Nessuna cartella selezionata")
        self.lbl_dest.setStyleSheet("color: #888; font-style: italic;")
        layout_dest.addWidget(self.lbl_dest, stretch=1)
        
        btn_dest = QPushButton("Seleziona Cartella")
        btn_dest.setCursor(Qt.PointingHandCursor)
        btn_dest.clicked.connect(self.select_dest_folder)
        layout_dest.addWidget(btn_dest)
        
        main_layout.addWidget(group_dest)
        
        # Action Button
        main_layout.addStretch()
        self.btn_analyze = QPushButton("ANALIZZA FILE")
        self.btn_analyze.setObjectName("primary")
        self.btn_analyze.setMinimumHeight(50)
        self.btn_analyze.setCursor(Qt.PointingHandCursor)
        self.btn_analyze.clicked.connect(self.start_scan)
        self.btn_analyze.setEnabled(False)
        main_layout.addWidget(self.btn_analyze)
        
        self.stack.addWidget(page)

    def init_page_preview(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header = QHBoxLayout()
        lbl_title = QLabel("Anteprima & Conferma")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(lbl_title)
        
        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet("color: #aaa;")
        header.addWidget(self.lbl_stats, alignment=Qt.AlignRight)
        layout.addLayout(header)
        
        # Table
        self.table_preview = QTableWidget()
        self.table_preview.setColumnCount(4)
        self.table_preview.setHorizontalHeaderLabels(["File Originale", "Data Rilevata", "Destinazione Proposta", "Stato"])
        self.table_preview.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_preview.setAlternatingRowColors(True)
        layout.addWidget(self.table_preview)
        
        # Action Bar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        btn_back = QPushButton("Indietro")
        btn_back.setMinimumHeight(45)
        btn_back.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        
        self.btn_run = QPushButton("AVVIA TRASFERIMENTO")
        self.btn_run.setObjectName("success")
        self.btn_run.setMinimumHeight(45)
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.clicked.connect(self.start_execution)
        
        btn_layout.addWidget(btn_back, stretch=1)
        btn_layout.addWidget(self.btn_run, stretch=2)
        layout.addLayout(btn_layout)
        
        self.stack.addWidget(page)

    def init_page_progress(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 60, 40, 40)
        layout.setSpacing(20)
        
        lbl_title = QLabel("Elaborazione in corso...")
        lbl_title.setStyleSheet("font-size: 22px; margin-bottom: 20px;")
        layout.addWidget(lbl_title, alignment=Qt.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("%p% - %v/%m File")
        layout.addWidget(self.progress_bar)
        
        self.log_view = QTreeWidget()
        self.log_view.setHeaderLabels(["Dettagli Operazioni"])
        self.log_view.setRootIsDecorated(False)
        layout.addWidget(self.log_view)
        
        self.btn_finish = QPushButton("Nuova Scansione")
        self.btn_finish.setObjectName("primary")
        self.btn_finish.setMinimumHeight(45)
        self.btn_finish.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_finish.setVisible(False)
        layout.addWidget(self.btn_finish)
        
        self.stack.addWidget(page)

    # ---

    def add_source_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Seleziona Cartella Sorgente")
        if dir_path:
            item = QTreeWidgetItem([dir_path])
            item.setIcon(0, QIcon.fromTheme("folder"))
            self.source_list.addTopLevelItem(item)
            self.check_ready()

    def select_dest_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Seleziona Cartella Destinazione")
        if dir_path:
            self.lbl_dest.setText(dir_path)
            self.lbl_dest.setStyleSheet("color: #4caf50; font-weight: bold;")
            self.check_ready()

    def check_ready(self):
        has_source = self.source_list.topLevelItemCount() > 0
        has_dest = self.lbl_dest.text() != "Nessuna selezionata" and self.lbl_dest.text() != "Nessuna cartella selezionata"
        self.btn_analyze.setEnabled(has_source and has_dest)

    def start_scan(self):
        self.stack.setCurrentIndex(2) # Go to progress for scanning
        self.log_view.clear()
        self.add_log("Inizio scansione...", "INFO")
        
        # Collect sources
        sources = []
        for i in range(self.source_list.topLevelItemCount()):
            sources.append(self.source_list.topLevelItem(i).text(0))
            
        self.worker = WorkerThread(self.run_scan_process, sources)
        self.worker.progress.connect(lambda s: self.add_log(s))
        self.worker.finished.connect(self.on_scan_finished)
        self.worker.start()

    def run_scan_process(self, sources, thread_context):
        for src in sources:
            self.scanner.scan_path(src, lambda f: thread_context.progress.emit(f"Scan: {f}"))
        
        # Calc destinations
        thread_context.progress.emit("Calcolo destinazioni in corso...")
        mode = OrganizerEngine.MODE_DATE_TREE if self.radio_date.isChecked() else OrganizerEngine.MODE_TYPE_DATE
        dest_path = self.lbl_dest.text()
        self.organizer.calculate_destinations(dest_path, mode)

    def on_scan_finished(self):
        self.add_log("Scansione completata.", "SUCCESS")
        self.load_preview()
        self.stack.setCurrentIndex(1) # Go to preview

    def load_preview(self):
        files = self.db.get_all_files()
        self.table_preview.setRowCount(len(files))
        
        # Update Stats
        total_size = sum(f['size'] for f in files)
        size_gb = total_size / (1024**3)
        self.lbl_stats.setText(f"File trovati: {len(files)} | Dimensione Totale: {size_gb:.2f} GB")
        
        status_map = {
            'pending': 'In attesa',
            'skipped': 'Saltato',
            'copied': 'Copiato',
            'verified': 'Verificato',
            'moved': 'Spostato',
            'error': 'Errore'
        }
        
        for i, row in enumerate(files):
            self.table_preview.setItem(i, 0, QTableWidgetItem(row['file_name']))
            self.table_preview.setItem(i, 1, QTableWidgetItem(row['date_taken']))
            self.table_preview.setItem(i, 2, QTableWidgetItem(row['dest_path']))
            
            raw_status = row['status']
            status_text = status_map.get(raw_status, raw_status)
            item_status = QTableWidgetItem(status_text)
            
            # Color code status
            if raw_status == 'error':
                 item_status.setForeground(Qt.red)
            elif raw_status == 'verified':
                item_status.setForeground(Qt.green)
                
            self.table_preview.setItem(i, 3, item_status)

    def start_execution(self):
        self.stack.setCurrentIndex(2)
        self.add_log("Avvio trasferimento...", "INFO")
        self.progress_bar.setValue(0)
        
        self.worker_exec = WorkerThread(self.run_execution_process)
        self.worker_exec.progress_int.connect(self.update_progress)
        self.worker_exec.finished.connect(self.on_execution_finished)
        self.worker_exec.start()

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def run_execution_process(self, thread_context):
        def progress(current, total):
            thread_context.progress_int.emit(current, total)
            
        try:
            self.organizer.execute_transfer(delete_source=False, progress_callback=progress)
        except Exception as e:
            print(f"Execution Error: {e}")

    def on_execution_finished(self):
        self.add_log("Trasferimento completato. Verifica in corso...", "INFO")
        
        # Run Verification
        try:
            report = self.organizer.verify_migration()
            self.add_log(f"Verifica completata: {report['success']} OK, {report['corrupted']} Corrotti", "SUCCESS")
        except Exception as e:
             self.add_log(f"Errore verifica: {e}", "ERROR")
             report = {'total': 0, 'success': 0, 'missing': 0, 'corrupted': 0}
        
        # Refresh table to show final statuses
        # We don't go back to preview automatically, but user can start over
        
        msg = (f"Operazione Completata!\n\n"
               f"Totale File: {report['total']}\n"
               f"Trasferiti con Successo: {report['success']}\n"
               f"Mancanti/Saltati: {report['missing']}\n"
               f"Corrotti: {report['corrupted']}")
               
        QMessageBox.information(self, "Report Finale", msg)
        self.btn_finish.setVisible(True)

    def add_log(self, text, level="INFO"):
        item = QTreeWidgetItem([f"[{level}] {text}"])
        if level == "ERROR":
            item.setForeground(0, Qt.red)
        elif level == "SUCCESS":
            item.setForeground(0, Qt.green)
        self.log_view.addTopLevelItem(item)
        self.log_view.scrollToBottom()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Apply Standard Font
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    # Apply Dark Theme
    app.setStyleSheet(DARK_THEME)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
