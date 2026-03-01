from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import REQUEST_TIMEOUT, REQUEST_HEADERS, MAX_CONCURRENT_REQUESTS, ECO_MODE, ECO_MAX_WORKERS
from .utils import get_status_text, get_status_type, create_session, check_url_status

_VALID_LANGUAGES = frozenset({
    'aa', 'ab', 'af', 'ak', 'am', 'an', 'ar', 'as', 'av', 'ay', 'az',
    'ba', 'be', 'bg', 'bh', 'bi', 'bm', 'bn', 'bo', 'br', 'bs',
    'ca', 'ce', 'ch', 'co', 'cr', 'cs', 'cu', 'cv', 'cy',
    'da', 'de', 'dv', 'dz',
    'ee', 'el', 'en', 'eo', 'es', 'et', 'eu',
    'fa', 'ff', 'fi', 'fj', 'fo', 'fr', 'fy',
    'ga', 'gd', 'gl', 'gn', 'gu', 'gv',
    'ha', 'he', 'hi', 'ho', 'hr', 'ht', 'hu', 'hy', 'hz',
    'ia', 'id', 'ie', 'ig', 'ii', 'ik', 'io', 'is', 'it', 'iu',
    'ja', 'jv',
    'ka', 'kg', 'ki', 'kj', 'kk', 'kl', 'km', 'kn', 'ko', 'kr', 'ks', 'ku', 'kv', 'kw', 'ky',
    'la', 'lb', 'lg', 'li', 'ln', 'lo', 'lt', 'lu', 'lv',
    'mg', 'mh', 'mi', 'mk', 'ml', 'mn', 'mr', 'ms', 'mt', 'my',
    'na', 'nb', 'nd', 'ne', 'ng', 'nl', 'nn', 'no', 'nr', 'nv', 'ny',
    'oc', 'oj', 'om', 'or', 'os',
    'pa', 'pi', 'pl', 'ps', 'pt',
    'qu',
    'rm', 'rn', 'ro', 'ru', 'rw',
    'sa', 'sc', 'sd', 'se', 'sg', 'si', 'sk', 'sl', 'sm', 'sn', 'so', 'sq', 'sr', 'ss', 'st', 'su', 'sv', 'sw',
    'ta', 'te', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tr', 'ts', 'tt', 'tw', 'ty',
    'ug', 'uk', 'ur', 'uz',
    'vi', 'vo',
    'wa', 'wo',
    'xh',
    'yi', 'yo',
    'za', 'zh', 'zu',
    'x-default'
})
class HreflangAnalyzer:
    def __init__(self, soup: BeautifulSoup, base_url: str, session=None):
        self.soup = soup
        self.base_url = base_url
        self.session = session or create_session()
    def analyze(self) -> dict:
        hreflangs = self._extract_hreflangs()
        if not hreflangs:
            return {
                'exists': False,
                'data': [],
                'has_x_default': False,
                'status': 'info',
                'message': 'Hreflang tags not found (Normal for single-language sites)'
            }
        hreflangs = self._check_hreflang_statuses(hreflangs)
        has_x_default = any(h['hreflang'] == 'x-default' for h in hreflangs)
        issues = self._check_issues(hreflangs, has_x_default)
        broken = [h for h in hreflangs if h.get('status_code', 0) >= 400]
        if broken:
            status = 'error'
            message = f'{len(broken)} broken hreflang URLs detected'
        elif issues:
            status = 'warning'
            message = f'{len(issues)} hreflang issues detected'
        else:
            status = 'success'
            message = f'{len(hreflangs)} hreflang tags correctly configured'
        return {
            'exists': True,
            'data': hreflangs,
            'total': len(hreflangs),
            'has_x_default': has_x_default,
            'issues': issues,
            'broken_count': len(broken),
            'status': status,
            'message': message
        }
    def _extract_hreflangs(self) -> list:
        hreflangs = []
        link_tags = self.soup.find_all('link', attrs={'rel': 'alternate', 'hreflang': True})
        for tag in link_tags:
            href = tag.get('href', '').strip()
            hreflang = tag.get('hreflang', '').strip()
            if href and hreflang:
                full_url = urljoin(self.base_url, href)
                hreflangs.append({
                    'hreflang': hreflang,
                    'href': href,
                    'full_url': full_url,
                    'language': self._parse_language(hreflang),
                    'region': self._parse_region(hreflang),
                    'is_x_default': hreflang.lower() == 'x-default'
                })
        return hreflangs
    def _parse_language(self, hreflang: str) -> str:
        if hreflang.lower() == 'x-default':
            return 'x-default'
        parts = hreflang.split('-')
        return parts[0].lower()
    def _parse_region(self, hreflang: str) -> str:
        if hreflang.lower() == 'x-default':
            return None
        parts = hreflang.split('-')
        if len(parts) > 1:
            return parts[1].upper()
        return None
    def _check_hreflang_statuses(self, hreflangs: list) -> list:
        def check_single_url(hreflang):
            result = check_url_status(self.session, hreflang['full_url'])
            hreflang['status_code'] = result['status_code']
            hreflang['status_text'] = result['status_text']
            hreflang['status_type'] = result['status_type']
            return hreflang
        max_workers = ECO_MAX_WORKERS if ECO_MODE else MAX_CONCURRENT_REQUESTS
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_single_url, h): h for h in hreflangs}
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        results.sort(key=lambda x: (x.get('status_code', 0) < 400, x.get('status_code', 0)))
        return results
    def _check_issues(self, hreflangs: list, has_x_default: bool) -> list:
        issues = []
        if not has_x_default and len(hreflangs) > 1:
            issues.append({
                'type': 'warning',
                'message': 'x-default hreflang not defined. Default language should be specified.'
            })
        seen_langs = {}
        for h in hreflangs:
            key = f"{h['language']}-{h['region']}"
            if key in seen_langs:
                issues.append({
                    'type': 'warning',
                    'message': f'Duplicate hreflang: {h["hreflang"]}'
                })
            seen_langs[key] = True
        for h in hreflangs:
            lang = h['language']
            if lang not in _VALID_LANGUAGES and lang != 'x-default':
                issues.append({
                    'type': 'info',
                    'message': f'Unknown language code: {lang} (May be valid but verify)'
                })
        return issues