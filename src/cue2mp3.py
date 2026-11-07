#!/usr/bin/env python3
"""
cue2mp3.py - Модуль нарезки и конвертации CUE + FLAC/WAV/APE в отдельные MP3 320 kbps.
Работает 100% локально на базе ffmpeg, сохраняет все теги и вшивает обложку.
"""

import sys
import os
import re
import shutil
import subprocess

def frames_to_seconds(time_str):
    """Преобразует время CUE 'MM:SS:FF' (где FF - кадры, 75 в секунде) в секунды."""
    parts = time_str.split(':')
    if len(parts) == 3:
        minutes = int(parts[0])
        seconds = int(parts[1])
        frames = int(parts[2])
        return minutes * 60 + seconds + (frames / 75.0)
    elif len(parts) == 2:
        minutes = int(parts[0])
        seconds = int(parts[1])
        return minutes * 60 + seconds
    return 0.0

def parse_cue(cue_path):
    """Парсит CUE-файл и возвращает общие метаданные и список треков."""
    album_info = {
        "title": "Unknown Album",
        "performer": "Unknown Artist",
        "date": "",
        "genre": "",
        "file": ""
    }
    tracks = []
    current_track = None

    with open(cue_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Общие метаданные альбома
            if line.startswith("TITLE ") and not current_track:
                album_info["title"] = line.split("TITLE ", 1)[1].strip('"')
            elif line.startswith("PERFORMER ") and not current_track:
                album_info["performer"] = line.split("PERFORMER ", 1)[1].strip('"')
            elif line.startswith("REM DATE ") and not current_track:
                album_info["date"] = line.split("REM DATE ", 1)[1].strip('"')
            elif line.startswith("REM GENRE ") and not current_track:
                album_info["genre"] = line.split("REM GENRE ", 1)[1].strip('"')
            elif line.startswith("FILE "):
                m = re.match(r'FILE\s+"?([^"]+)"?\s+.*', line)
                if m:
                    album_info["file"] = m.group(1)

            # Треки
            elif line.startswith("TRACK "):
                parts = line.split()
                track_num = parts[1]
                if current_track:
                    tracks.append(current_track)
                current_track = {
                    "number": int(track_num),
                    "title": f"Track {track_num}",
                    "performer": album_info["performer"],
                    "start": 0.0,
                    "end": None
                }
            elif current_track:
                if line.startswith("TITLE "):
                    current_track["title"] = line.split("TITLE ", 1)[1].strip('"')
                elif line.startswith("PERFORMER "):
                    current_track["performer"] = line.split("PERFORMER ", 1)[1].strip('"')
                elif line.startswith("INDEX 01 "):
                    time_code = line.split("INDEX 01 ", 1)[1].strip()
                    current_track["start"] = frames_to_seconds(time_code)

    if current_track:
        tracks.append(current_track)

    # Вычисляем конечные точки треков
    for i in range(len(tracks) - 1):
        tracks[i]["end"] = tracks[i+1]["start"]

    return album_info, tracks

def find_cover(directory):
    """Ищет обложку альбома в папке."""
    candidates = ["front.jpg", "front.jpeg", "cover.jpg", "cover.jpeg", "folder.jpg", "front.png"]
    files = {f.lower(): f for f in os.listdir(directory)}
    for cand in candidates:
        if cand in files:
            return os.path.join(directory, files[cand])
    # Если точного совпадения нет, ищем любой jpg/jpeg
    for f_lower, f_orig in files.items():
        if f_lower.endswith((".jpg", ".jpeg", ".png")) and "back" not in f_lower and "inside" not in f_lower:
            return os.path.join(directory, f_orig)
    return None

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Использование утилиты cue2mp3 (mac-m1-zero-token):")
        print("  cue2mp3 <папка_с_cue_или_путь_к_cue_файлу> [выходная_папка]")
        print("\nАвтоматически нарезает цельный FLAC/APE по CUE-разметке на треки MP3 320 kbps")
        print("с заполнением тегов и вшиванием обложки (100% локально через ffmpeg).")
        sys.exit(0)

    target_path = os.path.abspath(os.path.expanduser(sys.argv[1]))
    if os.path.isdir(target_path):
        cue_dir = target_path
        cues = [f for f in os.listdir(cue_dir) if f.lower().endswith(".cue")]
        if not cues:
            print(f"❌ Ошибка: В папке '{cue_dir}' не найден .cue файл!")
            sys.exit(1)
        cue_file = os.path.join(cue_dir, cues[0])
    else:
        cue_file = target_path
        cue_dir = os.path.dirname(target_path)

    if not os.path.exists(cue_file):
        print(f"❌ Ошибка: CUE файл не найден: {cue_file}")
        sys.exit(1)

    print(f" Чтение CUE: {os.path.basename(cue_file)}...")
    album_info, tracks = parse_cue(cue_file)
    print(f"  Альбом:     {album_info['title']}")
    print(f"  Исполнитель: {album_info['performer']}")
    print(f"  Треков:     {len(tracks)}")

    # Находим исходный аудиофайл
    audio_filename = album_info["file"]
    audio_path = os.path.join(cue_dir, audio_filename)
    if not os.path.exists(audio_path):
        # Пробуем найти любой .flac / .wav / .ape в папке
        audio_candidates = [f for f in os.listdir(cue_dir) if f.lower().endswith((".flac", ".wav", ".ape", ".wv"))]
        if audio_candidates:
            audio_path = os.path.join(cue_dir, audio_candidates[0])
            print(f"  Аудиофайл определен автоматически: {audio_candidates[0]}")
        else:
            print(f"❌ Ошибка: Не найден аудиофайл для нарезки: {audio_path}")
            sys.exit(1)
    else:
        print(f"  Аудиофайл:  {os.path.basename(audio_path)}")

    # Обложка
    cover_path = find_cover(cue_dir)
    if cover_path:
        print(f"  Обложка:    {os.path.basename(cover_path)}")
    else:
        print("  Обложка:    не найдена (треки будут без вшитой картинки)")

    # Папка вывода
    if len(sys.argv) >= 3:
        out_dir = os.path.abspath(os.path.expanduser(sys.argv[2]))
    else:
        out_dir = os.path.join(cue_dir, "MP3")

    os.makedirs(out_dir, exist_ok=True)
    if cover_path:
        shutil.copy2(cover_path, os.path.join(out_dir, "cover.jpg"))

    # Если исходник на сетевом диске SMB, временно копируем на локальный SSD для скорости
    is_remote = not audio_path.startswith(os.path.expanduser("~")) and not audio_path.startswith("/tmp")
    local_source = audio_path
    temp_local_file = None

    if is_remote and os.path.getsize(audio_path) < 1000 * 1024 * 1024:
        temp_local_file = f"/tmp/cue_source_{os.getpid()}.flac"
        size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        print(f"\n Копирование {size_mb:.1f} MB на локальный SSD для ускорения нарезки...")
        shutil.copy2(audio_path, temp_local_file)
        local_source = temp_local_file
        print("✓ Скопировано. Нарезка на SSD в разы быстрее сети!")

    print(f"\n Нарезка и кодирование в MP3 320 kbps (всего {len(tracks)} треков)...")
    ffmpeg_bin = "/opt/homebrew/bin/ffmpeg" if os.path.exists("/opt/homebrew/bin/ffmpeg") else "ffmpeg"

    for t in tracks:
        track_num = t["number"]
        title_sanitized = re.sub(r'[\/\\:\*\?"<>\|]', '_', t["title"])
        out_filename = f"{track_num:02d}. {title_sanitized}.mp3"
        out_filepath = os.path.join(out_dir, out_filename)

        print(f"  [{track_num:02d}/{len(tracks):02d}] {t['title']} ({t['performer']})...", end="", flush=True)

        cmd = [ffmpeg_bin, "-y", "-loglevel", "error"]
        cmd += ["-ss", f"{t['start']:.3f}"]
        if t["end"] is not None:
            cmd += ["-to", f"{t['end']:.3f}"]

        cmd += ["-i", local_source]

        if cover_path:
            cmd += [
                "-i", cover_path,
                "-map", "0:a", "-map", "1:0",
                "-c:a", "libmp3lame", "-b:a", "320k",
                "-c:v", "copy", "-id3v2_version", "3",
                "-metadata:s:v", "title=Album cover",
                "-metadata:s:v", "comment=Cover (front)"
            ]
        else:
            cmd += [
                "-map", "0:a",
                "-c:a", "libmp3lame", "-b:a", "320k",
                "-id3v2_version", "3"
            ]

        # Метаданные ID3
        cmd += [
            "-metadata", f"title={t['title']}",
            "-metadata", f"artist={t['performer']}",
            "-metadata", f"album={album_info['title']}",
            "-metadata", f"track={track_num:02d}/{len(tracks):02d}"
        ]
        if album_info.get("date"):
            cmd += ["-metadata", f"date={album_info['date']}"]
        if album_info.get("genre"):
            cmd += ["-metadata", f"genre={album_info['genre']}"]

        cmd.append(out_filepath)

        ret = subprocess.run(cmd)
        if ret.returncode == 0:
            size_kb = os.path.getsize(out_filepath) // 1024
            print(f" ✓ ({size_kb} KB)")
        else:
            print(" ❌ Ошибка кодирования!")

    # Удаляем временный файл на локальном диске
    if temp_local_file and os.path.exists(temp_local_file):
        os.remove(temp_local_file)

    print("\n" + "="*60)
    print(f"🎉 ГОТОВО! Все {len(tracks)} треков нарезаны и сохранены в:")
    print(f"📁 {out_dir}")
    print("="*60)

if __name__ == "__main__":
    main()
