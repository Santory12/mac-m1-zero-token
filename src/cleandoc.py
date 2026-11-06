#!/usr/bin/env python3
"""
cleandoc.py - Модуль 2 экосистемы mac-m1-zero-token.
Локальный чистильщик ТЗ, RFP и спецификаций от юридической воды, колонтитулов
и мусора для экономии до 85% контекстных токенов в LLM.
"""

import sys
import os
import re
import subprocess

# Секции "воды" и юридической шелухи, не несущие архитектурных требований
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

# Мусорные строки (колонтитулы, номера страниц, служебные метки)
JUNK_LINE_PATTERNS = [
    r"(?i)^\s*(?:стр\.|страница)\s*\d+(?:\s*(?:из|/)\s*\d+)?\s*$",
    r"(?i)^\s*(?:page)\s*\d+(?:\s*(?:of|/)\s*\d+)?\s*$",
    r"(?i)^\s*(?:коммерческая\s+тайна|конфиденциально|strictly\s+confidential)\s*$",
    r"^\s*[\-\_\*\=\~]{3,}\s*$",
    r"^\s*•\s*$",
    r"^\s*[\d\.\s]+\s*$",
]

def estimate_tokens(text: str) -> int:
    """Приблизительная оценка количества токенов (русский + английский)."""
    words = len(text.split())
    chars = len(text)
    # Для смешанного русско-английского текста в среднем 1 токен ~ 3-4 символа
    return max(words, chars // 3)

def convert_to_markdown_if_needed(file_path: str) -> str:
    """Если на вход подан DOCX или PDF, сначала переводим в текст через ocr/pandoc."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".docx":
        # Используем pandoc напрямую
        res = subprocess.run(["pandoc", "-f", "docx", "-t", "markdown", file_path],
                             capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout
    elif ext in [".pdf", ".png", ".jpg", ".jpeg", ".heic"]:
        # Используем нашу утилиту ocr
        res = subprocess.run(["ocr", file_path], capture_output=True, text=True)
        txt_path = os.path.splitext(file_path)[0] + ".txt"
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif res.stdout.strip():
            return res.stdout
            
    # Если это текстовый файл или Markdown
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def clean_text(raw_text: str) -> str:
    lines = raw_text.splitlines()
    cleaned_lines = []
    skip_mode = False
    
    for line in lines:
        stripped = line.strip()
        
        # 1. Проверяем, не начинается ли юридическая секция
        is_boilerplate_header = any(re.match(pat, stripped) for pat in BOILERPLATE_SECTION_PATTERNS)
        if is_boilerplate_header:
            skip_mode = True
            continue
            
        # 2. Если мы в режиме пропуска, проверяем, не начался ли новый значимый раздел
        if skip_mode:
            # Если новый заголовок, не являющийся водой
            if re.match(r"(?i)^#+\s+(?!предмет|порядок|ответственность|конфиденциальность).*$", stripped):
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
        
    result = "\n".join(cleaned_lines)
    
    # 5. Схлопывание 3+ пустых строк в максимум 2
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Использование утилиты cleandoc (mac-m1-zero-token):")
        print("  cleandoc <файл_тз.(docx|pdf|md|txt)>")
        print("\nУдаляет юридическую воду, колонтитулы и форматирует ТЗ в чистый Markdown,")
        print("сохраняя до 85% контекстных токенов в Gemini и Codex.")
        sys.exit(0)

    src_file = sys.argv[1]
    if not os.path.exists(src_file):
        print(f"Ошибка: Файл не найден: {src_file}")
        sys.exit(1)

    print(f" Чтение и первичный парсинг: {src_file}...")
    raw_content = convert_to_markdown_if_needed(src_file)
    if not raw_content.strip():
        print("Ошибка: Не удалось извлечь текст из файла.")
        sys.exit(1)

    initial_tokens = estimate_tokens(raw_content)
    print(f" Исходный объем: ~{len(raw_content.split())} слов (~{initial_tokens:,} токенов)")

    print(" Очистка от юридической воды, NDA, колонтитулов и мусора...")
    cleaned = clean_text(raw_content)
    final_tokens = estimate_tokens(cleaned)
    
    saved_tokens = max(0, initial_tokens - final_tokens)
    percent = (saved_tokens / initial_tokens * 100) if initial_tokens > 0 else 0

    base_path = os.path.splitext(src_file)[0]
    out_file = f"{base_path}_cleaned.md"
    
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(cleaned + "\n")

    print("\n" + "="*50)
    print(f"✓ Файл сохранен: {out_file}")
    print(f"📊 До очистки:  ~{initial_tokens:,} токенов")
    print(f"📊 После:       ~{final_tokens:,} токенов")
    print(f"🔥 СЭКОНОМЛЕНО: ~{saved_tokens:,} токенов ({percent:.1f}%)")
    print("="*50)

if __name__ == "__main__":
    main()
