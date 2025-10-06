import os
from flask import Flask, jsonify, request, send_from_directory
from redis import Redis
from dotenv import load_dotenv


load_dotenv()


REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
redis = Redis.from_url(REDIS_URL, decode_responses=True)


app = Flask(__name__, static_folder='../nginx/static')


@app.route('/api/health')
def health():
    try:
        redis.ping()
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
    return jsonify({'status': 'ok'})


@app.route('/api/visits', methods=['GET'])
def visits():
    try:
        count = redis.incr('visits')
    except Exception as e:
        # If Redis is unreachable return a helpful error
        return jsonify({'visits': None, 'error': str(e)}), 500
    return jsonify({'visits': int(count)})


@app.route('/api/echo', methods=['POST'])
def echo():
    data = request.get_json(silent=True) or {}
    return jsonify({'you_sent': data})


@app.route('/api/messages', methods=['GET', 'POST'])
def messages():
    """Simple guestbook stored in Redis as a list 'messages'.
    POST expects JSON: { "name": "Alice", "message": "Hello" }
    GET returns the latest 20 messages by default.
    """
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        name = data.get('name', 'anonymous')
        message = data.get('message', '')
        if not message:
            return jsonify({'error': 'message is required'}), 400
        import time
        entry = {'name': name, 'message': message, 'ts': int(time.time())}
        try:
            # store as JSON string
            import json
            redis.lpush('messages', json.dumps(entry))
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        return jsonify({'stored': entry}), 201

    # GET
    try:
        import json
        raw = redis.lrange('messages', 0, 19)
        msgs = [json.loads(x) for x in raw]
    except Exception as e:
        return jsonify({'messages': [], 'error': str(e)}), 500
    return jsonify({'messages': msgs})


# Optional: serve static from Flask when needed (normally nginx handles static)
@app.route('/static/<path:filename>')
def static_files(filename):
# serves from nginx static folder (useful for local dev without nginx)
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'nginx', 'static'))
    return send_from_directory(root, filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)