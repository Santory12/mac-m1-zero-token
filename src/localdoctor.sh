#!/usr/bin/env bash
# localdoctor.sh - Модуль 7 экосистемы mac-m1-zero-token.
# Диагностика зависимостей, путей и целостности всех модулей.

echo "🩺 Запуск localdoctor (mac-m1-zero-token)..."
echo "================================================="

TARGET_DIR="$HOME/.local/bin"
ERRORS=0

function check_dep() {
    local cmd=$1
    local name=$2
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "✅ $name: OK ($(command -v $cmd))"
    else
        echo "❌ $name: НЕ НАЙДЕН!"
        ERRORS=$((ERRORS + 1))
    fi
}

function check_util() {
    local util=$1
    if [ -x "$TARGET_DIR/$util" ]; then
        echo "✅ Утилита $util: УСТАНОВЛЕНА ($TARGET_DIR/$util)"
    else
        echo "❌ Утилита $util: НЕ НАЙДЕНА ИЛИ НЕТ ПРАВ!"
        ERRORS=$((ERRORS + 1))
    fi
}

echo "1. Проверка системных зависимостей (Homebrew / Xcode):"
check_dep swiftc "Apple Swift Compiler"
check_dep python3 "Python 3"
check_dep pandoc "Pandoc (DOCX to MD)"
check_dep rg "ripgrep (No-Token Search)"
check_dep ollama "Ollama (SLM Engine)"
check_dep ffmpeg "FFmpeg (Media)"
check_dep whisper "OpenAI Whisper (C++)"

echo ""
echo "2. Проверка переменной PATH:"
if [[ ":$PATH:" == *":$TARGET_DIR:"* ]]; then
    echo "✅ Путь $TARGET_DIR присутствует в \$PATH"
else
    echo "❌ Путь $TARGET_DIR ОТСУТСТВУЕТ в \$PATH!"
    echo "   Добавьте export PATH=\"$TARGET_DIR:\$PATH\" в ~/.zshrc"
    ERRORS=$((ERRORS + 1))
fi

echo ""
echo "3. Проверка модулей mac-m1-zero-token:"
check_util ocr
check_util cleandoc
check_util localai
check_util localsearch
check_util docmap
check_util wbsvalid
check_util wbs2xlsx
check_util checkodoo

echo ""
echo "4. Проверка моделей AI:"
if command -v ollama >/dev/null 2>&1; then
    if ollama list | grep -q "qwen2.5:3b"; then
        echo "✅ Модель qwen2.5:3b: ЗАГРУЖЕНА"
    else
        echo "❌ Модель qwen2.5:3b: НЕ НАЙДЕНА (Выполните: ollama pull qwen2.5:3b)"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "⏭️  Пропуск проверки моделей (ollama не установлен)"
fi

echo "================================================="
if [ $ERRORS -eq 0 ]; then
    echo "🎉 ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ! Экосистема работает штатно."
    exit 0
else
    echo "⚠️  ОБНАРУЖЕНЫ ОШИБКИ: $ERRORS. Пожалуйста, проверьте логи выше."
    exit 1
fi
