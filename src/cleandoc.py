#!/usr/bin/env python3
"""
cleandoc.py - Модуль 2 экосистемы mac-m1-zero-token.
Надежное извлечение и очистка ТЗ, RFP и документов от шума.
Всегда сохраняет полный извлеченный текст отдельно от компактной версии,
предотвращая потерю критических условий приемки, оплат и SLA.
"""

import sys
import os
import re
import subprocess

# Секции юридической и административной воды (вырезаются только в компактную версию)
BOILERPLATE_SECTION_PATTERNS = [
    r"(?i)^(?:#+\s*)?(?:раздел\s*\d*[\.\:]?\s*)?предмет\s+(?:договора|соглашения|тз).*$",
    r"(?i)^(?:#+\s*)?(?:раздел\s*\d*[\.\:]?\s*)?порядок\s+(?:сдачи|приемки|оплаты|расчетов).*$",
    r"(?i)^(?:#+\s*)?(?:раздел\s*\d*[\.\:]?\s*)?ответственность\s+сторон.*$",
    r"(?i)^(?:#+\s*)?(?:раздел\s*\d*[\.\:]?\s*)?форс[\s\-]мажор.*$",
    r"(?i)^(?:#+\s*)?(?:раздел\s*\d*[\.\:]?\s*)?разрешение\s+споров.*$",
    r"(?i)^(?:#+\s*)?(?:раздел\s*\d*[\.\:]?\s*)?конфиденциальность.*$",
    r"(?i)^(?:#+\s*)?(?:раздел\s*\d*[\.\:]?\s*)?права\s+и\s+обязанности\s+сторон.*$",
    r"(?i)^(?:#+\s*)?(?:раздел\s*\d*[\.\:]?\s*)?адреса[,\s]+реквизиты\s+и\s+подписи.*$",
    r"(?i)^(?:#+\s*)?(?:раздел\s*\d*[\.\:]?\s*)?срок\s+действия\s+договора.*$",
    r"(?i)^(?:#+\s*)?(?:раздел\s*\d*[\.\:]?\s*)?юридические\s+аспекты.*$",
]

# Мусорные строки (колонтитулы, номера страниц, служебные плашки)
JUNK_LINE_PATTERNS = [
    r"(?i)^\s*(?:стр\.|страница)\s*\d+(?:\s*(?:из|/)\s*\d+)?\s*$",
    r"(?i)^\s*(?:page)\s*\d+(?:\s*(?:of|/)\s*\d+)?\s*$",
    r"(?i)^\s*(?:коммерческая\s+тайна|конфиденциально|strictly\s+confidential)\s*$",
    r"^\s*[\-\_\*\=\~]{3,}\s*$",
    r"^\s*•\s*$",
    r"^\s*[\d\.\s]+\s*$",
]

def estimate_tokens(text: str) -> int:
    """Оценка количества токенов (русский + английский)."""
    words = len(text.split())
    chars = len(text)
    return max(words, chars // 3)

def convert_to_markdown(file_path: str) -> str:
    """
    Строгое локальное извлечение текста.
    Никаких опасных fallback в чтение бинарных файлов как UTF-8!
    При сбое конвертации выбрасывает понятную ошибку.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".docx":
        # Проверяем pandoc
        pandoc_bin = "/opt/homebrew/bin/pandoc" if os.path.exists("/opt/homebrew/bin/pandoc") else "pandoc"
        res = subprocess.run([pandoc_bin, "-f", "docx", "-t", "markdown", file_path],
                             capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Ошибка конвертации DOCX через pandoc: {res.stderr.strip()}")
        content = res.stdout.strip()
        if not content:
            raise RuntimeError("Pandoc вернул пустой результат при конвертации DOCX.")
        return content

    elif ext in [".pdf", ".png", ".jpg", ".jpeg", ".heic", ".webp"]:
        ocr_bin = os.path.expanduser("~/.local/bin/ocr")
        if not os.path.exists(ocr_bin):
            ocr_bin = "ocr"
        res = subprocess.run([ocr_bin, file_path], capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Утилита ocr завершилась с ошибкой: {res.stderr.strip() or res.stdout.strip()}")

        content = res.stdout.strip()
        if not content:
            raise RuntimeError(f"OCR не смог извлечь текст из файла '{file_path}'. Файл пуст или поврежден.")
        return content

    elif ext in [".txt", ".md", ".markdown"]:
        with open(file_path, "r", encoding="utf-8", errors="strict") as f:
            content = f.read().strip()
            if not content:
                raise RuntimeError(f"Текстовый файл '{file_path}' пуст.")
            return content

    else:
        raise ValueError(f"Неподдерживаемый формат: '{ext}'. Поддерживаются: .docx, .pdf, .png, .jpg, .heic, .md, .txt")

def clean_text_compact(raw_text: str, source_filename: str) -> str:
    lines = raw_text.splitlines()
    cleaned_lines = []
    skip_mode = False
    omitted_sections = []

    for line in lines:
        stripped = line.strip()

        # 1. Проверяем, не начинается ли юридическая секция
        matched_pat = None
        for pat in BOILERPLATE_SECTION_PATTERNS:
            if re.match(pat, stripped):
                matched_pat = pat
                break

        if matched_pat:
            skip_mode = True
            omitted_sections.append(stripped)
            continue

        # 2. Если мы в режиме пропуска, проверяем, не начался ли новый значимый раздел
        if skip_mode:
            if re.match(r"^\d+(?:\.\d+)*[.)]?\s+\S", stripped):
                skip_mode = False
            elif re.match(r"(?i)^#+\s+(?!предмет|порядок|ответственность|конфиденциальность).*$", stripped):
                skip_mode = False
            elif re.match(r"(?i)^(?:раздел\s*\d*[\.\:]?\s*)?(?:функционал|требован|архитектур|модул|интеграц|wbs|роли|сценари).*$", stripped):
                skip_mode = False
            else:
                continue

        # 3. Фильтрация колонтитулов и пустых мусорных строк
        if any(re.match(pat, stripped) for pat in JUNK_LINE_PATTERNS):
            continue

        # 4. Схлопывание множественных пробелов
        line = re.sub(r"[ \t]+", " ", line)
        cleaned_lines.append(line)

    body = "\n".join(cleaned_lines)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()

    header = (
        f"> 📌 **КОМПАКТНАЯ ВЫЖИМКА ТРЕБОВАНИЙ (mac-m1-zero-token)**\n"
        f"> **Исходный документ:** `{os.path.basename(source_filename)}`\n"
        f"> **Полный текст со всеми условиями оплаты/приемки:** сохранен в `{os.path.splitext(source_filename)[0]}_full.md`\n"
    )
    if omitted_sections:
        header += f"> **Исключенные разделы воды:** {', '.join(omitted_sections[:4])}...\n"
    header += "\n---\n\n"

    return header + body

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Использование утилиты cleandoc (mac-m1-zero-token):")
        print("  cleandoc <файл_тз.(docx|pdf|md|txt)>")
        print("\nСоздает ДВА файла:")
        print("  1. <файл>_full.md    -> Полный извлеченный текст (без дополнительного сокращения; полнота зависит от извлечения)")
        print("  2. <файл>_compact.md -> Компактная версия без юридической воды для экономии контекста")
        print("\nНикогда не производит скрытый облачный fallback при ошибках.")
        sys.exit(0)

    src_file = sys.argv[1]
    if not os.path.exists(src_file):
        print(f"❌ Ошибка: Файл не найден: {src_file}")
        sys.exit(1)

    print(f" Чтение и строгое локальное извлечение: {src_file}...")
    try:
        raw_content = convert_to_markdown(src_file)
    except Exception as e:
        print(f"❌ Сбой локальной обработки: {e}")
        print("Облачный fallback запрещен. Проверьте исходный файл.")
        sys.exit(1)

    initial_tokens = estimate_tokens(raw_content)
    base_path = os.path.splitext(src_file)[0]

    # 1. ВСЕГДА сохраняем полный извлеченный текст
    full_out = f"{base_path}_full.md"
    with open(full_out, "w", encoding="utf-8") as f:
        f.write(raw_content + "\n")
    print(f"✓ Полный текст сохранен: {full_out} (~{initial_tokens:,} токенов)")

    # 2. Генерируем компактную версию
    compact_content = clean_text_compact(raw_content, src_file)
    compact_tokens = estimate_tokens(compact_content)
    compact_out = f"{base_path}_compact.md"
    with open(compact_out, "w", encoding="utf-8") as f:
        f.write(compact_content + "\n")

    saved_tokens = max(0, initial_tokens - compact_tokens)
    percent = (saved_tokens / initial_tokens * 100) if initial_tokens > 0 else 0

    print("\n" + "="*60)
    print(f"📄 Полный файл (все условия):    {full_out} (~{initial_tokens:,} токенов)")
    print(f"⚡ Компактный файл (для чата):  {compact_out} (~{compact_tokens:,} токенов)")
    print(f"🔥 Разница объема:              -{saved_tokens:,} токенов ({percent:.1f}%)")
    print("="*60)

if __name__ == "__main__":
    main()
