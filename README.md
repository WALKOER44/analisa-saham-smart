# Analisa Saham Smart — Panduan Instalasi & Penggunaan

Sistem AI analisa 20 saham unggulan Indonesia secara real-time dengan web dashboard dan otomatisasi penuh.

---

## 1. Prasyarat (Requirements)
- **Python 3.8+** (pastikan sudah terinstal di komputer)
- Sistem Operasi: **Windows**

---

## 2. Cara Instalasi (Installation)
Buka Command Prompt (CMD) atau PowerShell di folder project:

```bash
cd "d:\LOCAL DISK D\MY PROJECT\ai_saham_bot"
pip install -r requirements.txt
```

---

## 3. Cara Menjalankan (Usage)

Cukup jalankan **1 file batch** untuk menghidupkan seluruh sistem:

```cmd
start_all.bat
```

**Apa yang terjadi saat dijalankan:**
1. **Server Flask** (web dashboard) otomatis berjalan di latar belakang (minimize agar layar tidak penuh).
2. **Analysis Engine** otomatis berjalan di latar belakang untuk memantau pasar.
3. Browser secara otomatis membuka **`http://localhost:5000`**.

Untuk menutup sistem, cukup tutup jendela command prompt server atau engine yang berjalan di background.

---

## 4. Fitur Utama
- **TOP 3 Rekomendasi**: Rekomendasi saham terbaik otomatis (BUY/SELL).
- **Web Dashboard**: Pantau harga real-time, grafik IHSG, portofolio, dan berita pasar.
- **Auto Trade Logger**: Menyimpan riwayat sinyal dan transaksi secara otomatis.
- **Telegram Notifier**: Mengirim sinyal penting langsung ke Telegram (opsional).

---

## 5. Konfigurasi Deploy (Deploy Configuration)

Untuk menambahkan URL website deploy:
1. Buka file `web/templates/index.html`
2. Cari section `About` atau `Settings`
3. Tambahkan link ke website deploy di sana

Contoh:
```html
<div class="about-section">
  <h3>Tentang</h3>
  <p>Website Live: <a href="https://your-deploy-url.com">your-deploy-url.com</a></p>
</div>
```

---

## 6. Troubleshooting (Kendala & Solusi)
- **Modul kurang / Error `ModuleNotFoundError`**: Jalankan ulang `pip install -r requirements.txt`.
- **Port 5000 sudah dipakai**: Tutup aplikasi lain yang menggunakan port 5000 atau restart komputer.
