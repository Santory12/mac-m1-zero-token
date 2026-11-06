#!/usr/bin/env python3
"""
localai.py - Модуль 3 экосистемы mac-m1-zero-token.
Локальный интерфейс к малым нейросетям (Qwen 2.5 3B / Llama 3.2 3B) на Apple Silicon M1 (Metal).
Выполняет черновую классификацию, саммаризацию и анализ текстов/логов с 0 расходом облачных токенов.
"""

import sys
import os
import json
import urllib.request
import urllib.error

DEFAULT_MODEL = "qwen2.5:3b"
OLLAMA_API_URL = "http://localhost:11434/api/generate"

def stream_generate(prompt: str, system_prompt: str = "", model: str = DEFAULT_MODEL):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.2, # низкая температура для точных фактов и классификации
        }
    }
    if system_prompt:
        payload["system"] = system_prompt

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_API_URL, data=data, headers={"Content-Type": "application/json"})

    try:
        completed = False
        with urllib.request.urlopen(req, timeout=120) as resp:
            for line in resp:
                if line:
                    chunk = json.loads(line.decode("utf-8"))
                    if chunk.get("error"):
                        raise RuntimeError(chunk["error"])
                    completed = completed or chunk.get("done", False)
                    text = chunk.get("response", "")
                    sys.stdout.write(text)
                    sys.stdout.flush()
            if not completed:
                raise RuntimeError("Незавершенный ответ Ollama")
            print() # перевод строки в конце
    except (urllib.error.URLError, TimeoutError, RuntimeError, ValueError) as e:
        print(f"\n[Ошибка] Не удалось связаться с локальным сервисом Ollama: {e}")
        print("Убедитесь, что сервис запущен: brew services start ollama или ollama serve")
        sys.exit(1)

def print_help():
    print("Использование утилиты localai (mac-m1-zero-token):")
    print("  1. Прямой вопрос:           localai \"Ваш вопрос или задача\"")
    print("  2. Анализ файла:            localai <файл> \"Инструкция к файлу\"")
    print("  3. Через конвейер (pipe):   cat logs.txt | localai \"Найди ошибки\"")
    print("\nМодель по умолчанию: qwen2.5:3b (локально на Metal, 0 токенов в облако)")

def main():
    if len(sys.argv) == 1 and sys.stdin.isatty():
        print_help()
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print_help()
        sys.exit(0)

    file_context = ""
    instruction = ""

    # Проверяем stdin (если текст передан через pipe: cat ... | localai ...)
    piped_content = sys.stdin.read().strip() if not sys.stdin.isatty() else ""
    if piped_content:
        file_context = piped_content
        if len(sys.argv) > 1:
            instruction = " ".join(sys.argv[1:])
        else:
            instruction = "Сделай краткое резюме и выдели ключевые факты:"

    elif len(sys.argv) == 2:
        # Один аргумент: либо путь к файлу, либо вопрос
        arg = sys.argv[1]
        if os.path.exists(arg):
            with open(arg, "r", encoding="utf-8", errors="strict") as f:
                file_context = f.read().strip()
            instruction = "Сделай краткую структурированную выжимку и выдели суть:"
        else:
            instruction = arg

    elif len(sys.argv) >= 3:
        # Два аргумента: файл и инструкция
        first_arg = sys.argv[1]
        if os.path.exists(first_arg):
            with open(first_arg, "r", encoding="utf-8", errors="strict") as f:
                file_context = f.read().strip()
            instruction = " ".join(sys.argv[2:])
        else:
            instruction = " ".join(sys.argv[1:])

    # Формируем итоговый промпт
    if file_context:
        full_prompt = f"{instruction}\n\nКОНТЕКСТ ДЛЯ АНАЛИЗА:\n---\n{file_context}\n---"
    else:
        full_prompt = instruction

    system_prompt = (
        "Ты — высокоэффективный локальный ИИ-ассистент, работающий оффлайн на Apple Silicon. "
        "Твоя задача — давать четкие, сжатые, конкретные ответы без лишних вводных слов, "
        "помогать в структурировании данных, поиске ошибок и классификации требований."
    )

    stream_generate(full_prompt, system_prompt=system_prompt)

if __name__ == "__main__":
    main()
