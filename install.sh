#!/usr/bin/env bash
set -e

# ==============================================================================
# mac-m1-zero-token: Установщик локальных инструментов для macOS Apple Silicon
# ==============================================================================

echo "=== Установка mac-m1-zero-token ==="

TARGET_DIR="$HOME/.local/bin"
mkdir -p "$TARGET_DIR"

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

# 5. Проверка $PATH в ~/.zshrc
if [[ ":$PATH:" != *":$TARGET_DIR:"* ]]; then
    echo " Добавление $TARGET_DIR в PATH (~/.zshrc)..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    echo "✓ Добавлено в ~/.zshrc"
fi

# 6. Проверка зависимостей
echo " Проверка зависимостей..."
if command -v rg >/dev/null 2>&1; then
    echo "✓ ripgrep (rg) найден"
else
    echo "⚠ ripgrep не найден. Рекомендуется установить: brew install ripgrep"
fi

if command -v ollama >/dev/null 2>&1; then
    echo "✓ ollama установлен"
    brew services start ollama 2>/dev/null || true
    if ! ollama list | grep -q "qwen2.5:3b"; then
        echo " Загрузка легковесной модели qwen2.5:3b (1.9 GB)..."
        ollama pull qwen2.5:3b
    else
        echo "✓ Модель qwen2.5:3b уже загружена"
    fi
else
    echo "⚠ ollama не найден. Рекомендуется установить: brew install ollama"
fi

if command -v pandoc >/dev/null 2>&1; then
    echo "✓ pandoc найден (поддержка DOCX активирована)"
else
    echo "⚠ pandoc не найден. Рекомендуется установить: brew install pandoc"
fi

echo ""
echo "=== Установка завершена успешно! ==="
echo "Доступные команды:"
echo "  1. ocr                       -> Распознать скриншот прямо из буфера обмена"
echo "  2. ocr <файл>                -> Распознать картинку или PDF"
echo "  3. cleandoc <файл_тз>        -> Очистить ТЗ/RFP от воды и сохранить до 85% токенов"
echo "  4. localai \"вопрос/задача\"   -> Задать вопрос локальной модели без интернета (0 токенов)"
echo "  5. localsearch \"запрос\"      -> Сверхбыстрый поиск по пресейлам и памяти (0 токенов)"
