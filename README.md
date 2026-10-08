# Star.Ai

Локальный веб-чат с ИИ через LM Studio. Запросы прогоняются через 4-ступенчатый пайплайн: анализ → черновик → критика → синтез. Всё работает офлайн, ничего не уходит в интернет.
(Ответ нейросети улучшаеться в 4-5 раз)

## Возможности

- 🌐 Чат в браузере, интерфейс на русском и английском
- 🧠 Пайплайн из 4 шагов для качественных ответов
- ⚡ Стриминг шагов обработки в реальном времени
- 💾 История чатов сохраняется в `chats.json`
- 📝 Подсветка кода, копирование и скачивание блоков
- 🎨 Тёмная и светлая темы, настройка размера текста
- 🔒 Полностью локально — работает без интернета

## Требования

- Windows / macOS / Linux
- Python 3.10+
- [LM Studio](https://lmstudio.ai/) с загруженной моделью
- Любая instruct-модель (рекомендую glm 4.7 flash-coder, Qwen3-8b-deepseek-r1, GPT-OSS 20B)

## Установка

1. Установи Python с [python.org](https://www.python.org/), при установке отметь **Add Python to PATH**
2. Установи зависимости:
   ```bash
   pip install flask requests
   ```
3. Скачай LM Studio, загрузи модель, во вкладке **Local Server** нажми **Start Server** (порт 1234)
4. Скопируй проект в любую папку

## Запуск

**Windows:** двойной клик по `start.bat` — скрипт сам найдёт Python, установит Flask, откроет браузер.

**Вручную:**
```bash
python app.py
```
Открой `http://127.0.0.1:5000`

## Структура

```
project/
├── app.py              # Flask-сервер, SSE, история чатов
├── pipeline.py         # 4-ступенчатый пайплайн
├── start.bat           # Автозапуск для Windows
├── chats.json          # История (создаётся автоматически)
└── templates/
    └── chat.html       # Интерфейс
```

## Как работает пайплайн

1. **Анализ** — модель разбирает запрос: тема, сложность, формат ответа
2. **Черновик** — пишет первый вариант ответа
3. **Критика** — проверяет черновик на ошибки и пробелы
4. **Синтез** — переписывает с учётом замечаний

Если критик считает черновик идеальным — шаги 3-4 пропускаются.

## Настройка

В `pipeline.py`:
- `LM_STUDIO_URL` — адрес API (по умолчанию `http://localhost:1234/v1/chat/completions`)
- `REQUEST_TIMEOUT` — таймаут запроса (по умолчанию 6 часов)
- `PROMPT_*` — тексты промптов

## Лицензия

MIT

---

# Star.Ai (English)

Local web chat with AI via LM Studio. Requests run through a 4-stage pipeline: analysis → draft → critique → synthesis. Fully offline, nothing leaves your machine.

## Features

- 🌐 Browser-based chat, Russian and English UI
- 🧠 4-stage pipeline for high-quality answers
- ⚡ Real-time streaming of pipeline steps
- 💾 Chat history saved to `chats.json`
- 📝 Code highlighting, copy and download buttons
- 🎨 Dark and light themes, adjustable text size
- 🔒 Fully local — works without internet

## Requirements

- Windows / macOS / Linux
- Python 3.10+
- [LM Studio](https://lmstudio.ai/) with a loaded model
- Any instruct model (glm 4.7 flash-coder, Qwen3-8b-deepseek-r1, GPT-OSS 20B recommended)

## Installation

1. Install Python from [python.org](https://www.python.org/), check **Add Python to PATH**
2. Install dependencies:
   ```bash
   pip install flask requests
   ```
3. Download LM Studio, load a model, click **Start Server** on the **Local Server** tab (port 1234)
4. Copy the project to any folder

## Running

**Windows:** double-click `start.bat` — it finds Python, installs Flask, opens the browser.

**Manually:**
```bash
python app.py
```
Open `http://127.0.0.1:5000`

## Structure

```
project/
├── app.py              # Flask server, SSE, chat history
├── pipeline.py         # 4-stage pipeline
├── start.bat           # Windows auto-launcher
├── chats.json          # History (created automatically)
└── templates/
    └── chat.html       # UI
```

## How the pipeline works

1. **Analysis** — model analyzes the request: topic, complexity, answer format
2. **Draft** — writes the first version of the answer
3. **Critique** — checks for errors and gaps
4. **Synthesis** — rewrites based on feedback

If the critic finds the draft perfect, steps 3-4 are skipped.

## Configuration

In `pipeline.py`:
- `LM_STUDIO_URL` — API endpoint (default `http://localhost:1234/v1/chat/completions`)
- `REQUEST_TIMEOUT` — request timeout (default 6 hours)
- `PROMPT_*` — prompt templates

## License

MIT
