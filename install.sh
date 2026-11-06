#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# ==============================================================================
# mac-m1-zero-token: Установщик локальных инструментов для macOS Apple Silicon
# ==============================================================================

echo "=== Установка mac-m1-zero-token ==="

TARGET_DIR="$HOME/.local/bin"
mkdir -p "$TARGET_DIR"

# Use a Python environment with the required Excel dependency.
PYTHON_BIN=""
for candidate in python3 python3.14; do
    if command -v "$candidate" >/dev/null && "$candidate" -c 'import openpyxl' 2>/dev/null; then
        PYTHON_BIN=$(command -v "$candidate")
        break
    fi
done
if [ -z "$PYTHON_BIN" ]; then
    echo "Requires Python with openpyxl. Install it in a virtual environment and put that environment on PATH." >&2
    exit 1
fi

# 1. Компиляция нативной утилиты ocr (Swift + Apple Vision + PDFKit)
echo " Компиляция утилиты ocr под Apple Silicon..."
swiftc -O src/ocr.swift -o "$TARGET_DIR/ocr"
chmod +x "$TARGET_DIR/ocr"
echo "✓ Утилита ocr установлена в $TARGET_DIR/ocr"

# 2. Установка утилиты cleandoc (Python-фильтратор ТЗ и документов)
echo " Установка утилиты cleandoc..."
cp src/cleandoc.py "$TARGET_DIR/cleandoc"
chmod +x "$TARGET_DIR/cleandoc"
echo "✓ Утилита cleandoc установлена в $TARGET_DIR/cleandoc"

# 3. Установка утилиты localai (Интерфейс к малым локальным моделям SLM 3B)
echo " Установка утилиты localai..."
cp src/localai.py "$TARGET_DIR/localai"
chmod +x "$TARGET_DIR/localai"
echo "✓ Утилита localai установлена в $TARGET_DIR/localai"

# 4. Установка утилиты localsearch (Сверхбыстрый поиск по базе знаний через ripgrep)
echo " Установка утилиты localsearch..."
cp src/localsearch.py "$TARGET_DIR/localsearch"
chmod +x "$TARGET_DIR/localsearch"
echo "✓ Утилита localsearch установлена в $TARGET_DIR/localsearch"

# 5. Установка утилит валидации артефактов (Модуль 5: wbsvalid, wbs2xlsx, checkodoo)
echo " Установка утилит валидации артефактов..."
cp src/validate_wbs.py "$TARGET_DIR/wbsvalid"
chmod +x "$TARGET_DIR/wbsvalid"
cp src/generate_wbs_xlsx.py "$TARGET_DIR/wbs2xlsx"
chmod +x "$TARGET_DIR/wbs2xlsx"
cp src/checkodoo.py "$TARGET_DIR/checkodoo"
chmod +x "$TARGET_DIR/checkodoo"
echo "✓ Утилиты wbsvalid, wbs2xlsx, checkodoo установлены в $TARGET_DIR"

# 6. Установка продвинутых утилит (Модуль 6 и 7: docmap, localdoctor)
echo " Установка утилит docmap и localdoctor..."
cp src/docmap.py "$TARGET_DIR/docmap"
chmod +x "$TARGET_DIR/docmap"
cp src/localdoctor.sh "$TARGET_DIR/localdoctor"
chmod +x "$TARGET_DIR/localdoctor"
echo "✓ Утилиты docmap и localdoctor установлены в $TARGET_DIR"

# Pin Python tools to the interpreter whose dependencies were checked.
for tool in cleandoc localai localsearch wbsvalid wbs2xlsx checkodoo docmap; do
    "$PYTHON_BIN" - "$TARGET_DIR/$tool" "$PYTHON_BIN" <<'PYTHON'
import pathlib, sys
p = pathlib.Path(sys.argv[1])
p.write_text("#!" + sys.argv[2] + "\n" + p.read_text().split("\n", 1)[1])
PYTHON
done
cp src/transcribe_local.sh "$TARGET_DIR/transcribe_local"
chmod +x "$TARGET_DIR/transcribe_local"

# 6. Проверка $PATH в ~/.zshrc
if [[ ":$PATH:" != *":$TARGET_DIR:"* ]]; then
    echo " Добавление $TARGET_DIR в PATH (~/.zshrc)..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    echo "✓ Добавлено в ~/.zshrc"
fi

# 7. Проверка зависимостей
echo " Проверка зависимостей..."
if command -v rg >/dev/null 2>&1; then
    echo "✓ ripgrep (rg) найден"
else
    echo "⚠ ripgrep не найден. Рекомендуется установить: brew install ripgrep"
fi

if command -v ollama >/dev/null 2>&1; then
    echo "✓ ollama установлен"
    echo "Модели и запуск Ollama настраиваются отдельно; установщик их не загружает."
else
    echo "⚠ ollama не найден. Рекомендуется установить: brew install ollama"
fi

if command -v pandoc >/dev/null 2>&1; then
    echo "✓ pandoc найден (поддержка DOCX активирована)"
else
    echo "⚠ pandoc не найден. Рекомендуется установить: brew install pandoc"
fi

echo ""
echo "=== Установка завершена успешно! Все 5 модулей развернуты! ==="
echo "Доступные команды:"
echo "  1. ocr                       -> Распознать скриншот прямо из буфера обмена"
echo "  2. ocr <файл>                -> Распознать картинку или PDF"
echo "  3. cleandoc <файл_тз>        -> Очистить ТЗ/RFP от воды и сохранить до 85% токенов"
echo "  4. localai \"вопрос/задача\"   -> Задать вопрос локальной модели без интернета (0 токенов)"
echo "  5. localsearch \"запрос\"      -> Сверхбыстрый поиск по пресейлам и памяти (0 токенов)"
echo "  6. wbsvalid <файл.csv>       -> Строгая валидация WBS Gold Standard"
echo "  7. wbs2xlsx <en.csv> <ru.csv> <output.xlsx>       -> Генерация форматированного 2-вкладочного Excel"
echo "  8. checkodoo <файл.xml|py>   -> Проверка синтаксиса и правил Odoo 18/19"
echo "  9. docmap <файл.md>          -> Генерация карты документа (номера строк, H1-H6, токены)"
echo " 10. localdoctor               -> Диагностика зависимостей и целостности модулей экосистемы"
