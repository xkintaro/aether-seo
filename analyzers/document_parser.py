import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from config import REQUEST_TIMEOUT, REQUEST_HEADERS
from .url_utils import normalize_url, get_base_url, is_internal_link
from .utils import create_session
class DocumentParser:
    def __init__(self, url: str, session=None):
        self.original_url = url
        self.url = normalize_url(url)
        self.base_url = get_base_url(self.url)
        self.domain = urlparse(self.url).netloc
        self.html = None
        self.soup = None
        self.status_code = None
        self.response_time = None
        self.error = None
        self.headers = None
        self.session = session or create_session()
    def fetch(self) -> dict:
        start_time = time.time()
        try:
            response = self.session.get(
                self.url,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True,
                verify=True
            )
            self.response_time = round(time.time() - start_time, 3)
            self.status_code = response.status_code
            self.html = response.text
            self.headers = dict(response.headers)
            self.soup = BeautifulSoup(self.html, 'lxml')
            return {
                'success': True,
                'status_code': self.status_code,
                'response_time': self.response_time,
                'html': self.html,
                'soup': self.soup,
                'error': None,
                'headers': self.headers,
                'url': self.url,
                'base_url': self.base_url,
                'domain': self.domain
            }
        except requests.exceptions.Timeout:
            self.error = f"Timeout: No response received within {REQUEST_TIMEOUT} seconds"
        except requests.exceptions.SSLError as e:
            self.error = f"SSL Error: {str(e)}"
        except requests.exceptions.ConnectionError as e:
            self.error = f"Connection Error: Unreachable server"
        except requests.exceptions.RequestException as e:
            self.error = f"Request Error: {str(e)}"
        except Exception as e:
            self.error = f"Unexpected Error: {str(e)}"
        self.response_time = round(time.time() - start_time, 3)
        return {
            'success': False,
            'status_code': self.status_code,
            'response_time': self.response_time,
            'html': None,
            'soup': None,
            'error': self.error,
            'headers': None,
            'url': self.url,
            'base_url': self.base_url,
            'domain': self.domain
        }
    def resolve_url(self, href: str) -> str:
        if not href:
            return None
        return urljoin(self.url, href)
    def is_internal_link(self, url: str) -> bool:
        return is_internal_link(url, self.domain)