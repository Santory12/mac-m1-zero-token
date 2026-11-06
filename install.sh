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

# 3. Проверка $PATH в ~/.zshrc
if [[ ":$PATH:" != *":$TARGET_DIR:"* ]]; then
    echo " Добавление $TARGET_DIR в PATH (~/.zshrc)..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    echo "✓ Добавлено в ~/.zshrc"
fi

# 4. Проверка зависимостей
echo " Проверка зависимостей..."
if command -v pandoc >/dev/null 2>&1; then
    echo "✓ pandoc найден (поддержка DOCX активирована)"
else
    echo "⚠ pandoc не найден. Для конвертации DOCX рекомендуется установить: brew install pandoc"
fi

echo ""
echo "=== Установка завершена успешно! ==="
echo "Доступные команды:"
echo "  1. ocr                       -> Распознать скриншот прямо из буфера обмена"
echo "  2. ocr <файл>                -> Распознать картинку или PDF"
echo "  3. cleandoc <файл_тз>        -> Очистить ТЗ/RFP от воды и сохранить до 85% токенов"
