from bs4 import BeautifulSoup, NavigableString
from collections import Counter
import re

TURKISH_STOP_WORDS = {
    've', 'ile', 'bir', 'bu', 'da', 'de', 'için', 'ama', 'ancak', 'gibi',
    'daha', 'çok', 'en', 'ne', 'ki', 'mi', 'mu', 'mı', 'mü', 'ya', 'hem',
    'veya', 'ise', 'olan', 'olarak', 'kadar', 'sonra', 'önce', 'üzere',
    'dolayı', 'göre', 'rağmen', 'karşı', 'aracılığıyla', 'tarafından',
    'her', 'tüm', 'bütün', 'bazı', 'hiç', 'şu', 'o', 'ben', 'sen', 'biz',
    'siz', 'onlar', 'var', 'yok', 'oldu', 'olur', 'olacak',
    'edilir', 'edildi', 'edilmiş', 'yapılır', 'yapıldı',
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
    'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
    'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
    'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how',
    'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
    'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
    'very', 'just', 'any', 'if', 'because', 'about', 'into', 'through',
    'during', 'before', 'after', 'above', 'below', 'up', 'down', 'out'
}
DEPRECATED_TAGS = {
    'font': 'CSS should be used for styling',
    'center': 'CSS text-align or flexbox should be used for centering',
    'marquee': 'Not supported in modern web standards',
    'frameset': 'Modern layout techniques (Grid/Flex) should be used',
    'frame': 'Iframe or modern techniques should be used',
    'big': 'CSS font-size should be used',
    'strike': 'CSS text-decoration or <del>/<s> should be used',
    'tt': '<code> or CSS font-family should be used',
    'align': 'CSS should be used (as attribute)',
    'bgcolor': 'CSS background-color should be used (as attribute)'
}
MIN_WORD_COUNT_BLOG = 300
MIN_WORD_COUNT_PAGE = 150
class ContentAnalyzer:
    def __init__(self, soup: BeautifulSoup, html: str, cached_elements=None):
        self.soup = soup
        self.html = html
        self.html_bytes = html.encode('utf-8') if html else b''
        self.html_size = len(self.html_bytes)
        self._cached_elements = cached_elements
    def analyze(self) -> dict:
        text = self._extract_visible_text()
        words = self._extract_words(text)
        word_count = len(words)
        text_html_ratio = self._calculate_text_html_ratio(text)
        keyword_data = self._analyze_keywords(words)
        word_status = self._get_word_count_status(word_count)
        ratio_status = self._get_ratio_status(text_html_ratio)
        deprecated_tags = self._check_deprecated_tags()
        inline_code_analysis = self._analyze_inline_code()

        statuses = [word_status['status'], ratio_status['status']]
        if deprecated_tags.get('has_deprecated'):
            statuses.append('warning')
        error_count = statuses.count('error')
        warning_count = statuses.count('warning')
        if error_count > 0:
            summary_status = 'error'
        elif warning_count > 0:
            summary_status = 'warning'
        else:
            summary_status = 'success'

        return {
            'word_count': {
                'total': word_count,
                'status': word_status['status'],
                'message': word_status['message'],
                'min_recommended': MIN_WORD_COUNT_BLOG
            },
            'text_html_ratio': {
                'percentage': text_html_ratio,
                'status': ratio_status['status'],
                'message': ratio_status['message']
            },
            'keywords': keyword_data,
            'text_length': len(text),
            'html_length': len(self.html) if self.html else 0,
            'html_size_bytes': self.html_size,
            'deprecated_tags': deprecated_tags,
            'inline_code': inline_code_analysis,
            'summary': {
                'status': summary_status,
                'word_count': word_count,
                'text_html_ratio': round(text_html_ratio, 2),
                'errors': error_count,
                'warnings': warning_count,
                'message': f'{word_count} words, {text_html_ratio:.1f}% text ratio'
            }
        }
    def _analyze_inline_code(self) -> dict:
        if not self.html:
            return {'ratio': 0, 'status': 'success', 'message': 'No data'}
        inline_size = 0
        scripts = self._cached_elements.scripts if self._cached_elements else self.soup.find_all('script')
        for script in scripts:
            if not script.get('src') and script.string:
                inline_size += len(script.string)
        styles = self._cached_elements.styles if self._cached_elements else self.soup.find_all('style')
        for style in styles:
            if style.string:
                inline_size += len(style.string)
        inline_style_elements = self._cached_elements.all_with_style if self._cached_elements else self.soup.find_all(attrs={'style': True})
        for el in inline_style_elements:
            inline_size += len(el.get('style', ''))
        ratio = (inline_size / len(self.html)) * 100 if self.html else 0
        ratio = round(ratio, 2)
        if ratio > 40:
             return {
                'ratio': ratio,
                'total_inline_bytes': inline_size,
                'status': 'error',
                'message': f'Inline code ratio is very high ({ratio}%). External files should be used.'
            }
        elif ratio > 20:
             return {
                'ratio': ratio,
                'total_inline_bytes': inline_size,
                'status': 'warning',
                'message': f'Inline code ratio is high ({ratio}%). External files preferred for cache efficiency.'
            }
        return {
            'ratio': ratio,
            'total_inline_bytes': inline_size,
            'status': 'success',
            'message': f'Inline code ratio is at an ideal level ({ratio}%)'
        }

    def _check_deprecated_tags(self) -> dict:
        found_tags = {}
        tag_names = {k for k in DEPRECATED_TAGS if k not in ('align', 'bgcolor')}
        attr_names = {'align', 'bgcolor'}
        for el in self.soup.find_all(list(tag_names)):
            tag = el.name
            if tag not in found_tags:
                found_tags[tag] = {'tag': tag, 'count': 0, 'reason': DEPRECATED_TAGS[tag]}
            found_tags[tag]['count'] += 1
        for attr in attr_names:
            elements = self.soup.find_all(attrs={attr: True})
            if elements:
                key = f'attribute: {attr}'
                found_tags[key] = {'tag': key, 'count': len(elements), 'reason': DEPRECATED_TAGS[attr]}
        tag_list = list(found_tags.values())
        if tag_list:
            return {
                'has_deprecated': True,
                'tag_list': tag_list,
                'count': sum(t['count'] for t in tag_list),
                'status': 'warning',
                'message': f'{len(tag_list)} different types of deprecated/forbidden tags detected'
            }
        return {
            'has_deprecated': False,
            'tag_list': [],
            'count': 0,
            'status': 'success',
            'message': 'Modern HTML structure (No forbidden tags found)'
        }

    def _extract_visible_text(self) -> str:
        skip_tags = {'script', 'style', 'head', 'meta', 'link', 'noscript', 'iframe', 'svg', 'path'}
        body = self.soup.find('body')
        if not body:
            return ''
        texts = []
        for element in body.descendants:
            if isinstance(element, NavigableString):
                parent = element.parent
                if parent and parent.name not in skip_tags:
                    stripped = element.strip()
                    if stripped:
                        texts.append(stripped)
        return re.sub(r'\s+', ' ', ' '.join(texts)).strip()
    def _extract_words(self, text: str) -> list:
        words = re.findall(r'\b[a-zA-ZğüşıöçĞÜŞİÖÇ]+\b', text.lower())
        words = [w for w in words if len(w) > 2]
        return words
    def _calculate_text_html_ratio(self, text: str) -> float:
        if not self.html:
            return 0.0
        text_len = len(text)
        html_len = len(self.html)
        if html_len == 0:
            return 0.0
        ratio = (text_len / html_len) * 100
        return round(ratio, 2)
    def _analyze_keywords(self, words: list) -> dict:
        if not words:
            return {
                'top_keywords': [],
                'total_unique': 0,
                'status': 'warning',
                'message': 'Very little or no content found'
            }
        filtered_words = [w for w in words if w not in TURKISH_STOP_WORDS]
        word_counts = Counter(filtered_words)
        top_keywords = []
        for word, count in word_counts.most_common(10):
            density = round((count / len(words)) * 100, 2)
            top_keywords.append({
                'word': word,
                'count': count,
                'density': density
            })
        has_stuffing = any(kw['density'] > 5 for kw in top_keywords)
        return {
            'top_keywords': top_keywords,
            'total_unique': len(word_counts),
            'total_filtered': len(filtered_words),
            'status': 'warning' if has_stuffing else 'success',
            'message': 'High keyword density (stuffing risk)' if has_stuffing else 'Normal keyword distribution'
        }
    def _get_word_count_status(self, count: int) -> dict:
        if count < 100:
            return {
                'status': 'error',
                'message': f'Very little content ({count} words). Minimum 300 words recommended.'
            }
        elif count < MIN_WORD_COUNT_PAGE:
            return {
                'status': 'warning',
                'message': f'Insufficient content ({count} words). Minimum 300 words recommended.'
            }
        elif count < MIN_WORD_COUNT_BLOG:
            return {
                'status': 'warning',
                'message': f'Content is short ({count} words). 300+ words recommended for blog posts.'
            }
        else:
            return {
                'status': 'success',
                'message': f'Sufficient content ({count} words)'
            }
    def _get_ratio_status(self, ratio: float) -> dict:
        if ratio < 10:
            return {
                'status': 'error',
                'message': f'Very low ratio ({ratio}%). Page is code-heavy, content is insufficient.'
            }
        elif ratio < 20:
            return {
                'status': 'warning',
                'message': f'Low ratio ({ratio}%). More text content is recommended.'
            }
        elif ratio < 70:
            return {
                'status': 'success',
                'message': f'Good ratio ({ratio}%). Content and code are balanced.'
            }
        else:
            return {
                'status': 'success',
                'message': f'High text ratio ({ratio}%). Content-focused page.'
            }