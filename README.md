# 🚀 mac-m1-zero-token

> **Экосистема локальных утилит macOS (Apple Silicon M1/M2/M3/M4) для аппаратной разгрузки LLM (Gemini CLI, Codex, Claude Code) и работы с 0 расходом облачных токенов.**

---

## 🎯 Философия проекта
Современные мультимодальные модели (Gemini 2.5 Pro, Claude 3.5 Sonnet, GPT-4o) берут огромную плату за «тяжелые» входные данные: скриншоты, сканы документов, PDF-файлы на 100 страниц и аудиозаписи. Загрузка нескольких картинок или скана договора способна сжечь **100 000+ токенов** за один запрос и мгновенно забить контекстную память агента «шумом».

**Принцип mac-m1-zero-token:**
1. Ни одного пикселя или аудиобайта не должно отправляться в облачный API.
2. Процессор Apple Silicon (Neural Engine, аппаратные медиа-декодеры, Unified Memory) выполняет всю черновую работу **локально, оффлайн, мгновенно и бесплатно**.
3. В облачную LLM попадает **только концентрированный, чистый текст (Markdown / TXT)**.

---

## 📊 Дорожная карта внедрения (Прогресс: 7 из 7 — 100% ГОТОВО!)

| № | Направление | Инструмент | Статус | Экономия токенов |
|---|---|---|:---:|:---:|
| **1** | **Локальный OCR & Extractor** | `ocr` (Swift + Apple Vision + PDFKit + Pandoc) | ✅ **ГОТОВО** | 100% (ноль картинок в API) |
| **2** | **Очистка ТЗ и документов от «воды»** | `cleandoc` (Boilerplate Stripper & Table normalizer) | ✅ **ГОТОВО** | ~85% контекста документов |
| **3** | **Малые локальные нейросети (SLM)** | `localai` (Qwen 2.5 3B / Ollama на Apple Metal M1) | ✅ **ГОТОВО** | 100% на черновую обработку |
| **4** | **Локальный поиск и индексация** | `localsearch` (ripgrep по базе знаний и пресейлам) | ✅ **ГОТОВО** | ~95% токенов на контекстный поиск |
| **5** | **Локальная валидация артефактов** | `wbsvalid`, `wbs2xlsx`, `checkodoo` (Odoo 18/19 Linter) | ✅ **ГОТОВО** | Предотвращает ошибки и циклы правок |
| **6** | **Карта документа** | `docmap` (Генератор структуры Markdown со строками) | ✅ **ГОТОВО** | Точечное извлечение нужных строк |
| **7** | **Локальная диагностика** | `localdoctor` (Проверка зависимостей и экосистемы) | ✅ **ГОТОВО** | Стабильность среды |

---

## 🛠️ Установка на любой Mac за 1 минуту

Если вы переехали на новый компьютер Mac или обновили систему:

```bash
git clone git@github.com:Santory12/mac-m1-zero-token.git
cd mac-m1-zero-token
./install.sh
```

Скрипт автоматически:
1. Скомпилирует нативный ARM64-бинарник `ocr` с оптимизацией `-O`.
2. Установит все утилиты в `~/.local/bin/`.
3. Запустит локальный движок `ollama` и загрузит модель `qwen2.5:3b`.
4. Добавит пути в `PATH` в `~/.zshrc`.

---

## ⚡ Полный каталог инструментов

### 1. `ocr` — Нативный аппаратный OCR (Apple Vision)
* **Мгновенный скриншот:** Нажмите `Cmd + Ctrl + Shift + 4` -> в терминале `ocr` -> текст уже в буфере обмена (`Cmd + V`).
* **Распознавание файлов:** `ocr image.png` или `ocr contract.pdf` (вычитывает текст или делает OCR сканов).
* **Конвертация Word:** `ocr requirements.docx` (переводит Word в чистый Markdown).

### 2. `cleandoc` — Очистка ТЗ от юридической воды
* **Срезает до 85% объема:** Вырезает «Предмет договора», NDA, порядок расчетов, форс-мажор, колонтитулы и номера страниц.
* **Использование:** `cleandoc client_tz.docx` -> создает компактный `client_tz_cleaned.md` и выводит отчет экономии токенов.

### 3. `localai` — Малые нейросети без интернета (Metal M1)
* **Локальный интеллект:** Работает на Qwen 2.5 3B (весит 1.9 ГБ, использует Metal GPU).
* **Сценарии:**
  ```bash
  localai "Сравни PostgreSQL и SQLite"
  localai rfp_cleaned.md "Разложи требования по модулям Odoo"
  cat error.log | localai "Найди критические ошибки"
  ```

### 4. `localsearch` — No-Token Search по пресейлам
* **Мгновенный поиск:** Сканирует тысячи строк базы знаний за 0.05 секунды через `ripgrep`.
* **Использование:**
  ```bash
  localsearch "KSeF"
  localsearch "NovaZone 3PL"
  ```

### 5. Валидаторы артефактов (Quality Gates)
* **`wbsvalid <файл.csv>`:** Проверка WBS Gold Standard (11 колонок, точка с запятой, математика, фазы).
* **`wbs2xlsx <файл.csv>`:** Автоматическая генерация форматированного клиентского 2-вкладочного Excel.
* **`checkodoo <файл.xml|py>`:** Локальный линтер Odoo 18/19 (проверка запрета `<tree>`, лишних `<data>`, правильности записей и синтаксиса Python).

### 6. `docmap` — Карта документа
* **Назначение:** Генерирует оглавление Markdown-файла с точными номерами строк (начало и конец раздела) и оценкой токенов.
* **Использование:** `docmap document_full.md` -> Выдает ИИ-агенту карту, чтобы он извлекал только нужный кусок (`start_line=10`, `end_line=50`).

### 7. `localdoctor` — Диагностика экосистемы
* **Назначение:** Единая команда для проверки целостности всех утилит, зависимостей ($PATH, pandoc, swiftc, ripgrep) и наличия локальных моделей (Ollama).
* **Использование:** `localdoctor` -> Выводит подробный отчет о состоянии всех модулей.

---

## 🤖 Инструкция для ИИ-агентов (Gemini CLI, Codex, Claude Code)

### Железный мандат (Zero-Media & Zero-Image Mandate):
Каждый ИИ-агент, работающий в этой системе, обязан соблюдать следующие правила:
1. **Запрет сырых медиа в API:** Никогда не отправлять аудио, видео или сырые картинки в облако.
2. **Локальный OCR:** При получении картинки или PDF сначала выполнить `ocr <файл>` и работать только с текстом.
3. **Очистка ТЗ:** Перед глубоким анализом больших документов выполнить `cleandoc <файл>`.
4. **Поиск прецедентов:** Искать информацию через `localsearch <запрос>` вместо считывания десятков файлов пресейлов.
5. **Валидация перед показом:** Всегда проверять сметы через `wbsvalid` и код Odoo через `checkodoo`.

---

## 👤 Автор и поддержка
* **Автор:** Mikhail (Santory12)
* **Платформа:** macOS Sequoia / Sonoma (Apple Silicon M1 8GB+)
* **Репозиторий:** [https://github.com/Santory12/mac-m1-zero-token](https://github.com/Santory12/mac-m1-zero-token)


## Reliability checks (2026-11-06)

Run `python3 checks/regression.py` with Python containing `openpyxl`.
The installer selects and pins a Python interpreter with this dependency; it no longer
starts Ollama or downloads models. Run the installer from any working directory.

- `cleandoc` uses fresh OCR stdout, never a pre-existing sidecar file.
  Full text means unabridged extraction, not guaranteed coverage of the original.
  Compact output is auxiliary and can omit requirements; consult full text.
- `ocr file.pdf --force-ocr` recognizes every page for mixed scanned/text PDFs.
  Default mode prefers existing text. Empty OCR pages cause a failure requiring review.
  File mode leaves the clipboard alone, reports failures, and overwrites its `.txt`/`.md`
  output only after extraction. No raw media is sent to a model.
- `localsearch` uses literal strings and reports execution errors separately.
- `wbsvalid` rejects negative, nonfinite, nonnumeric hours and inverted ranges.
  It does not verify business completeness or reconcile declared summary totals.
- `wbs2xlsx en.csv ru.csv output.xlsx` supports decimal hours and stores text as
  literal cells. Both input files need 11 columns. It does not translate content.
- `checkodoo` is a syntax/heuristic check; install and runtime tests remain necessary.
- `transcribe_local` uses isolated temporary files. The existing backend is Python
  Whisper, not whisper.cpp; Metal acceleration is not verified. Whisper may download
  a missing model; provision/cache models before offline use.
