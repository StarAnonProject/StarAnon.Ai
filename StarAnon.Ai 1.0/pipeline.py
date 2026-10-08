import time
import requests
import json
import re

# ==================== НАСТРОЙКИ ====================
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "local-model"
MAX_RETRIES = 2
RETRY_DELAY = 3
REQUEST_TIMEOUT = 21600

# ==================== ПРОМПТЫ (без JSON) ====================
PROMPT_ANALYZE = """Ты — аналитик запросов в составе AI-пайплайна. Твой анализ читает
и использует следующий модуль, который будет писать черновик ответа.
Проанализируй запрос пользователя обычным текстом, кратко (3-6 предложений):
- какая тема и суть запроса
- насколько запрос сложный (простой/средний/сложный)
- есть ли эмоциональный подтекст, который стоит учесть
- какой формат ответа уместен (список, развёрнутый текст, пошаговый план и т.д.)
- что человек ДЕЙСТВИТЕЛЬНО хочет получить, включая то, что не сказано прямо
Пиши просто связным текстом, без списков полей, без разметки, без JSON.
Message:"""

PROMPT_DRAFT = """Ты — генератор глубоких, полезных и точных ответов. Ты получаешь
не только запрос пользователя, но и его предварительный анализ —
используй его, чтобы ответ точнее попадал в цель.
Напиши черновик полноценного ответа на запрос пользователя, учитывая анализ.
В конце, отдельным коротким абзацем, честно напиши, в чём ты не уверен
в этом ответе (если не уверен — так и скажи; если уверен полностью — так и напиши).
Пиши обычным текстом, без JSON и без служебной разметки.
Message:"""

PROMPT_CRITIC = """Ты — строгий, но конструктивный критик и логический аудитор.
Твоя задача — находить реальные проблемы, а не придираться формально.
Не занижай оценку намеренно и не ищи проблемы там, где их нет —
если черновик действительно хорош, честно признай это.
Проверь черновик по следующим критериям:
1. Логические противоречия или неточности
2. Пропущенные важные аспекты запроса
3. Несоответствие формату/тону, заданному в анализе
4. Избыточность или наоборот — недостаточная глубина
5. Стилистические проблемы
Если черновик хорош и не требует правок — начни свой ответ ровно со слова
"ИДЕАЛЬНО" и больше ничего не пиши.
Если есть проблемы — начни ответ со слова "ТРЕБУЕТ ПРАВОК", затем опиши
обычным текстом: какие конкретно слабые места ты нашёл и какой план
исправлений предлагаешь.
Пиши обычным текстом, без JSON и без служебной разметки.
Message:"""

PROMPT_SYNTHESIZE = """Ты — финальный синтезатор ответов. Твоя задача — переписать черновик,
устранив все указанные критиком слабые места, следуя его плану исправлений,
но сохранив всё, что в черновике было хорошо. Не переписывай с нуля то,
что критик не отметил как проблему — вноси точечные исправления.
Верни ТОЛЬКО финальный текст ответа для пользователя — без пометок вроде
"вот исправленная версия", без ссылок на критику, без служебных комментариев.
Это должен быть самодостаточный, готовый к показу пользователю текст.
Message:"""

# ==================== ВЫЗОВ МОДЕЛИ ====================
def call_llm(message_text: str, max_tokens: int = 10000, temperature: float = 0.7) -> str:
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": message_text}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }
    try:
        response = requests.post(LM_STUDIO_URL, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Не могу подключиться к LM Studio. Убедись, что:\n"
            "  1. LM Studio открыт\n"
            "  2. Модель загружена и выбрана\n"
            "  3. Во вкладке Local Server нажат Start Server"
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Таймаут {REQUEST_TIMEOUT} секунд превышен.")
    data = response.json()
    choice = data["choices"][0]
    message = choice.get("message", {})
    content = message.get("content", "")
    reasoning = message.get("reasoning_content", "")
    if not content.strip() and reasoning.strip():
        content = reasoning
    elif not content.strip():
        raise RuntimeError("Модель вернула пустой ответ.")
    return content

def call_llm_with_retry(message_text: str, max_tokens: int = 10000, temperature: float = 0.7,
                        retries: int = MAX_RETRIES, delay: int = RETRY_DELAY) -> str:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            return call_llm(message_text, max_tokens, temperature)
        except RuntimeError as e:
            last_error = e
            print(f"⚠️ Попытка {attempt} из {retries} не удалась: {e}")
            if attempt < retries:
                print(f"   Повторная попытка через {delay} сек...")
                time.sleep(delay)
            else:
                print("❌ Все попытки исчерпаны.")
                raise last_error
    raise RuntimeError("Не удалось получить ответ после всех попыток.")

def print_step(name: str, text: str):
    print(f"\n--- {name} ---")
    print(text)

def fallback_analysis(query: str) -> str:
    return (f"Тема: {query[:50]}... Сложность: средняя. Эмоциональный тон: нейтральный. "
            f"Формат ответа: развёрнутый текст. Пользователь хочет получить содержательный ответ по теме.")

# ==================== ОСНОВНАЯ ФУНКЦИЯ ====================
def process_query(user_query: str) -> str:
    # Шаг 1: Анализ (увеличен до 5000)
    try:
        analysis_text = call_llm_with_retry(PROMPT_ANALYZE + user_query, max_tokens=8000)
    except RuntimeError as e:
        print(f"⚠️ Ошибка при анализе: {e}")
        analysis_text = fallback_analysis(user_query)
    print_step("1. АНАЛИЗ", analysis_text)

    # Шаг 2: Черновик (увеличен до 7500)
    draft_prompt = (
        PROMPT_DRAFT
        + "\n\nАнализ запроса:\n"
        + analysis_text
        + "\n\nЗапрос пользователя:\n"
        + user_query
    )
    try:
        draft_raw = call_llm_with_retry(draft_prompt, max_tokens=8000)
    except RuntimeError as e:
        print(f"⚠️ Ошибка при черновике: {e}")
        return "Извините, не удалось сгенерировать ответ. Попробуйте переформулировать вопрос."
    print_step("2. ЧЕРНОВИК", draft_raw)

    # Шаг 3: Критика (увеличен до 3750)
    critic_prompt = (
        PROMPT_CRITIC
        + "\n\nИсходный запрос:\n"
        + user_query
        + "\n\nЧерновик:\n"
        + draft_raw
    )
    try:
        critique_raw = call_llm_with_retry(critic_prompt, max_tokens=8000)
    except RuntimeError as e:
        print(f"⚠️ Ошибка при критике: {e}")
        return draft_raw
    print_step("3. КРИТИКА", critique_raw)

    if critique_raw.strip().startswith("ИДЕАЛЬНО"):
        print("✅ Черновик идеален – возвращаем.")
        return draft_raw
    if len(critique_raw.strip()) < 10:
        print("⚠️ Критика короткая – возвращаем черновик.")
        return draft_raw

    # Шаг 4: Синтез (увеличен до 7500)
    synth_prompt = (
        PROMPT_SYNTHESIZE
        + "\n\nИсходный запрос:\n"
        + user_query
        + "\n\nЧерновик:\n"
        + draft_raw
        + "\n\nКритика:\n"
        + critique_raw
    )
    try:
        final_answer = call_llm_with_retry(synth_prompt, max_tokens=20000)
    except RuntimeError as e:
        print(f"⚠️ Ошибка при синтезе: {e}")
        return draft_raw
    print_step("4. СИНТЕЗ", final_answer)
    return final_answer if final_answer.strip() else draft_raw

def process_query_stream(user_query: str):
    """SSE-версия пайплайна: стримит шаги в UI."""
    final_answer = ""
    try:
        print("\n🧠 Модуль Разум 1.0", flush=True)

        yield {"type": "pipeline_step", "step": "analyze", "status": "start"}
        print("  [1/4] Анализ...", flush=True)
        try:
            analysis_text = call_llm_with_retry(PROMPT_ANALYZE + user_query, max_tokens=8000)
        except RuntimeError as e:
            print(f"  ⚠️ Ошибка анализа: {e}", flush=True)
            analysis_text = fallback_analysis(user_query)
        yield {"type": "pipeline_step", "step": "analyze", "status": "done"}
        print(f"  ✓ Анализ ({len(analysis_text)} симв.)", flush=True)

        yield {"type": "pipeline_step", "step": "draft", "status": "start"}
        print("  [2/4] Черновик...", flush=True)
        draft_prompt = (PROMPT_DRAFT + "\n\nАнализ запроса:\n" + analysis_text
                        + "\n\nЗапрос пользователя:\n" + user_query)
        try:
            draft_raw = call_llm_with_retry(draft_prompt, max_tokens=8000)
        except RuntimeError as e:
            print(f"  ⚠️ Ошибка черновика: {e}", flush=True)
            yield {"type": "pipeline_answer", "text": f"⚠️ Не удалось сгенерировать ответ: {e}"}
            return
        yield {"type": "pipeline_step", "step": "draft", "status": "done"}
        print(f"  ✓ Черновик ({len(draft_raw)} симв.)", flush=True)

        yield {"type": "pipeline_step", "step": "critic", "status": "start"}
        print("  [3/4] Критика...", flush=True)
        critic_prompt = (PROMPT_CRITIC + "\n\nИсходный запрос:\n" + user_query
                         + "\n\nЧерновик:\n" + draft_raw)
        try:
            critique_raw = call_llm_with_retry(critic_prompt, max_tokens=8000)
        except RuntimeError as e:
            print(f"  ⚠️ Ошибка критики: {e}", flush=True)
            yield {"type": "pipeline_step", "step": "critic", "status": "skip"}
            yield {"type": "pipeline_answer", "text": draft_raw}
            return

        if critique_raw.strip().startswith("ИДЕАЛЬНО") or len(critique_raw.strip()) < 10:
            print("  ✓ Критик: идеально, синтез не нужен", flush=True)
            yield {"type": "pipeline_step", "step": "critic", "status": "skip"}
            yield {"type": "pipeline_answer", "text": draft_raw}
            return
        yield {"type": "pipeline_step", "step": "critic", "status": "done"}
        print(f"  ✓ Критика ({len(critique_raw)} симв.)", flush=True)

        yield {"type": "pipeline_step", "step": "synthesize", "status": "start"}
        print("  [4/4] Синтез...", flush=True)
        synth_prompt = (PROMPT_SYNTHESIZE + "\n\nИсходный запрос:\n" + user_query
                        + "\n\nЧерновик:\n" + draft_raw
                        + "\n\nКритика:\n" + critique_raw)
        try:
            final_answer = call_llm_with_retry(synth_prompt, max_tokens=20000)
        except RuntimeError as e:
            print(f"  ⚠️ Ошибка синтеза: {e}", flush=True)
            yield {"type": "pipeline_step", "step": "synthesize", "status": "skip"}
            yield {"type": "pipeline_answer", "text": draft_raw}
            return
        yield {"type": "pipeline_step", "step": "synthesize", "status": "done"}
        print(f"  ✓ Синтез ({len(final_answer)} симв.)", flush=True)

        if not final_answer.strip():
            final_answer = draft_raw

        yield {"type": "pipeline_answer", "text": final_answer}

    except Exception as e:
        print(f"  ❌ Внутренняя ошибка: {e}", flush=True)
        fb = final_answer if final_answer.strip() else f"⚠️ Внутренняя ошибка: {e}"
        yield {"type": "pipeline_answer", "text": fb}