from urllib.parse import urlparse, parse_qs
import re
class URLAnalyzer:
    def __init__(self, url: str):
        self.url = url
        self.parsed_url = urlparse(url)
    def analyze(self) -> dict:
        parameters = self._check_parameters()
        separators = self._check_separators()
        depth = self._check_depth()
        length = self._check_length()
        structure = self._analyze_structure()
        statuses = [
            parameters.get('status'), separators.get('status'),
            depth.get('status'), length.get('status')
        ]
        success_count = statuses.count('success')
        total = len(statuses)

        if success_count == total:
            summary_status = 'success'
        elif success_count >= total // 2:
            summary_status = 'warning'
        else:
            summary_status = 'error'

        return {
            'parameters': parameters,
            'separators': separators,
            'depth': depth,
            'length': length,
            'structure': structure,
            'summary': {
                'status': summary_status,
                'checks_passed': success_count,
                'checks_total': total,
                'message': f'{success_count}/{total} checks successful'
            }
        }
    def _check_parameters(self) -> dict:
        query_params = parse_qs(self.parsed_url.query)
        if query_params:
            return {
                'is_clean': False,
                'status': 'warning',
                'message': 'URL contains parameters (?id=, ?ref= etc.). Not SEO friendly (Clean URL).',
                'params': list(query_params.keys())
            }
        return {
            'is_clean': True,
            'status': 'success',
            'message': 'Clean URL structure (No parameters)'
        }
    def _check_separators(self) -> dict:
        path = self.parsed_url.path
        has_hyphen = '-' in path
        has_underscore = '_' in path
        if has_underscore:
            return {
                'status': 'warning',
                'message': 'Underscore (_) used in URL. Google prefers hyphens (-).',
                'found': '_'
            }
        if has_uppercase := any(c.isupper() for c in path):
             return {
                'status': 'warning',
                'message': 'Uppercase letters used in URL. Lowercase is preferred.',
                'found': 'Uppercase'
            }
        return {
            'status': 'success',
            'message': 'URL character usage is appropriate (Hyphen or plain text)'
        }
    def _check_depth(self) -> dict:
        path_segments = [s for s in self.parsed_url.path.split('/') if s]
        depth = len(path_segments)
        if depth > 4:
            return {
                'level': depth,
                'status': 'warning',
                'message': f'URL structure is too deep ({depth} levels). Ex: /blog/year/month/category/title',
                'segments': path_segments
            }
        return {
            'level': depth,
            'status': 'success',
            'message': f'URL depth is appropriate ({depth} levels)'
        }
    def _check_length(self) -> dict:
        relative_path = self.parsed_url.path
        if self.parsed_url.query:
            relative_path += '?' + self.parsed_url.query
        length = len(relative_path)
        if length > 75:
             return {
                'length': length,
                'status': 'warning',
                'message': f'URL path is too long ({length} chars). Short and descriptive is recommended.'
            }
        return {
            'length': length,
            'status': 'success',
            'message': 'URL length is appropriate'
        }
    def _analyze_structure(self) -> dict:
        return {
            'scheme': self.parsed_url.scheme,
            'netloc': self.parsed_url.netloc,
            'path': self.parsed_url.path,
            'is_secure': self.parsed_url.scheme == 'https'
        }