"""Video downloader tool for social media (TikTok, Instagram, YouTube, Facebook, dll).

Menggunakan yt-dlp sebagai engine utama karena mendukung banyak platform.
"""
import os
import subprocess

from ..config import state


def _shutil_which(name):
    """Cari binary apakah tersedia (tanpa import shutil di level modul)."""
    import shutil
    return shutil.which(name)


def _resolve_output_dir(output_dir):
    """Pastikan direktori output berada di dalam WORKSPACE_DIR, lalu buat jika perlu."""
    workspace = os.path.abspath(state.WORKSPACE_DIR)
    if not output_dir:
        target = os.path.join(workspace, "downloads")
    elif os.path.isabs(output_dir):
        # Jalur absolut: paksa agar tetap berada di dalam workspace.
        target = os.path.abspath(output_dir)
        if os.path.commonpath([target, workspace]) != workspace:
            target = os.path.join(workspace, "downloads")
    else:
        # Jalur relatif: dianggap relatif terhadap WORKSPACE_DIR, bukan cwd.
        target = os.path.abspath(os.path.join(workspace, output_dir))
    os.makedirs(target, exist_ok=True)
    return target


def download_video(url, output_dir="", format_="best"):
    """Download video dari URL medsos (TikTok/IG/YT/FB/dll) via yt-dlp.

    Args:
        url: URL lengkap video media sosial.
        output_dir: folder tujuan (relatif/absolut dalam workspace). Default workspace/downloads.
        format_: format yang diminta (best = gabungan video+audio terbaik).

    Returns:
        String berisi hasil/status download.
    """
    if not url or not str(url).strip():
        return "Error: URL kosong. Berikan URL video yang valid."
    url = str(url).strip()

    # ===== Cek engine yt-dlp =====
    yt_dlp = _shutil_which("yt-dlp")
    if not yt_dlp:
        return (
            "Error: yt-dlp belum terinstall.\n"
            "Install dengan:  pip install yt-dlp   (atau)  pkg install yt-dlp  (Termux).\n"
            "Juga pastikan ffmpeg terinstall untuk hasil video+audio:  pkg install ffmpeg"
        )

    target = _resolve_output_dir(output_dir)

    cmd = [yt_dlp]
    # Format default yang robust: ambil video+audio terbaik.
    # 'bv*+ba/b' = best video + best audio (bakal merge, butuh ffmpeg).
    # 'best'     = fallback single file bila ffmpeg tidak ada.
    if format_ and str(format_).strip() not in ("", "best"):
        cmd += ["-f", str(format_)]
    else:
        cmd += ["-f", "bv*+ba/b", "--merge-output-format", "mp4"]

    # File sementara untuk mencatat path hasil tanpa mencemari stdout live.
    import tempfile
    pathfile = os.path.join(tempfile.gettempdir(), "zagent_dl_path.txt")
    try:
        os.remove(pathfile)
    except OSError:
        pass

    cmd += [
        "-o", os.path.join(target, "%(title)s.%(ext)s"),
        "--no-playlist",
        "--no-warnings",
        # Progress (persen) dialirkan LIVE ke terminal
        "--progress",
        "--print-to-file", "after_move:filepath", pathfile,
        url,
    ]

    try:
        proc = subprocess.run(
            cmd,
            # stdout/stderr diteruskan ke terminal → progress persen terlihat live
            capture_output=False,
            timeout=900,
        )

        saved = ""
        try:
            with open(pathfile, "r", encoding="utf-8") as f:
                saved = f.read().strip()
        except OSError:
            saved = ""

        if proc.returncode == 0:
            if not saved:
                saved = os.path.join(target, "hasil (cek folder)")
            return (
                f"\n[✓] Download selesai!\n"
                f"  URL      : {url}\n"
                f"  Tersimpan: {saved}\n"
            )
        # yt-dlp mungkin butuh ffmpeg untuk merge; jika error, beri saran
        return f"\n[x] Gagal download (kode {proc.returncode}).\n"
    except subprocess.TimeoutExpired:
        return "Error: Download melebihi batas waktu (900 detik)."
    except Exception as e:
        return f"Error saat download: {e}"


def downloads_help():
    """Panduan singkat penggunaan tool download."""
    return (
        "Tool downloader video medsos (yt-dlp).\n"
        "Contoh perintah:\n"
        "  'download video TikTok ini: <url>'\n"
        "  'simpan video YouTube <url> ke folder youtube'\n"
        "  'download video <url> resolusi terbaik'\n"
        "File disimpan ke workspace/downloads (atau folder yang diminta)."
    )
