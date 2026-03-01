import re
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import REQUEST_TIMEOUT, REQUEST_HEADERS, MAX_CONCURRENT_REQUESTS, ECO_MODE, ECO_MAX_WORKERS, MAX_SITEMAP_CHECK
from .utils import get_status_text, get_status_type, create_session, check_url_status
class SitemapRobotAnalyzer:
    def __init__(self, base_url: str, session=None):
        self.base_url = base_url.rstrip('/')
        self.session = session or create_session()
    def analyze(self) -> dict:
        robots = self._analyze_robots()
        sitemap = self._analyze_sitemap(robots.get('sitemaps', []))
        return {
            'robots': robots,
            'sitemap': sitemap,
            'summary': self._generate_summary(robots, sitemap)
        }
    def _analyze_robots(self) -> dict:
        robots_url = f'{self.base_url}/robots.txt'
        try:
            response = self.session.get(
                robots_url,
                timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 200:
                content = response.text
                parsed = self._parse_robots(content)
                return {
                    'exists': True,
                    'url': robots_url,
                    'status_code': response.status_code,
                    'content': content,
                    'content_preview': content[:1000] if len(content) > 1000 else content,
                    'parsed': parsed,
                    'sitemaps': parsed.get('sitemaps', []),
                    'status': 'success',
                    'message': 'robots.txt file exists'
                }
            else:
                return {
                    'exists': False,
                    'url': robots_url,
                    'status_code': response.status_code,
                    'content': None,
                    'parsed': None,
                    'sitemaps': [],
                    'status': 'warning',
                    'message': f'robots.txt not found (HTTP {response.status_code})'
                }
        except Exception as e:
            return {
                'exists': False,
                'url': robots_url,
                'status_code': None,
                'content': None,
                'parsed': None,
                'sitemaps': [],
                'status': 'error',
                'message': f'Failed to access robots.txt: {str(e)}'
            }
    def _parse_robots(self, content: str) -> dict:
        result = {
            'user_agents': {},
            'sitemaps': [],
            'host': None
        }
        current_ua = None
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('    '):
                continue
            if ':' in line:
                directive, value = line.split(':', 1)
                directive = directive.strip().lower()
                value = value.strip()
                if directive == 'user-agent':
                    current_ua = value
                    if current_ua not in result['user_agents']:
                        result['user_agents'][current_ua] = {
                            'allow': [],
                            'disallow': []
                        }
                elif directive == 'disallow' and current_ua:
                    result['user_agents'][current_ua]['disallow'].append(value)
                elif directive == 'allow' and current_ua:
                    result['user_agents'][current_ua]['allow'].append(value)
                elif directive == 'sitemap':
                    result['sitemaps'].append(value)
                elif directive == 'host':
                    result['host'] = value
        return result
    def _analyze_sitemap(self, robots_sitemaps: list) -> dict:
        default_sitemap = f'{self.base_url}/sitemap.xml'
        sitemap_urls = list(set([default_sitemap] + robots_sitemaps))
        all_sitemaps = []
        all_page_urls = []
        for sitemap_url in sitemap_urls:
            sitemap_result = self._fetch_and_parse_sitemap(sitemap_url)
            all_sitemaps.append(sitemap_result)
            if sitemap_result['exists']:
                all_page_urls.extend(sitemap_result.get('urls', []))
        if all_page_urls:
            total_found = len(all_page_urls)
            urls_to_check = all_page_urls[:MAX_SITEMAP_CHECK]
            urls_to_check = self._check_sitemap_url_statuses(urls_to_check)
            unchecked_count = max(0, total_found - MAX_SITEMAP_CHECK)
            all_page_urls = urls_to_check
        broken_urls = [u for u in all_page_urls if u.get('status_code', 0) >= 400]
        redirect_urls = [u for u in all_page_urls if 300 <= u.get('status_code', 0) < 400]
        if not any(s['exists'] for s in all_sitemaps):
            status = 'error'
            message = 'sitemap.xml file not found'
        elif broken_urls:
            status = 'warning'
            message = f'{len(broken_urls)} broken URLs detected'
        else:
            status = 'success'
            message = f'{len(all_page_urls)} URLs checked, all valid'
            if unchecked_count > 0:
                message += f' (+{unchecked_count} URLs not checked)'
        primary_url = default_sitemap
        for s in all_sitemaps:
            if s['exists']:
                primary_url = s['url']
                break
        return {
            'url': primary_url,
            'sitemaps': all_sitemaps,
            'all_urls': all_page_urls,
            'total_urls': len(all_page_urls),
            'broken_urls': len(broken_urls),
            'redirect_urls': len(redirect_urls),
            'status': status,
            'message': message
        }
    def _fetch_and_parse_sitemap(self, sitemap_url: str) -> dict:
        try:
            response = self.session.get(
                sitemap_url,
                timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 200:
                content = response.text
                urls = self._parse_sitemap_xml(content, sitemap_url)
                return {
                    'exists': True,
                    'url': sitemap_url,
                    'status_code': response.status_code,
                    'type': 'sitemap_index' if '<sitemapindex' in content else 'urlset',
                    'urls': urls,
                    'url_count': len(urls),
                    'status': 'success',
                    'message': f'{len(urls)} URLs found'
                }
            else:
                return {
                    'exists': False,
                    'url': sitemap_url,
                    'status_code': response.status_code,
                    'type': None,
                    'urls': [],
                    'url_count': 0,
                    'status': 'warning' if sitemap_url.endswith('/sitemap.xml') else 'info',
                    'message': f'Sitemap not found (HTTP {response.status_code})'
                }
        except Exception as e:
            return {
                'exists': False,
                'url': sitemap_url,
                'status_code': None,
                'type': None,
                'urls': [],
                'url_count': 0,
                'status': 'error',
                'message': f'Failed to access sitemap: {str(e)}'
            }
    def _parse_sitemap_xml(self, content: str, sitemap_url: str) -> list:
        urls = []
        try:
            root = ET.fromstring(content)
            def strip_ns(tag):
                if '}' in tag:
                    return tag.split('}')[1]
                return tag
            def find_child(elem, local_name):
                for child in elem:
                    if strip_ns(child.tag) == local_name:
                        return child
                return None
            is_index = strip_ns(root.tag) == 'sitemapindex'
            if is_index:
                for child in root:
                    if strip_ns(child.tag) == 'sitemap':
                        loc = find_child(child, 'loc')
                        if loc is not None and loc.text:
                            urls.append({
                                'url': loc.text.strip(),
                                'type': 'sitemap',
                                'source': sitemap_url
                            })
            else:
                for child in root:
                    if strip_ns(child.tag) == 'url':
                        loc = find_child(child, 'loc')
                        if loc is not None and loc.text:
                            lastmod = find_child(child, 'lastmod')
                            changefreq = find_child(child, 'changefreq')
                            priority = find_child(child, 'priority')
                            urls.append({
                                'url': loc.text.strip(),
                                'type': 'page',
                                'source': sitemap_url,
                                'lastmod': lastmod.text.strip() if lastmod is not None and lastmod.text else None,
                                'changefreq': changefreq.text.strip() if changefreq is not None and changefreq.text else None,
                                'priority': priority.text.strip() if priority is not None and priority.text else None
                            })
        except Exception as e:
            loc_pattern = re.compile(r'<loc>([^<]+)</loc>')
            matches = loc_pattern.findall(content)
            for match in matches:
                urls.append({
                    'url': match.strip(),
                    'type': 'unknown',
                    'source': sitemap_url
                })
        return urls
    def _check_sitemap_url_statuses(self, urls: list) -> list:
        def check_single_url(url_data):
            result = check_url_status(self.session, url_data['url'])
            url_data['status_code'] = result['status_code']
            url_data['status_text'] = result['status_text']
            url_data['status_type'] = result['status_type']
            return url_data
        max_workers = ECO_MAX_WORKERS if ECO_MODE else MAX_CONCURRENT_REQUESTS
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_single_url, url): url for url in urls}
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        results.sort(key=lambda x: (x.get('status_code', 0) < 400, x.get('status_code', 0)))
        return results

    def _generate_summary(self, robots: dict, sitemap: dict) -> dict:
        issues = []
        if not robots['exists']:
            issues.append('robots.txt not found')
        if sitemap['status'] == 'error':
            issues.append('sitemap.xml not found')
        elif sitemap['broken_urls'] > 0:
            issues.append(f'{sitemap["broken_urls"]} broken URLs')
        return {
            'robots_exists': robots['exists'],
            'sitemap_exists': sitemap['status'] != 'error',
            'total_sitemap_urls': sitemap['total_urls'],
            'issues': issues,
            'status': 'error' if not robots['exists'] or sitemap['status'] == 'error' else
                     ('warning' if issues else 'success')
        }