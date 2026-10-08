from flask import Flask, render_template, request, jsonify, redirect, Response, stream_with_context
import json
from pathlib import Path
from pipeline import process_query_stream

app = Flask(__name__)

CHATS_FILE = Path(__file__).parent / "chats.json"


def _log(msg, symbol="•"):
    print(f"{symbol} {msg}", flush=True)


def load_chats():
    if CHATS_FILE.exists():
        try:
            with open(CHATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            _log(f"Загружено чатов: {len(data)} из {CHATS_FILE.name}", "📂")
            return data
        except Exception as e:
            _log(f"Не удалось загрузить чаты: {e}", "⚠️")
    _log("История чатов пуста", "📂")
    return {}


def save_chats(chats):
    try:
        with open(CHATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(chats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        _log(f"Не удалось сохранить чаты: {e}", "⚠️")


chats_db = load_chats()


class User:
    email = "user@example.com"


@app.route('/')
def index():
    return render_template('chat.html', chats=list(chats_db.values()), user=User())


@app.route('/landing')
def landing():
    return redirect('/')


def sse(payload):
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.route('/ask_stream', methods=['POST'])
def ask_stream():
    data = request.get_json()
    question = data.get('question', '').strip()
    chat_id = data.get('chat_id')

    if not question:
        return jsonify({'error': 'Пустой вопрос'}), 400

    print("", flush=True)
    _log("━━━ Запрос ━━━", "📨")
    _log(f"Текст: {question[:100]}{'...' if len(question) > 100 else ''}", "  ")

    if chat_id not in chats_db:
        chats_db[chat_id] = {
            "chat_id": chat_id,
            "title": question[:30] + ('…' if len(question) > 30 else ''),
            "messages": [],
        }

    @stream_with_context
    def generate():
        pipeline_answer = ""
        try:
            for event in process_query_stream(question):
                yield sse(event)
                if event.get("type") == "pipeline_answer":
                    pipeline_answer = event.get("text", "")
        except Exception as e:
            import traceback
            traceback.print_exc()
            pipeline_answer = pipeline_answer or f"⚠️ Критическая ошибка: {e}"

        if not pipeline_answer.strip():
            pipeline_answer = "⚠️ Не удалось получить ответ. Проверь LM Studio."

        chats_db[chat_id]['messages'].append({"role": "user", "content": question})
        chats_db[chat_id]['messages'].append({"role": "assistant", "content": pipeline_answer})
        save_chats(chats_db)
        _log(f"Ответ готов ({len(pipeline_answer)} симв.)", "✅")

        yield sse({"type": "answer", "text": pipeline_answer})
        yield sse({"type": "done"})

    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no',
        'Connection': 'keep-alive',
    })


@app.route('/delete_chat', methods=['POST'])
def delete_chat():
    data = request.get_json()
    chat_id = data.get('chat_id')
    if chat_id in chats_db:
        del chats_db[chat_id]
        save_chats(chats_db)
        return jsonify({'success': True})
    return jsonify({'success': False}), 404


if __name__ == '__main__':
    print("=" * 60, flush=True)
    print("  Star.Ai — сервер (только пайплайн)", flush=True)
    print(f"  Чатов в базе: {len(chats_db)}", flush=True)
    print(f"  Файл истории: {CHATS_FILE}", flush=True)
    print("=" * 60, flush=True)
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)