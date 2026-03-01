from bs4 import BeautifulSoup
from config import META_TITLE_MIN, META_TITLE_MAX, META_DESCRIPTION_MIN, META_DESCRIPTION_MAX
class MetaAnalyzer:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
    def analyze(self) -> dict:
        title = self._analyze_title()
        description = self._analyze_description()
        charset = self._analyze_charset()
        viewport = self._analyze_viewport()
        canonical = self._analyze_canonical()
        robots_meta = self._analyze_robots_meta()
        og_tags = self._analyze_og_tags()
        twitter_tags = self._analyze_twitter_tags()
        other_meta = self._analyze_other_meta()
        statuses = [
            title.get('status'), description.get('status'),
            charset.get('status'), viewport.get('status')
        ]
        error_count = statuses.count('error')
        warning_count = statuses.count('warning')

        if error_count > 0:
            status = 'error'
        elif warning_count > 0:
            status = 'warning'
        else:
            status = 'success'

        return {
            'title': title,
            'description': description,
            'charset': charset,
            'viewport': viewport,
            'canonical': canonical,
            'robots_meta': robots_meta,
            'og_tags': og_tags,
            'twitter_tags': twitter_tags,
            'other_meta': other_meta,
            'summary': {
                'status': status,
                'errors': error_count,
                'warnings': warning_count,
                'message': f'{error_count} errors, {warning_count} warnings'
            }
        }
    def _analyze_title(self) -> dict:
        title_tag = self.soup.find('title')
        if not title_tag or not title_tag.string:
            return {
                'exists': False,
                'content': None,
                'length': 0,
                'status': 'error',
                'message': 'Title tag not found or empty',
                'min_length': META_TITLE_MIN,
                'max_length': META_TITLE_MAX
            }
        title_text = title_tag.string.strip()
        length = len(title_text)
        if length < META_TITLE_MIN:
            status = 'warning'
            message = f'Title is too short ({length} chars). Minimum {META_TITLE_MIN} chars recommended.'
        elif length > META_TITLE_MAX:
            status = 'warning'
            message = f'Title is too long ({length} chars). Maximum {META_TITLE_MAX} chars recommended.'
        else:
            status = 'success'
            message = f'Title has optimal length ({length} chars)'
        return {
            'exists': True,
            'content': title_text,
            'length': length,
            'status': status,
            'message': message,
            'min_length': META_TITLE_MIN,
            'max_length': META_TITLE_MAX
        }
    def _analyze_description(self) -> dict:
        desc_tag = self.soup.find('meta', attrs={'name': 'description'})
        if not desc_tag or not desc_tag.get('content'):
            return {
                'exists': False,
                'content': None,
                'length': 0,
                'status': 'error',
                'message': 'Meta description not found or empty',
                'min_length': META_DESCRIPTION_MIN,
                'max_length': META_DESCRIPTION_MAX
            }
        desc_text = desc_tag.get('content', '').strip()
        length = len(desc_text)
        if length < META_DESCRIPTION_MIN:
            status = 'warning'
            message = f'Description is too short ({length} chars). Minimum {META_DESCRIPTION_MIN} chars recommended.'
        elif length > META_DESCRIPTION_MAX:
            status = 'warning'
            message = f'Description is too long ({length} chars). Maximum {META_DESCRIPTION_MAX} chars recommended.'
        else:
            status = 'success'
            message = f'Description has optimal length ({length} chars)'
        return {
            'exists': True,
            'content': desc_text,
            'length': length,
            'status': status,
            'message': message,
            'min_length': META_DESCRIPTION_MIN,
            'max_length': META_DESCRIPTION_MAX
        }
    def _analyze_charset(self) -> dict:
        charset_tag = self.soup.find('meta', attrs={'charset': True})
        if charset_tag:
            charset = charset_tag.get('charset', '').upper()
            return {
                'exists': True,
                'value': charset,
                'status': 'success' if charset == 'UTF-8' else 'warning',
                'message': 'UTF-8 charset is defined' if charset == 'UTF-8' else f'{charset} is defined, UTF-8 recommended'
            }
        content_type_tag = self.soup.find('meta', attrs={'http-equiv': 'Content-Type'})
        if content_type_tag:
            content = content_type_tag.get('content', '')
            if 'utf-8' in content.lower():
                return {
                    'exists': True,
                    'value': 'UTF-8',
                    'status': 'success',
                    'message': 'UTF-8 charset is defined (via http-equiv)'
                }
            return {
                'exists': True,
                'value': content,
                'status': 'warning',
                'message': f'Charset: {content}. UTF-8 recommended.'
            }
        return {
            'exists': False,
            'value': None,
            'status': 'error',
            'message': 'Charset definition not found. UTF-8 should be added.'
        }
    def _analyze_viewport(self) -> dict:
        viewport_tag = self.soup.find('meta', attrs={'name': 'viewport'})
        if not viewport_tag:
            return {
                'exists': False,
                'content': None,
                'status': 'error',
                'message': 'Viewport tag not found. Required for mobile compatibility.'
            }
        content = viewport_tag.get('content', '')
        has_width = 'width=' in content
        has_initial_scale = 'initial-scale=' in content
        if has_width and has_initial_scale:
            return {
                'exists': True,
                'content': content,
                'status': 'success',
                'message': 'Viewport is defined correctly'
            }
        return {
            'exists': True,
            'content': content,
            'status': 'warning',
            'message': 'Viewport has missing properties. width=device-width, initial-scale=1.0 recommended.'
        }
    def _analyze_canonical(self) -> dict:
        canonical_tag = self.soup.find('link', attrs={'rel': 'canonical'})
        if not canonical_tag:
            return {
                'exists': False,
                'url': None,
                'status': 'warning',
                'message': 'Canonical URL not defined. Recommended to prevent duplicate content issues.'
            }
        href = canonical_tag.get('href', '').strip()
        if not href:
            return {
                'exists': False,
                'url': None,
                'status': 'error',
                'message': 'Canonical tag exists but href value is empty'
            }
        return {
            'exists': True,
            'url': href,
            'status': 'success',
            'message': 'Canonical URL is defined'
        }
    def _analyze_robots_meta(self) -> dict:
        robots_tag = self.soup.find('meta', attrs={'name': 'robots'})
        if not robots_tag:
            return {
                'exists': False,
                'content': None,
                'status': 'info',
                'message': 'Robots meta tag not defined (default: index, follow)'
            }
        content = robots_tag.get('content', '').lower()
        issues = []
        if 'noindex' in content:
            issues.append('noindex: Page will not be indexed by search engines')
        if 'nofollow' in content:
            issues.append('nofollow: Links will not be followed')
        return {
            'exists': True,
            'content': content,
            'status': 'warning' if issues else 'success',
            'message': '; '.join(issues) if issues else 'Robots meta normal (index, follow)',
            'directives': content.split(',') if content else []
        }
    def _analyze_meta_group(self, prefix: str, attr_key: str, essential_tags: list) -> dict:
        found_tags = {}
        elements = self.soup.find_all('meta', attrs={attr_key: lambda x: x and x.startswith(prefix)})
        for tag in elements:
            property_name = tag.get(attr_key, '').replace(prefix, '')
            found_tags[property_name] = tag.get('content', '')
        missing_tags = [tag for tag in essential_tags if tag not in found_tags]
        group_name = 'Open Graph' if 'og' in prefix else 'Twitter Card'
        status = 'success'
        message = f'All essential {group_name} tags are present'
        if missing_tags:
            if found_tags:
                status = 'warning'
                message = f'Missing {group_name} tags: {", ".join(missing_tags)}'
            else:
                status = 'info'
                message = f'No {group_name} tags found'
        return {
            'exists': bool(found_tags),
            'tags': found_tags,
            'missing': missing_tags,
            'status': status,
            'message': message
        }
    def _analyze_og_tags(self) -> dict:
        return self._analyze_meta_group(
            prefix='og:',
            attr_key='property',
            essential_tags=['title', 'description', 'image', 'url', 'type', 'site_name']
        )
    def _analyze_twitter_tags(self) -> dict:
        return self._analyze_meta_group(
            prefix='twitter:',
            attr_key='name',
            essential_tags=['card', 'site', 'title', 'description', 'image', 'url']
        )
    def _analyze_other_meta(self) -> dict:
        other_meta = {}
        author_tag = self.soup.find('meta', attrs={'name': 'author'})
        if author_tag:
            other_meta['author'] = author_tag.get('content', '')
        publisher_tag = self.soup.find('meta', attrs={'name': 'publisher'})
        if publisher_tag:
            other_meta['publisher'] = publisher_tag.get('content', '')
        keywords_tag = self.soup.find('meta', attrs={'name': 'keywords'})
        if keywords_tag:
            other_meta['keywords'] = keywords_tag.get('content', '')
        theme_color_tag = self.soup.find('meta', attrs={'name': 'theme-color'})
        if theme_color_tag:
            other_meta['theme_color'] = theme_color_tag.get('content', '')
        generator_tag = self.soup.find('meta', attrs={'name': 'generator'})
        if generator_tag:
            other_meta['generator'] = generator_tag.get('content', '')
        return {
            'tags': other_meta,
            'count': len(other_meta)
        }