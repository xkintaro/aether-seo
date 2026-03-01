import json
import queue
import threading
import uuid

from flask import Flask, render_template, redirect, url_for, request, jsonify, Response
from urllib.parse import unquote
from cachetools import TTLCache
from seo_analyzer import SEOAnalyzer
from analyzers.utils import format_size as _format_size
from analyzers.url_utils import strip_protocol as normalize_url, build_full_url
from config import (
    ECO_CPU_LABEL, COPYRIGHT_TEXT, SOCIAL_GITHUB, SOCIAL_DISCORD,
    APP_TITLE, CACHE_MAXSIZE, CACHE_TTL
)
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.jinja_env.globals.update(min=min, max=max)
app.jinja_env.filters['format_size'] = _format_size

@app.context_processor
def inject_global_config():
    return dict(
        eco_cpu_label=ECO_CPU_LABEL,
        copyright_text=COPYRIGHT_TEXT,
        social_github=SOCIAL_GITHUB,
        social_discord=SOCIAL_DISCORD,
        app_title=APP_TITLE
    )
@app.route('/')
def index() -> str:
    return render_template('index.html')
_cache_lock = threading.Lock()
TEMP_CACHE = TTLCache(maxsize=CACHE_MAXSIZE, ttl=CACHE_TTL)
@app.route('/api/stream_analyze')
def stream_analyze() -> Response:
    url = request.args.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL required'}), 400
    clean_url = normalize_url(url)
    decoded_domain = unquote(clean_url)
    full_url = build_full_url(decoded_domain)
    report_key = uuid.uuid4().hex[:12]
    def generate():
        analyzer = SEOAnalyzer(full_url)

        q = queue.Queue()
        def runner():
            try:
                result = analyzer.analyze(progress_callback=lambda m: q.put(('msg', m)))
                q.put(('done', result))
            except Exception as e:
                q.put(('error', str(e)))
        t = threading.Thread(target=runner, daemon=True)
        t.start()
        while True:
            try:
                item = q.get(timeout=120)
                type_, payload = item
                if type_ == 'msg':
                    yield f"data: {json.dumps({'msg': payload}, ensure_ascii=False)}\n\n"
                elif type_ == 'done':
                    with _cache_lock:
                        TEMP_CACHE[report_key] = payload
                    yield f"data: {json.dumps({'redirect': f'/report?key={report_key}'}, ensure_ascii=False)}\n\n"
                    break
                elif type_ == 'error':
                    yield f"data: {json.dumps({'error': payload}, ensure_ascii=False)}\n\n"
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'error': 'Analysis timed out (120s)'}, ensure_ascii=False)}\n\n"
                break
    return Response(generate(), mimetype='text/event-stream')
@app.route('/report')
def report() -> str:
    report_key = request.args.get('key', '').strip()
    if not report_key:
        return redirect(url_for('index'))
    with _cache_lock:
        results = TEMP_CACHE.get(report_key, None)
    if results is not None:
        domain = results.get('url', '')
        if domain:
            domain = normalize_url(domain)
        return render_template(
            'report.html',
            domain=domain,
            url=results.get('url', ''),
            data=results
        )
    return redirect(url_for('index'))
@app.route('/api/analyze', methods=['POST'])
def api_analyze() -> Response:
    url = request.json.get('url', '').strip() if request.is_json else request.form.get('url', '').strip()
    if not url:
        return jsonify({'error': 'URL required'}), 400
    clean_url = normalize_url(url)
    decoded_domain = unquote(clean_url)
    full_url = build_full_url(decoded_domain)
    try:
        analyzer = SEOAnalyzer(full_url)
        results = analyzer.analyze()
        report_key = uuid.uuid4().hex[:12]
        with _cache_lock:
            TEMP_CACHE[report_key] = results
        return jsonify({'success': True, 'key': report_key, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=7663, threaded=True)