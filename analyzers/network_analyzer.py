import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import (
    REQUEST_TIMEOUT, REQUEST_HEADERS,
    CSS_SIZE_WARNING_KB, JS_SIZE_WARNING_KB,
    MAX_CONCURRENT_REQUESTS,
    ECO_MODE, ECO_DELAY, ECO_MAX_WORKERS,
    MAX_LINKS_TO_CHECK, MAX_ASSETS_TO_CHECK
)
from .utils import get_status_text, get_status_type, format_size, create_session, check_url_status
from .url_utils import is_internal_link as _is_internal_link
class NetworkAnalyzer:
    def __init__(self, soup: BeautifulSoup, base_url: str, domain: str, session=None, cached_elements=None):
        self.soup = soup
        self.base_url = base_url
        self.domain = domain
        self.session = session or create_session()
        self._cached_elements = cached_elements
    def analyze(self) -> dict:
        links = self._extract_and_check_links()
        assets = self._analyze_assets()
        known_urls = set()
        for a in assets.get('css', {}).get('data', []):
            known_urls.add(a.get('full_url', ''))
        for a in assets.get('js', {}).get('data', []):
            known_urls.add(a.get('full_url', ''))
        mixed_content = self._check_mixed_content(known_urls)
        return {
            'links': links,
            'assets': assets,
            'mixed_content': mixed_content,
            'summary': self._generate_summary(links, assets, mixed_content)
        }
    def _extract_and_check_links(self) -> dict:
        links = []
        a_tags = self._cached_elements.links if self._cached_elements else self.soup.find_all('a', href=True)
        seen_urls = set()
        unique_links = []
        for tag in a_tags:
            href = tag.get('href', '').strip()
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                continue
            full_url = urljoin(self.base_url, href)
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            is_internal = self._is_internal(full_url)
            is_absolute = href.startswith(('http://', 'https://'))
            link_type = 'absolute' if is_absolute else 'relative'
            unique_links.append({
                'href': href,
                'full_url': full_url,
                'text': tag.get_text(strip=True)[:100],
                'is_internal': is_internal,
                'type': link_type,
                'target': tag.get('target', ''),
                'rel': tag.get('rel', []),
                'nofollow': 'nofollow' in (tag.get('rel', []) or [])
            })
        links = self._check_link_statuses(unique_links)
        internal_links = [l for l in links if l['is_internal']]
        external_links = [l for l in links if not l['is_internal']]
        broken_internal = [l for l in internal_links if l.get('status_code', 0) >= 400]
        broken_external = [l for l in external_links if l.get('status_code', 0) >= 400]
        internal_links.sort(key=lambda x: (x.get('status_code', 0) < 400, x.get('status_code', 0)))
        external_links.sort(key=lambda x: (x.get('status_code', 0) < 400, x.get('status_code', 0)))
        return {
            'internal': {
                'total': len(internal_links),
                'broken': len(broken_internal),
                'data': internal_links
            },
            'external': {
                'total': len(external_links),
                'broken': len(broken_external),
                'data': external_links
            },
            'total': len(links),
            'total_broken': len(broken_internal) + len(broken_external),
            'link_types': {
                'absolute': len([l for l in links if l['type'] == 'absolute']),
                'relative': len([l for l in links if l['type'] == 'relative'])
            },
            'status': 'error' if (broken_internal or broken_external) else 'success'
        }
    def _check_link_statuses(self, links: list) -> list:
        def check_single_link(link):
            result = check_url_status(self.session, link['full_url'])
            link['status_code'] = result['status_code']
            link['status_text'] = result['status_text']
            link['status_type'] = result['status_type']
            return link
        links_to_check = links[:MAX_LINKS_TO_CHECK]
        unchecked = links[MAX_LINKS_TO_CHECK:]
        max_workers = ECO_MAX_WORKERS if ECO_MODE else MAX_CONCURRENT_REQUESTS
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_single_link, link): link for link in links_to_check}
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        for link in unchecked:
            link['status_code'] = None
            link['status_text'] = 'Not checked (limit)'
            link['status_type'] = 'unchecked'
        results.extend(unchecked)
        return results
    def _check_mixed_content(self, known_urls: set = None) -> dict:
        parsed_base = urlparse(self.base_url)
        if parsed_base.scheme != 'https':
            return {'has_mixed': False, 'items': [], 'status': 'success', 'message': 'Page is not HTTPS, mixed content check skipped.'}
        if known_urls is None:
            known_urls = set()
        mixed_items = []
        remaining_tags = {'img': 'src', 'iframe': 'src', 'embed': 'src', 'object': 'data', 'source': 'src'}
        if self._cached_elements:
            check_elements = (list(self._cached_elements.images) +
                            list(self._cached_elements.iframes) +
                            list(self._cached_elements.embed_tags) +
                            list(self._cached_elements.object_tags))
            check_elements.extend(self.soup.find_all('source'))
        else:
            check_elements = self.soup.find_all(list(remaining_tags.keys()))
        for el in check_elements:
            attr = remaining_tags.get(el.name)
            if attr:
                url = el.get(attr, '')
                if url and url.startswith('http://'):
                    mixed_items.append({
                        'tag': el.name,
                        'url': url,
                        'line': getattr(el, 'sourceline', 'Unknown')
                    })
        script_link_elements = []
        if self._cached_elements:
            script_link_elements = [(el, 'src') for el in self._cached_elements.scripts if el.get('src')]
            script_link_elements += [(el, 'href') for el in self._cached_elements.link_tags if el.get('href')]
        else:
            for tag_name, attr in [('script', 'src'), ('link', 'href')]:
                for el in self.soup.find_all(tag_name):
                    if el.get(attr):
                        script_link_elements.append((el, attr))
        for el, attr in script_link_elements:
            url = el.get(attr, '')
            if url and url.startswith('http://') and urljoin(self.base_url, url) not in known_urls:
                mixed_items.append({
                    'tag': el.name,
                    'url': url,
                    'line': getattr(el, 'sourceline', 'Unknown')
                })
        if mixed_items:
            return {
                'has_mixed': True,
                'observed_resources': mixed_items,
                'status': 'error',
                'message': f'{len(mixed_items)} insecure (HTTP) resources detected!'
            }
        return {
            'has_mixed': False,
            'observed_resources': [],
            'status': 'success',
            'message': 'All resources are secure (HTTPS)'
        }
    def _analyze_assets(self) -> dict:
        css_assets = self._check_asset_sizes(self._get_css_assets())
        js_assets = self._check_asset_sizes(self._get_js_assets())
        oversized_css = [a for a in css_assets if a.get('is_oversized', False)]
        oversized_js = [a for a in js_assets if a.get('is_oversized', False)]
        css_total_bytes = sum(a.get('size_bytes', 0) or 0 for a in css_assets)
        js_total_bytes = sum(a.get('size_bytes', 0) or 0 for a in js_assets)
        return {
            'css': {
                'total': len(css_assets),
                'oversized': len(oversized_css),
                'data': css_assets,
                'size_limit_kb': CSS_SIZE_WARNING_KB,
                'total_size_bytes': css_total_bytes
            },
            'js': {
                'total': len(js_assets),
                'oversized': len(oversized_js),
                'data': js_assets,
                'size_limit_kb': JS_SIZE_WARNING_KB,
                'total_size_bytes': js_total_bytes
            },
            'status': 'warning' if (oversized_css or oversized_js) else 'success'
        }
    def _get_css_assets(self) -> list:
        css_assets = []
        if self._cached_elements:
            link_tags = [t for t in self._cached_elements.link_tags if 'stylesheet' in (t.get('rel') or [])]
        else:
            link_tags = self.soup.find_all('link', rel='stylesheet')
        for tag in link_tags:
            href = tag.get('href', '')
            if href:
                css_assets.append({
                    'type': 'css',
                    'href': href,
                    'full_url': urljoin(self.base_url, href),
                    'is_external': not self._is_internal(urljoin(self.base_url, href))
                })
        return css_assets
    def _get_js_assets(self) -> list:
        js_assets = []
        if self._cached_elements:
            script_tags = [t for t in self._cached_elements.scripts if t.get('src')]
        else:
            script_tags = self.soup.find_all('script', src=True)
        for tag in script_tags:
            src = tag.get('src', '')
            if src:
                js_assets.append({
                    'type': 'js',
                    'href': src,
                    'full_url': urljoin(self.base_url, src),
                    'is_external': not self._is_internal(urljoin(self.base_url, src)),
                    'async': tag.has_attr('async'),
                    'defer': tag.has_attr('defer')
                })
        return js_assets
    def _check_asset_sizes(self, assets: list) -> list:
        def check_single_asset(asset):
            result = check_url_status(self.session, asset['full_url'])
            if result['status_code'] > 0:
                content_length = result.get('headers', {}).get('Content-Length')
                if content_length:
                    size_bytes = int(content_length)
                    size_kb = round(size_bytes / 1024, 2)
                    limit = CSS_SIZE_WARNING_KB if asset['type'] == 'css' else JS_SIZE_WARNING_KB
                    asset['size_bytes'] = size_bytes
                    asset['size_kb'] = size_kb
                    asset['size_formatted'] = format_size(size_bytes)
                    asset['is_oversized'] = size_kb > limit
                    asset['recommendation'] = f'File size exceeds {limit}KB limit. Compression/minify recommended.' if asset['is_oversized'] else None
                else:
                    asset['size_bytes'] = None
                    asset['size_kb'] = None
                    asset['size_formatted'] = 'Unknown'
                    asset['is_oversized'] = False
                    asset['recommendation'] = None
                asset['status_code'] = result['status_code']
            else:
                asset['size_bytes'] = None
                asset['size_kb'] = None
                asset['size_formatted'] = 'Inaccessible'
                asset['is_oversized'] = False
                asset['status_code'] = 0
                asset['error'] = result['status_text']
            return asset
        assets_to_check = assets[:MAX_ASSETS_TO_CHECK]
        unchecked = assets[MAX_ASSETS_TO_CHECK:]
        max_workers = ECO_MAX_WORKERS if ECO_MODE else MAX_CONCURRENT_REQUESTS
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_single_asset, asset): asset for asset in assets_to_check}
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        for asset in unchecked:
            asset['size_bytes'] = None
            asset['size_kb'] = None
            asset['size_formatted'] = 'Not checked (limit)'
            asset['is_oversized'] = False
            asset['status_code'] = None
        results.extend(unchecked)
        return results
    def _is_internal(self, url: str) -> bool:
        return _is_internal_link(url, self.domain)
    def _generate_summary(self, links: dict, assets: dict, mixed_content: dict) -> dict:
        total_issues = links['total_broken'] + assets['css']['oversized'] + assets['js']['oversized']
        if mixed_content['has_mixed']:
            total_issues += 1
        return {
            'total_links': links['total'],
            'broken_links': links['total_broken'],
            'total_assets': assets['css']['total'] + assets['js']['total'],
            'oversized_assets': assets['css']['oversized'] + assets['js']['oversized'],
            'mixed_content_issues': len(mixed_content.get('observed_resources', [])),
            'total_issues': total_issues,
            'status': 'error' if (links['total_broken'] > 0 or mixed_content['has_mixed']) else ('warning' if total_issues > 0 else 'success')
        }