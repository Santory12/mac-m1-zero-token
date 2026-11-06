#!/usr/bin/env python3
"""
localsearch.py - Модуль 4 экосистемы mac-m1-zero-token.
Сверхбыстрый локальный поиск по базе пресейлов, архитектуре и памяти проектов
на базе ripgrep без расхода токенов в LLM.
"""

import sys
import os
import subprocess
import re

DEFAULT_SEARCH_PATHS = [
    os.path.expanduser("~/Documents/GEMINI CLI Sandbox/Presale"),
    os.path.expanduser("~/.gemini/tmp/mais/memory"),
    os.path.expanduser("~/Projects")
]

def print_help():
    print("Использование утилиты localsearch (mac-m1-zero-token):")
    print("  localsearch \"поисковый запрос\" [папка_для_поиска]")
    print("  localsearch --all \"поисковый запрос\"  (поиск по всей базе знаний)")
    print("\nПримеры:")
    print("  localsearch \"KSeF\"                 -> Поиск в текущем проекте и памяти")
    print("  localsearch \"NovaZone\" ./LMA_Trading -> Поиск ТОЛЬКО в указанной папке")
    print("  localsearch --all \"DATEV\"          -> Глобальный поиск по всем архивам")
    print("\nМгновенно находит релевантные куски с контекстом (0 токенов в облако).")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print_help()
        sys.exit(0)

    is_global = False
    args = sys.argv[1:]

    if args[0] in ["--all", "-a"]:
        is_global = True
        args = args[1:]

    if not args:
        print_help()
        sys.exit(0)

    query = args[0]
    search_dirs = []

    if len(args) >= 2:
        # Указана конкретная папка -> ищем ТОЛЬКО в ней!
        custom_dir = os.path.expanduser(args[1])
        if os.path.exists(custom_dir):
            search_dirs.append(custom_dir)
        else:
            print(f"❌ Ошибка: Указанная папка не найдена: {custom_dir}")
            sys.exit(1)
    elif is_global:
        # Глобальный поиск по всем архивам
        search_dirs = [p for p in DEFAULT_SEARCH_PATHS if os.path.exists(p)]
    else:
        # По умолчанию: текущая папка + память проектов
        search_dirs = [os.getcwd()]
        mem_dir = os.path.expanduser("~/.gemini/tmp/mais/memory")
        if os.path.exists(mem_dir) and mem_dir not in search_dirs:
            search_dirs.append(mem_dir)

    if not search_dirs:
        print("Нет доступных каталогов", file=sys.stderr)
        sys.exit(2)

    print(f"🔍 Поиск «{query}» в: {', '.join(search_dirs)}...")

    cmd = [
        "rg", "-F", "-i", "-C", "2", "-M", "300",
        "--heading", "--line-number",
        "-g", "!*.git*",
        "-g", "!*.pyc",
        "-g", "!__pycache__",
        "-g", "!*.iso",
        "-g", "!*.dsf",
        "-g", "!*.flac",
        "-g", "!*.mp3",
        "--", query
    ] + search_dirs

    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode not in (0, 1):
            print(res.stderr.strip(), file=sys.stderr)
            sys.exit(2)
        output = res.stdout.strip()
        if not output:
            print(f" Совпадений по запросу «{query}» не найдено.")
            sys.exit(0)

        matches_count = len(re.findall(rf"(?i){re.escape(query)}", output))
        print(f"✓ Найдено совпадений: {matches_count}\n")
        print("="*60)
        print(output)
        print("="*60)
        print("\n💡 Совет: Передавайте в контекст Gemini/Codex только найденные 5–10 строк, а не весь файл.")
    except FileNotFoundError:
        print("❌ Ошибка: ripgrep (rg) не найден. Установите: brew install ripgrep")
        sys.exit(1)

if __name__ == "__main__":
    main()
