from bs4 import BeautifulSoup
from collections import OrderedDict
class StructureAnalyzer:
    def __init__(self, soup: BeautifulSoup):
        self.soup = soup
    def analyze(self) -> dict:
        headings = self._extract_headings()
        tree = self._build_heading_tree(headings)
        issues = self._check_hierarchy_issues(headings)
        counts = self._count_headings(headings)
        return {
            'headings': headings,
            'tree': tree,
            'issues': issues,
            'counts': counts,
            'h1_status': self._analyze_h1(counts),
            'summary': self._generate_summary(counts, issues)
        }
    def _extract_headings(self) -> list:
        headings = []
        heading_tags = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for idx, tag in enumerate(heading_tags):
            text = tag.get_text(strip=True)
            level = int(tag.name[1])
            headings.append({
                'index': idx,
                'level': level,
                'tag': tag.name,
                'text': text,
                'length': len(text),
                'has_id': bool(tag.get('id')),
                'id': tag.get('id', None)
            })
        return headings
    def _build_heading_tree(self, headings: list) -> list:
        if not headings:
            return []
        tree = []
        stack = [(0, tree)]
        for heading in headings:
            node = {
                'level': heading['level'],
                'tag': heading['tag'],
                'text': heading['text'],
                'children': []
            }
            while stack and stack[-1][0] >= heading['level']:
                stack.pop()
            if stack:
                stack[-1][1].append(node)
            else:
                tree.append(node)
            stack.append((heading['level'], node['children']))
        return tree
    def _check_hierarchy_issues(self, headings: list) -> list:
        issues = []
        if not headings:
            issues.append({
                'type': 'error',
                'message': 'No headings (H1-H6) found on the page'
            })
            return issues
        if headings[0]['level'] != 1:
            issues.append({
                'type': 'warning',
                'message': f'Page does not start with H1, first heading: H{headings[0]["level"]}'
            })
        for i in range(1, len(headings)):
            prev_level = headings[i - 1]['level']
            curr_level = headings[i]['level']
            if curr_level > prev_level + 1:
                issues.append({
                    'type': 'warning',
                    'message': f'Hierarchy skipped: H{prev_level} → H{curr_level} ("{headings[i]["text"][:50]}...")',
                    'from': f'H{prev_level}',
                    'to': f'H{curr_level}',
                    'heading_text': headings[i]['text']
                })
        for heading in headings:
            if not heading['text']:
                issues.append({
                    'type': 'error',
                    'message': f'Empty {heading["tag"].upper()} heading detected'
                })
        return issues
    def _count_headings(self, headings: list) -> dict:
        counts = {f'h{i}': 0 for i in range(1, 7)}
        for heading in headings:
            counts[heading['tag']] += 1
        counts['total'] = len(headings)
        return counts
    def _analyze_h1(self, counts: dict) -> dict:
        h1_count = counts.get('h1', 0)
        if h1_count == 0:
            return {
                'count': 0,
                'status': 'error',
                'message': 'H1 heading not found. There should be one H1 on every page.'
            }
        elif h1_count == 1:
            return {
                'count': 1,
                'status': 'success',
                'message': 'H1 heading is defined correctly (1 count)'
            }
        else:
            return {
                'count': h1_count,
                'status': 'warning',
                'message': f'Multiple H1 headings detected ({h1_count} count). There should be only 1.'
            }
    def _generate_summary(self, counts: dict, issues: list) -> dict:
        error_count = sum(1 for i in issues if i['type'] == 'error')
        warning_count = sum(1 for i in issues if i['type'] == 'warning')
        if error_count > 0:
            status = 'error'
        elif warning_count > 0:
            status = 'warning'
        else:
            status = 'success'
        return {
            'total_headings': counts['total'],
            'error_count': error_count,
            'warning_count': warning_count,
            'status': status,
            'message': f'{counts["total"]} headings found. {error_count} errors, {warning_count} warnings.'
        }