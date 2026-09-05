# Z-Agent (RYZEN/Zen) — Terminal AI Coding Agent

**Z-Agent** adalah *AI coding agent* berbasis CLI yang ringan, dirancang untuk
berjalan di **Termux / Android** maupun di desktop Linux/macOS. Agent ini
terhubung ke API Gemini atau OpenRouter, bisa membaca/menulis file, menjalankan
perintah shell, mencari di web, mengingat konteks jangka panjang, serta mengelola
tugas dan project secara otomatis.

> Nama internal: `RYZEN/Zen (Termux AI Coding Agent)` · Owner: **Master Ken**

---

## Fitur Utama

- **Multi-Provider** — Gemini (Google) dan OpenRouter (banyak model, termasuk
  yang gratis `:free`).
- **Tool Agentik** — AI bisa memanggil fungsi untuk:
  - Manajemen file: baca, tulis, rename, hapus, list direktori.
  - Jalankan perintah shell (`execute_command`).
  - Pencarian web & scraping halaman (`search_web`, `fetch_web_page`).
  - Download video media sosial (`download_video`): TikTok, Instagram, YouTube, Facebook, dll.
  - Long-term memory (`remember_fact`, `get_memory`).
  - Project awareness: info project, cari kode, install dependency, dokumentasi.
  - Task management (`add_task`, `list_tasks`, `complete_task`, `delete_task`).
  - Git integration (`git_status`, `git_operation`, `git_auto_commit`).
- **Mode Berpikir (Think)** — reasonering tertangkap untuk Gemini 2.5 / DeepSeek-R1,
  atau *Chain-of-Thought* fallback lewat prompt.
- **Autocomplete** — popup `/` saat mengetik menggunakan `prompt_toolkit`.
- **Pelacakan Token** — ringkasan pemakaian token per sesi (`/usage`).

---

## Persyaratan

- Python **>= 3.11**
- `uv` (direkomendasikan) atau `pip`
- Koneksi internet & API key Gemini/OpenRouter

Dependency (lihat `pyproject.toml` / `requirements.txt`):

```
requests
beautifulsoup4
prompt_toolkit
yt-dlp        # untuk download video medsos
```

> **Catatan downloader video:** tool `download_video` membutuhkan binary `yt-dlp`
> tersedia di `PATH` (diinstall sebagai dependency Python lewat `uv`/`pip`, atau
> `pkg install yt-dlp` di Termux). Untuk hasil video+audio (merge), install juga
> `ffmpeg`: `pkg install ffmpeg` (Termux) / `sudo apt install ffmpeg` (Linux).

---

## Instalasi & Menjalankan

### One-liner (curl)

```bash
curl -fsSL https://raw.githubusercontent.com/RydzzKen/Z-Agent/main/install.sh | bash
```

Script akan clone repo ke `~/.zagent`, bikin venv, install dependency, dan
pasang launcher `zagent` ke `~/.local/bin` (tambahkan folder itu ke `PATH`
bila belum). Setelah selesai, jalankan:

```bash
zagent
```

Update ke versi terbaru:

```bash
curl -fsSL https://raw.githubusercontent.com/RydzzKen/Z-Agent/main/install.sh | bash
```

### Cara cepat (Termux / Linux)

```bash
git clone <repo-url> zagent && cd zagent
chmod +x run.sh
./run.sh
```

`run.sh` akan:
1. Membuat `requirements.txt` bila belum ada.
2. Menggunakan `uv` (otomatis bikin venv & install). Bila `uv` tidak ada,
   fallback ke `pip install -r requirements.txt`.
3. Menjalankan `python -m zagent.main`.

### Manual

```bash
python -m pip install -r requirements.txt
python -m zagent.main
```

> **Catatan (Termux/Android):** `/sdcard` (FAT) tidak mendukung symlink, sehingga
> venv `uv` dipindah ke `/data` via `UV_LINK_MODE=copy`.

---

## Menghubungkan Provider & API Key

Pertama kali, hubungkan provider dan masukkan API key (otomatis tersimpan ke
`.env`, sudah di-*gitignore*):

```
/connect gemini <API_KEY_ANDA>
/connect openrouter <API_KEY_ANDA>
```

Atau mode interaktif:

```
/connect
```

Ganti provider yang sudah tersimpan (tanpa memasukkan key lagi):

```
/connect gemini
/connect openrouter
```

---

## Perintah Slash (Command)

| Perintah      | Fungsi                                                   |
|---------------|----------------------------------------------------------|
| `/`           | Tampilkan menu perintah                                   |
| `/connect`    | Hubungkan provider & API key                              |
| `/model`      | Lihat & ganti model AI (nomor/nama/manual)               |
| `/status`     | Status agent, koneksi, memori, & tugas                    |
| `/usage`      | Ringkasan pemakaian token sesi ini                        |
| `/think`      | Toggle mode berpikir (on/off/tanpa argumen = toggle)      |
| `/info`       | Profil agent & info sistem                               |
| `/medsos`     | Link media sosial developer                               |
| `/project`    | Info project saat ini                                     |
| `/tasks`      | Lihat daftar tugas                                        |
| `/reset`      | Reset riwayat percakapan                                  |
| `/new`        | Mulai sesi baru (bersihkan riwayat & usage)              |
| `/session`    | Kembali ke sesi sebelumnya (`/session <id>`, `/session baru`) |
| `/clear`      | Bersihkan layar                                           |
| `exit`/`quit` | Keluar                                                    |

Ganti model:

```
/model                  # lihat daftar
/model gemini-2.5-flash
/model 3                # pilih berdasar nomor di daftar
/model free             # hanya model OpenRouter gratis
```

---

## Struktur Project

```
zagent/
├── main.py            # Loop utama & penanganan perintah slash
├── config/
│   ├── state.py       # State global & path (workspace, .env, dll)
│   ├── provider.py    # Manajemen provider & API key
│   ├── models.py      # Daftar & pemilihan model
│   └── state.py
├── llm/
│   ├── client.py      # Panggilan API & schema tool
│   ├── schema.py      # Skema respons
│   └── usage.py       # Pelacakan token
├── tools/
│   ├── registry.py    # Dispatch pemanggilan fungsi
│   ├── web.py         # Search & scraping web
│   ├── downloads.py   # Download video medsos (yt-dlp)
│   ├── memory.py      # Long-term memory
│   ├── fs.py          # Manajemen file sistem
│   ├── exec.py        # Eksekusi perintah shell
│   ├── project.py     # Info project, git, dependency, docs
│   ├── tasks.py       # Manajemen tugas
│   └── prompt.py      # Input & system instruction
├── ui/
│   ├── banner.py      # Banner pembuka
│   └── colors.py      # Warna terminal
└── workspace/         # Batasan operasi file agent (memory.json, tasks.json, ...)
```

---

## Catatan Keamanan

- API key disimpan di `.env` (sudah di-*gitignore*). **Jangan di-commit.**
- Semua operasi file agent dibatasi ke folder `workspace/` agar tidak
  merusak sistem di luar project.

---

## Social Media Developer

- GitHub:    https://github.com/RydzzKen
- Instagram: https://instagram.com/satoru_Ian
- TikTok:    https://tiktok.com/@yxeel05

---

## Lisensi

Project ini bersifat pribadi/milik **Master Ken**. Sesuaikan lisensi sesuai
kebutuhan sebelum disebarluaskan.
