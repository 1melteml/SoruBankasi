import sqlite3
import openpyxl
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QLineEdit,
    QHBoxLayout, QRadioButton, QTabWidget, QMessageBox, QComboBox, QListWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,QButtonGroup
)
from PyQt5.QtCore import Qt

# Veritabanı işlemleri ve şema güncellemesi
def veritabani_olustur():
    conn = sqlite3.connect("soru_bankasi.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Kategoriler (
            id INTEGER PRIMARY KEY,
            isim TEXT NOT NULL UNIQUE
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS Sorular (
            id INTEGER PRIMARY KEY,
            soru TEXT NOT NULL,
            sik1 TEXT NOT NULL,
            sik2 TEXT NOT NULL,
            sik3 TEXT NOT NULL,
            sik4 TEXT NOT NULL,
            dogru_cevap INTEGER NOT NULL
        )
        """
    )
    cursor.execute("PRAGMA table_info(Sorular)")
    cols = [row[1] for row in cursor.fetchall()]
    if 'category_id' not in cols:
        cursor.execute("ALTER TABLE Sorular ADD COLUMN category_id INTEGER")
    conn.commit()
    conn.close()

# Excel'e aktarım fonksiyonu
def sorulari_excel_aktar(parent=None):
    conn = sqlite3.connect("soru_bankasi.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT s.soru, s.sik1, s.sik2, s.sik3, s.sik4, s.dogru_cevap, COALESCE(k.isim, '-') "
        "FROM Sorular s LEFT JOIN Kategoriler k ON s.category_id = k.id"
    )
    sorular = cursor.fetchall()
    conn.close()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sorular"
    ws.append(["Soru", "A", "B", "C", "D", "Doğru", "Kategori"])
    for soru, a, b, c, d, dogru, kategori in sorular:
        ws.append([soru, a, b, c, d, chr(65 + dogru), kategori])
    wb.save("soru_bankasi_sorular.xlsx")
    QMessageBox.information(parent, "Excel'e Aktarma", "Sorular başarıyla dışa aktarıldı.")

# 1. Hoşgeldiniz sekmesi
class HosgeldinizTab(QWidget):
    def __init__(self, tabs):
        super().__init__()
        self.tabs = tabs
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.addWidget(QLabel("<b><span style='font-size:28pt;'>Soru Bankasına Hoşgeldiniz!</span></b>"), alignment=Qt.AlignCenter)
        layout.addWidget(QLabel("<b>Bilgiyle Güçlen, Sorularla Zirveye Çık!</b>"), alignment=Qt.AlignCenter)
        btn = QPushButton("Hemen Başla")
        btn.setFixedSize(150, 40)
        btn.setStyleSheet("background-color:#4CAF50;color:white;font-weight:bold;font-size:14pt;border-radius:8px;")
        btn.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        layout.addWidget(btn, alignment=Qt.AlignCenter)
        self.setLayout(layout)

# 2. Kategori Yönetimi sekmesi
class KategoriTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Kategori Yönetimi</b>"), alignment=Qt.AlignCenter)
        self.input = QLineEdit(); self.input.setPlaceholderText("Yeni kategori...")
        self.list = QListWidget()
        btn_add = QPushButton("Ekle"); btn_del = QPushButton("Sil")
        btn_add.clicked.connect(self.ekle); btn_del.clicked.connect(self.sil)
        layout.addWidget(self.input)
        layout.addWidget(btn_add)
        layout.addWidget(QLabel("Mevcut Kategoriler:"))
        layout.addWidget(self.list)
        layout.addWidget(btn_del)
        self.setLayout(layout)
        self.yukle()

    def yukle(self):
        self.list.clear()
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        cur.execute("SELECT isim FROM Kategoriler ORDER BY isim")
        for (isim,) in cur.fetchall():
            self.list.addItem(isim)
        conn.close()

    def ekle(self):
        isim = self.input.text().strip()
        if not isim:
            QMessageBox.warning(self, "Hata", "Boş kategori adı.")
            return
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO Kategoriler (isim) VALUES (?)", (isim,))
            conn.commit()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Hata", "Kategori zaten var.")
        conn.close()
        self.input.clear()
        self.yukle()

    def sil(self):
        item = self.list.currentItem()
        if not item:
            return
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        cur.execute("DELETE FROM Kategoriler WHERE isim=?", (item.text(),))
        conn.commit()
        conn.close()
        self.yukle()

# 3. Soru Ekleme sekmesi
class SoruEkleTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Soru Ekle</b>"), alignment=Qt.AlignCenter)
        self.soru_in = QLineEdit(); self.soru_in.setPlaceholderText("Soru metni..."); layout.addWidget(self.soru_in)
        self.siks = []; self.rads = []
        for i in range(4):
            h = QHBoxLayout()
            e = QLineEdit(); e.setPlaceholderText(f"Şık {i+1}")
            r = QRadioButton("Doğru")
            h.addWidget(e); h.addWidget(r)
            layout.addLayout(h)
            self.siks.append(e)
            self.rads.append(r)
        layout.addWidget(QLabel("Kategori:"))
        self.cat = QComboBox()
        layout.addWidget(self.cat)
        btn = QPushButton("Kaydet")
        btn.clicked.connect(self.kaydet)
        layout.addWidget(btn, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        self.yukle()

    def yukle(self):
        self.cat.clear()
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        cur.execute("SELECT id, isim FROM Kategoriler ORDER BY isim")
        for cid, isim in cur.fetchall():
            self.cat.addItem(isim, cid)
        conn.close()

    def kaydet(self):
        soru = self.soru_in.text().strip()
        siklar = [e.text().strip() for e in self.siks]
        dogru = next((i for i, r in enumerate(self.rads) if r.isChecked()), None)
        cid = self.cat.currentData()
        if not soru or not all(siklar) or dogru is None:
            QMessageBox.warning(self, "Hata", "Lütfen tüm alanları doldurun.")
            return
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO Sorular (soru,sik1,sik2,sik3,sik4,dogru_cevap,category_id) VALUES (?,?,?,?,?,?,?)",
            (soru, *siklar, dogru, cid)
        )
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Başarılı", "Soru eklendi.")
        self.soru_in.clear()
        for e in self.siks: e.clear()
        for r in self.rads: r.setChecked(False)

# 4. Soru Düzenleme sekmesi
class SoruDuzenleTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Soru Düzenle</b>"), alignment=Qt.AlignCenter)
        self.sel = QComboBox()
        layout.addWidget(self.sel)
        self.soru_in = QLineEdit()
        layout.addWidget(self.soru_in)
        self.siks = []
        self.rads = []
        for _ in range(4):
            h = QHBoxLayout()
            e = QLineEdit()
            r = QRadioButton("Doğru")
            h.addWidget(e); h.addWidget(r)
            layout.addLayout(h)
            self.siks.append(e)
            self.rads.append(r)
        layout.addWidget(QLabel("Kategori:"))
        self.cat = QComboBox()
        layout.addWidget(self.cat)
        btn = QPushButton("Güncelle")
        btn.clicked.connect(self.guncelle)
        layout.addWidget(btn, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        self.yukle_kat()
        self.yukle_sor()
        self.sel.currentIndexChanged.connect(self.doldur)

    def yukle_kat(self):
        self.cat.clear()
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        cur.execute("SELECT id, isim FROM Kategoriler ORDER BY isim")
        for cid, isim in cur.fetchall():
            self.cat.addItem(isim, cid)
        conn.close()

    def yukle_sor(self):
        self.sel.clear()
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        cur.execute("SELECT id, soru FROM Sorular")
        for sid, soru in cur.fetchall():
            self.sel.addItem(soru, sid)
        conn.close()

    def doldur(self):
        sid = self.sel.currentData()
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        cur.execute(
            "SELECT soru, sik1, sik2, sik3, sik4, dogru_cevap, category_id FROM Sorular WHERE id=?", (sid,)
        )
        data = cur.fetchone()
        conn.close()
        if data:
            soru, a, b, c, d, dogru, catid = data
            self.soru_in.setText(soru)
            for i, txt in enumerate((a, b, c, d)):
                self.siks[i].setText(txt)
                self.rads[i].setChecked(i == dogru)
            idx = self.cat.findData(catid)
            if idx >= 0:
                self.cat.setCurrentIndex(idx)

    def guncelle(self):
        sid = self.sel.currentData()
        soru = self.soru_in.text().strip()
        siklar = [e.text().strip() for e in self.siks]
        dogru = next((i for i, r in enumerate(self.rads) if r.isChecked()), None)
        catid = self.cat.currentData()
        if not soru or not all(siklar) or dogru is None:
            QMessageBox.warning(self, "Hata", "Lütfen tüm alanları doldurun.")
            return
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        cur.execute(
            "UPDATE Sorular SET soru=?, sik1=?, sik2=?, sik3=?, sik4=?, dogru_cevap=?, category_id=? WHERE id=?", 
            (soru, *siklar, dogru, catid, sid)
        )
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Başarılı", "Soru güncellendi.")
        self.yukle_sor()

# 5. Arama & Filtreleme sekmesi
class AramaTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Ara & Filtrele</b>"), alignment=Qt.AlignCenter)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Anahtar kelime...")
        self.search.textChanged.connect(self.load)
        self.filter = QComboBox()
        self.filter.currentIndexChanged.connect(self.load)
        hl = QHBoxLayout()
        hl.addWidget(self.search)
        hl.addWidget(self.filter)
        layout.addLayout(hl)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Soru", "Kategori", "Doğru"]) 
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.load_categories()
        self.load()

    def load_categories(self):
        self.filter.clear()
        self.filter.addItem("Tümü", None)
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        cur.execute("SELECT id, isim FROM Kategoriler ORDER BY isim")
        for cid, isim in cur.fetchall():
            self.filter.addItem(isim, cid)
        conn.close()

    def load(self):
        keyword = self.search.text().lower()
        cid = self.filter.currentData()
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        query = "SELECT s.id, s.soru, COALESCE(k.isim,'-'), s.dogru_cevap FROM Sorular s LEFT JOIN Kategoriler k ON s.category_id=k.id"
        conditions = []
        params = []
        if cid is not None:
            conditions.append("s.category_id=?"); params.append(cid)
        if keyword:
            conditions.append("LOWER(s.soru) LIKE ?"); params.append(f"%{keyword}%")
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        self.table.setRowCount(len(rows))
        for i, (id_, soru, kategori, dogru) in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(id_)))
            self.table.setItem(i, 1, QTableWidgetItem(soru))
            self.table.setItem(i, 2, QTableWidgetItem(kategori))
            self.table.setItem(i, 3, QTableWidgetItem(chr(65+dogru)))

# 6. Sınav Modu sekmesi
class SoruKontrolTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<b>Sınav Modu</b>"), alignment=Qt.AlignCenter)
        self.filter = QComboBox()
        self.filter.addItem("Tümü", None)
        layout.addWidget(self.filter)
        self.combo = QComboBox()
        layout.addWidget(self.combo)
        self.lbl = QLabel()
        self.lbl.setWordWrap(True)
        layout.addWidget(self.lbl)
        self.rads = [QRadioButton() for _ in range(4)]
        for r in self.rads:
            layout.addWidget(r)
        btn = QPushButton("Kontrol Et")
        btn.clicked.connect(self.kontrol)
        layout.addWidget(btn, alignment=Qt.AlignCenter)
        self.setLayout(layout)
        self.load_categories()
        self.filter.currentIndexChanged.connect(self.load_questions)
        self.load_questions()

    def load_categories(self):
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        cur.execute("SELECT id, isim FROM Kategoriler ORDER BY isim")
        for cid, isim in cur.fetchall():
            self.filter.addItem(isim, cid)
        conn.close()

    def load_questions(self):
        self.combo.clear()
        cid = self.filter.currentData()
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        if cid:
            cur.execute("SELECT id, soru FROM Sorular WHERE category_id=?", (cid,))
        else:
            cur.execute("SELECT id, soru FROM Sorular")
        for sid, soru in cur.fetchall():
            self.combo.addItem(soru, sid)
        conn.close()
        self.load_question()

    def load_question(self):
        sid = self.combo.currentData()
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        cur.execute(
            "SELECT soru, sik1, sik2, sik3, sik4, dogru_cevap FROM Sorular WHERE id=?", (sid,)
        )
        data = cur.fetchone()
        conn.close()
        if data:
            soru, a, b, c, d, dogru = data
            self.lbl.setText(soru)
            for i, txt in enumerate((a, b, c, d)):
                self.rads[i].setText(txt)
                self.rads[i].setChecked(False)
            self.correct = dogru

    def kontrol(self):
        idx = next((i for i, r in enumerate(self.rads) if r.isChecked()), None)
        if idx is None:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir şık seçin.")
            return
        if idx == self.correct:
            QMessageBox.information(self, "Sonuç", "Doğru!")
        else:
            QMessageBox.information(self, "Sonuç", f"Yanlış! Doğru şık: {chr(65+self.correct)}")

# 7. Zamanlı Sınav sekmesi
from PyQt5.QtCore import QTimer

class ZamanliSinavTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

    def init_ui(self):
        layout = QVBoxLayout()

        self.timer_label = QLabel("Süre: 00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.timer_label)

        self.score_label = QLabel("")
        self.score_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.score_label)

        self.count_spin = QComboBox()
        self.count_spin.addItems(["5", "10", "15", "20"])
        self.count_spin.setCurrentIndex(1)
        layout.addWidget(QLabel("Soru Sayısı"))
        layout.addWidget(self.count_spin)

        self.duration_spin = QComboBox()
        self.duration_spin.addItems(["60", "120", "180", "300"])
        layout.addWidget(QLabel("Süre (saniye cinsinden)"))
        layout.addWidget(self.duration_spin)

        self.start_btn = QPushButton("Sınavı Başlat")
        self.start_btn.clicked.connect(self.start_quiz)
        layout.addWidget(self.start_btn)

        self.question_label = QLabel("")
        self.question_label.setWordWrap(True)
        layout.addWidget(self.question_label)

        self.option_rads = []
        self.option_group = QButtonGroup()
        for i in range(4):
            rad = QRadioButton()
            self.option_group.addButton(rad, i)
            self.option_rads.append(rad)
            layout.addWidget(rad)

        self.next_btn = QPushButton("Sonraki")
        self.next_btn.clicked.connect(self.next_question)
        self.next_btn.setEnabled(False)
        layout.addWidget(self.next_btn)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Soru metni içinde ara...")
        self.search_input.textChanged.connect(self.filter_questions)
        layout.addWidget(self.search_input)

        self.category_filter = QComboBox()
        self.category_filter.addItem("Tüm Kategoriler", userData=None)
        self.yukle_kategoriler()
        self.category_filter.currentIndexChanged.connect(self.filter_questions)
        layout.addWidget(QLabel("Kategoriye Göre Filtrele"))
        layout.addWidget(self.category_filter)

        self.sonuc_tablosu = QTableWidget()
        self.sonuc_tablosu.setColumnCount(3)
        self.sonuc_tablosu.setHorizontalHeaderLabels(["Soru", "Verilen Cevap", "Doğru Cevap"])
        self.sonuc_tablosu.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.sonuc_tablosu)

        self.setLayout(layout)

    def yukle_kategoriler(self):
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        cur.execute("SELECT id, isim FROM Kategoriler")
        kategoriler = cur.fetchall()
        for kid, isim in kategoriler:
            self.category_filter.addItem(isim, userData=kid)
        conn.close()

    def start_quiz(self):
        cnt = int(self.count_spin.currentText())
        dur = int(self.duration_spin.currentText())
        self.category = self.category_filter.currentData()
        search_text = self.search_input.text().strip().lower()

        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()

        query = "SELECT id FROM Sorular WHERE 1=1"
        params = []

        if self.category is not None:
            query += " AND category_id = ?"
            params.append(self.category)

        if search_text:
            query += " AND LOWER(soru) LIKE ?"
            params.append(f"%{search_text}%")

        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(cnt)

        cur.execute(query, params)
        self.sorular = [row[0] for row in cur.fetchall()]
        conn.close()

        if not self.sorular:
            QMessageBox.warning(self, "Sınav Başlatılamadı", "Seçilen filtrelere uygun yeterli sayıda soru bulunamadı.")
            return

        self.current = 0
        self.score = 0
        self.kullanici_cevaplari = []
        self.time_left = dur
        self.start_btn.setEnabled(False)
        self.next_btn.setEnabled(True)
        self.score_label.setText("")
        self.sonuc_tablosu.setRowCount(0)
        self.load_question()
        self.timer.start(1000)

    def update_timer(self):
        self.time_left -= 1
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.timer_label.setText(f"Süre: {minutes:02}:{seconds:02}")
        if self.time_left <= 0:
            self.timer.stop()
            QMessageBox.information(self, "Süre Doldu", "Süre sona erdi! Sınav bitiriliyor.")
            self.finish_quiz()

    def load_question(self):
        if self.current >= len(self.sorular):
            self.finish_quiz()
            return
        sid = self.sorular[self.current]
        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()
        cur.execute("SELECT soru, sik1, sik2, sik3, sik4, dogru_cevap FROM Sorular WHERE id=?", (sid,))
        self.soru_metni, a, b, c, d, self.correct = cur.fetchone()
        conn.close()
        self.question_label.setText(f"{self.current + 1}. Soru: {self.soru_metni}")
        for i, txt in enumerate((a, b, c, d)):
            self.option_rads[i].setText(txt)
            self.option_rads[i].setChecked(False)

    def next_question(self):
        selected = next((i for i, r in enumerate(self.option_rads) if r.isChecked()), None)
        if selected is None:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir şık seçin.")
            return
        self.kullanici_cevaplari.append((self.soru_metni, selected, self.correct))
        if selected == self.correct:
            self.score += 1
        self.current += 1
        if self.current < len(self.sorular):
            self.load_question()
        else:
            self.timer.stop()
            self.finish_quiz()

    def finish_quiz(self):
        dakika = int(self.duration_spin.currentText()) // 60
        saniye = int(self.duration_spin.currentText()) % 60
        QMessageBox.information(
            self, "Sınav Bitti",
            f"{len(self.sorular)} sorudan {self.score} doğru!\nToplam Süre: {dakika} dk {saniye} sn"
        )
        self.score_label.setText(f"Puan: {self.score} / {len(self.sorular)}")
        self.start_btn.setEnabled(True)
        self.next_btn.setEnabled(False)
        self.question_label.setText("")
        for r in self.option_rads:
            r.setText("")
            r.setChecked(False)
        self.timer_label.setText("Süre: 00:00")

        # Sonuçları tabloya yaz
        self.sonuc_tablosu.setRowCount(len(self.kullanici_cevaplari))
        for i, (soru, verilen, dogru) in enumerate(self.kullanici_cevaplari):
            self.sonuc_tablosu.setItem(i, 0, QTableWidgetItem(soru))
            verilen_cevap = QTableWidgetItem(chr(65 + verilen))
            dogru_cevap = QTableWidgetItem(chr(65 + dogru))

            if verilen == dogru:
                verilen_cevap.setForeground(Qt.green)
                dogru_cevap.setForeground(Qt.green)
            else:
                verilen_cevap.setForeground(Qt.red)
                dogru_cevap.setForeground(Qt.darkGreen)

            self.sonuc_tablosu.setItem(i, 1, verilen_cevap)
            self.sonuc_tablosu.setItem(i, 2, dogru_cevap)

    def filter_questions(self):
        search_text = self.search_input.text().strip().lower()
        category_id = self.category_filter.currentData()

        conn = sqlite3.connect("soru_bankasi.db")
        cur = conn.cursor()

        query = "SELECT COUNT(*) FROM Sorular WHERE 1=1"
        params = []

        if category_id is not None:
            query += " AND category_id = ?"
            params.append(category_id)

        if search_text:
            query += " AND LOWER(soru) LIKE ?"
            params.append(f"%{search_text}%")

        cur.execute(query, params)
        count = cur.fetchone()[0]
        conn.close()

        self.timer_label.setText(f"Eşleşen Soru Sayısı: {count}")

# 8. Excel Aktar sekmesi
class ExcelTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        btn = QPushButton("Soruları Excel'e Aktar")
        btn.clicked.connect(lambda: sorulari_excel_aktar(self))
        layout.addWidget(btn, alignment=Qt.AlignCenter)
        self.setLayout(layout)

# Ana uygulama penceresi

def main():
    veritabani_olustur()
    app = QApplication([])
    
    app.setStyleSheet("""
    QWidget {
        background-color: #0b0c2a;
        color: white;
        font-family: Arial;
        font-size: 12pt;
    }
    QPushButton {
        background-color: #1e90ff;
        color: white;
        border-radius: 6px;
        padding: 6px 12px;
    }
    QPushButton:hover {
        background-color: #4682b4;
    }
    QLineEdit, QComboBox, QListWidget, QTableWidget, QTableWidget QHeaderView::section {
        background-color: #1a1a2e;
        color: white;
        border: 1px solid #555;
        selection-background-color: #34495e;
        selection-color: white;
    }
    QTableWidget QHeaderView::section {
        background-color: #2c3e50;
        color: white;
        font-weight: bold;
    }
    QRadioButton, QLabel {
        color: white;
    }
    QTabWidget::pane {
        border: 1px solid #444;
    }
    QTabBar::tab {
        background: #1a1a2e;
        color: white;
        padding: 10px;
    }
    QTabBar::tab:selected {
        background: #1e90ff;
        font-weight: bold;
    }
""")


    window = QWidget()
    window.setWindowTitle("Soru Bankası Uygulaması")
    tabs = QTabWidget()
    tabs.addTab(HosgeldinizTab(tabs), "Hoşgeldiniz")
    tabs.addTab(KategoriTab(), "Kategoriler")
    tabs.addTab(SoruEkleTab(), "Soru Ekle")
    tabs.addTab(SoruDuzenleTab(), "Düzenle")
    tabs.addTab(AramaTab(), "Ara & Filtrele")
    tabs.addTab(SoruKontrolTab(), "Sınav Modu")
    tabs.addTab(ExcelTab(), "Excel Aktar")
    tabs.addTab(ZamanliSinavTab(), "Zamanlı Sınav")

    
    main_layout = QVBoxLayout()
    main_layout.addWidget(tabs)
    window.setLayout(main_layout)
    window.resize(800, 600)
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()
