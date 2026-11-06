#!/usr/bin/env bash
# ==============================================================================
#                  LOCAL AUDIO/VIDEO TRANSCRIPTION (M1 LOCAL)
# ==============================================================================
# Полностью локальная транскрибация видео/аудио на чипе Apple Silicon (M1)
# с использованием ffmpeg и OpenAI Whisper. В облако не уходит НИ ОДНОГО токена!

set -e

INPUT_FILE="$1"
TRANSCRIBE_LANGUAGE="${2:-ru}"
MODEL="${3:-base}"

if [ -z "$INPUT_FILE" ]; then
    echo "Ошибка: Укажи путь к медиа-файлу!"
    echo "Использование: ~/transcribe_local.sh <путь_к_видео_или_аудио> [язык: ru|en] [модель: base|small|tiny]"
    exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
    echo "Ошибка: Файл '$INPUT_FILE' не найден!"
    exit 1
fi

WHISPER_BIN="/opt/homebrew/bin/whisper"
FFMPEG_BIN="/opt/homebrew/bin/ffmpeg"

if [ ! -x "$WHISPER_BIN" ]; then
    echo "Ошибка: Whisper не найден по пути $WHISPER_BIN"
    exit 1
fi

if [ ! -x "$FFMPEG_BIN" ]; then
    echo "Ошибка: ffmpeg не найден по пути $FFMPEG_BIN"
    exit 1
fi

BASENAME=$(basename "$INPUT_FILE")
FILENAME="${BASENAME%.*}"
DIRNAME=$(dirname "$INPUT_FILE")
WORK_DIR=$(mktemp -d "${TMPDIR:-/tmp}/transcribe.XXXXXX")
trap 'rm -rf -- "$WORK_DIR"' EXIT
TEMP_WAV="$WORK_DIR/audio.wav"
OUT_TXT="${DIRNAME}/${FILENAME}_transcript.txt"

echo "🎙️ [1/3] Извлечение аудио через ffmpeg (16kHz mono)..."
"$FFMPEG_BIN" -y -i "$INPUT_FILE" -vn -ar 16000 -ac 1 -c:a pcm_s16le "$TEMP_WAV" -loglevel warning

echo "🧠 [2/3] Локальная расшифровка через Whisper (модель: $MODEL, язык: $TRANSCRIBE_LANGUAGE)..."
"$WHISPER_BIN" "$TEMP_WAV" \
    --model "$MODEL" \
    --language "$TRANSCRIBE_LANGUAGE" \
    --output_format txt \
    --output_dir "$WORK_DIR" \
    --fp16 False

TRANSCRIPT_TMP="$WORK_DIR/audio.txt"
if [ -s "$TRANSCRIPT_TMP" ]; then
    mv "$TRANSCRIPT_TMP" "$OUT_TXT"
    echo "✅ [3/3] Готово! Транскрипт сохранен: $OUT_TXT"
else
    echo "⚠️ Не удалось найти сгенерированный транскрипт в /tmp"
    exit 1
fi

echo "📄 Результат: $OUT_TXT"
