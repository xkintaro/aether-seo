import re
import threading
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urlparse as _urlparse
from config import REQUEST_TIMEOUT, REQUEST_HEADERS, CONNECTION_POOL_SIZE, HEAD_FALLBACK_CODES
def get_status_text(code: int) -> str:
    status_texts = {
        200: 'OK',
        201: 'Created',
        301: 'Moved Permanently',
        302: 'Found (Redirect)',
        304: 'Not Modified',
        400: 'Bad Request',
        401: 'Unauthorized',
        403: 'Forbidden',
        404: 'Not Found',
        500: 'Internal Server Error',
        502: 'Bad Gateway',
        503: 'Service Unavailable'
    }
    return status_texts.get(code, f'HTTP {code}')

def get_status_type(code: int) -> str:
    if 200 <= code < 300:
        return 'success'
    elif 300 <= code < 400:
        return 'redirect'
    elif 400 <= code < 500:
        return 'client_error'
    elif 500 <= code < 600:
        return 'server_error'
    return 'unknown'

def format_size(size_bytes: int) -> str:
    if not size_bytes:
        return '0 B'
    try:
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
    except (ValueError, TypeError):
        return '0 B'

def create_session() -> requests.Session:
    session = requests.Session()
    adapter = HTTPAdapter(
        pool_connections=CONNECTION_POOL_SIZE,
        pool_maxsize=CONNECTION_POOL_SIZE,
        max_retries=Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[502, 503, 504]
        )
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers.update(REQUEST_HEADERS)
    return session

_thread_local = threading.local()

def get_thread_session():
    if not hasattr(_thread_local, 'session'):
        _thread_local.session = create_session()
    return _thread_local.session

_head_unsupported_domains: set = set()

def check_url_status(session, url, timeout=None):
    if timeout is None:
        timeout = REQUEST_TIMEOUT // 2
    domain = _urlparse(url).netloc
    try:
        if domain not in _head_unsupported_domains:
            response = session.head(url, timeout=timeout, allow_redirects=True)
            if response.status_code in HEAD_FALLBACK_CODES:
                _head_unsupported_domains.add(domain)
                response = session.get(url, timeout=timeout, allow_redirects=True, stream=True)
                response.close()
        else:
            response = session.get(url, timeout=timeout, allow_redirects=True, stream=True)
            response.close()
        return {
            'status_code': response.status_code,
            'status_text': get_status_text(response.status_code),
            'status_type': get_status_type(response.status_code),
            'headers': response.headers
        }
    except requests.exceptions.Timeout:
        return {'status_code': 0, 'status_text': 'Timeout', 'status_type': 'error'}
    except requests.exceptions.SSLError:
        return {'status_code': 0, 'status_text': 'SSL Error', 'status_type': 'error'}
    except requests.exceptions.ConnectionError:
        return {'status_code': 0, 'status_text': 'Connection Error', 'status_type': 'error'}
    except Exception as e:
        return {'status_code': 0, 'status_text': str(e)[:50], 'status_type': 'error'}

def turkish_lower(text: str) -> str:
    mapping = {'I': 'ı', 'İ': 'i'}
    text = ''.join(mapping.get(c, c) for c in str(text))
    return text.lower()

def clean_text(text: str) -> str:
    text = turkish_lower(text)
    text = re.sub(r'[^\w\s]', ' ', text)
    return ' '.join(text.split())

def get_tokens(text: str) -> set:
    return set(w for w in text.split() if len(w) > 1)
