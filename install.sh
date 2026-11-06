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

# 2. Проверка $PATH в ~/.zshrc
if [[ ":$PATH:" != *":$TARGET_DIR:"* ]]; then
    echo " Добавление $TARGET_DIR в PATH (~/.zshrc)..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    echo "✓ Добавлено в ~/.zshrc"
fi

# 3. Проверка зависимостей
echo " Проверка зависимостей..."
if command -v pandoc >/dev/null 2>&1; then
    echo "✓ pandoc найден (поддержка DOCX активирована)"
else
    echo "⚠ pandoc не найден. Для конвертации DOCX рекомендуется установить: brew install pandoc"
fi

echo ""
echo "=== Установка завершена успешно! ==="
echo "Как пользоваться:"
echo "  1. Скопируй любую картинку/скриншот в буфер и напиши: ocr"
echo "  2. Или распознай файл напрямую: ocr image.png / ocr document.pdf"
