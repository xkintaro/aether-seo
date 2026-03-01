from analyzers import (
    DocumentParser,
    MetaAnalyzer,
    StructureAnalyzer,
    MediaAnalyzer,
    NetworkAnalyzer,
    SitemapRobotAnalyzer,
    SSLAnalyzer,
    HreflangAnalyzer,
    ContentAnalyzer,
    URLAnalyzer,
    AccessibilityAnalyzer
)
from analyzers.element_cache import ElementCache
from analyzers.utils import create_session, clean_text, get_tokens
from config import ECO_MODE, ECO_DELAY, META_TITLE_MIN, META_TITLE_MAX, META_DESCRIPTION_MIN, META_DESCRIPTION_MAX, PARALLEL_ANALYZER_WORKERS
import time
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed

class SEOAnalyzer:
    def __init__(self, url: str):
        self.url = url
        self.results = {}
        self.errors = []
        self.session = create_session()

    def analyze(self, progress_callback=None) -> dict:
        def emit(msg):
            if progress_callback:
                progress_callback(msg)
                if ECO_MODE:
                    time.sleep(ECO_DELAY)

        emit("Establishing connection and analyzing DOM structure...")
        parser = DocumentParser(self.url, session=self.session)
        doc_result = parser.fetch()
        self.results['document'] = {
            'url': doc_result['url'],
            'base_url': doc_result['base_url'],
            'domain': doc_result['domain'],
            'status_code': doc_result['status_code'],
            'response_time': doc_result['response_time'],
            'success': doc_result['success'],
            'error': doc_result['error']
        }
        if not doc_result['success']:
            self.errors.append(doc_result['error'])
            return self._build_response(success=False)

        soup = doc_result['soup']
        base_url = doc_result['base_url']
        domain = doc_result['domain']

        if ECO_MODE:
            self._run_sequential(emit, soup, base_url, domain, doc_result)
        else:
            self._run_parallel(emit, soup, base_url, domain, doc_result)

        emit("Compiling all data and calculating score...")
        self.results['relevance'] = self._check_relevance()
        self.results['score'] = self._calculate_score()
        self.results['critical_issues'] = self._get_critical_issues()
        emit("Analysis complete! Generating report...")
        return self._build_response(success=True)

    def _run_analyzer(self, name, analyzer_fn):
        try:
            return name, analyzer_fn(), None
        except Exception as e:
            return name, {'error': str(e)}, f'{name} analysis error: {str(e)}'

    def _run_sequential(self, emit, soup, base_url, domain, doc_result):
        cached_elements = ElementCache(soup)
        analyzers = [
            ("Scanning meta tags and SEO signatures...", 'meta', lambda: MetaAnalyzer(soup).analyze()),
            ("Examining hierarchical structure and headings...", 'structure', lambda: StructureAnalyzer(soup).analyze()),
            ("Performing image and media analysis (This may take some time)...", 'media', lambda: MediaAnalyzer(soup, base_url, session=create_session(), cached_elements=cached_elements).analyze()),
            ("Checking network topology and link health...", 'network', lambda: NetworkAnalyzer(soup, base_url, domain, session=create_session(), cached_elements=cached_elements).analyze()),
            ("Verifying SSL certificate and security protocols...", 'ssl', lambda: SSLAnalyzer(doc_result['url']).analyze()),
            ("Scanning bot directives and sitemap...", 'sitemap_robots', lambda: SitemapRobotAnalyzer(base_url, session=create_session()).analyze()),
            ("Checking international targeting (Hreflang)...", 'hreflang', lambda: HreflangAnalyzer(soup, base_url, session=create_session()).analyze()),
            ("Analyzing content quality and keywords...", 'content', lambda: ContentAnalyzer(soup, doc_result['html'], cached_elements=cached_elements).analyze()),
            ("Checking accessibility (A11y) standards...", 'accessibility', lambda: AccessibilityAnalyzer(soup, base_url, cached_elements=cached_elements.as_dict()).analyze()),
            ("Examining URL structure and semantic integrity...", 'url', lambda: URLAnalyzer(self.url).analyze()),
        ]
        for msg, name, fn in analyzers:
            emit(msg)
            _, result, error = self._run_analyzer(name, fn)
            self.results[name] = result
            if error:
                self.errors.append(error)

    def _run_parallel(self, emit, soup, base_url, domain, doc_result):
        emit("Starting all analyses in parallel...")
        cached_elements = ElementCache(soup)

        independent_analyzers = {
            'ssl': lambda: SSLAnalyzer(doc_result['url']).analyze(),
            'sitemap_robots': lambda: SitemapRobotAnalyzer(base_url, session=create_session()).analyze(),
            'url': lambda: URLAnalyzer(self.url).analyze(),
        }

        soup_analyzers = {
            'meta': lambda: MetaAnalyzer(soup).analyze(),
            'structure': lambda: StructureAnalyzer(soup).analyze(),
            'media': lambda: MediaAnalyzer(soup, base_url, session=create_session(), cached_elements=cached_elements).analyze(),
            'network': lambda: NetworkAnalyzer(soup, base_url, domain, session=create_session(), cached_elements=cached_elements).analyze(),
            'hreflang': lambda: HreflangAnalyzer(soup, base_url, session=create_session()).analyze(),
            'content': lambda: ContentAnalyzer(soup, doc_result['html'], cached_elements=cached_elements).analyze(),
            'accessibility': lambda: AccessibilityAnalyzer(soup, base_url, cached_elements=cached_elements.as_dict()).analyze(),
        }

        all_analyzers = {**independent_analyzers, **soup_analyzers}

        with ThreadPoolExecutor(max_workers=PARALLEL_ANALYZER_WORKERS) as executor:
            futures = {
                executor.submit(self._run_analyzer, name, fn): name
                for name, fn in all_analyzers.items()
            }

            status_messages = {
                'meta': "Meta tags and SEO signatures scanned",
                'structure': "Hierarchical structure examined",
                'media': "Image and media analysis completed",
                'network': "Network topology checked",
                'ssl': "SSL certificate verified",
                'sitemap_robots': "Bot directives and sitemap scanned",
                'hreflang': "Hreflang checked",
                'content': "Content quality analyzed",
                'accessibility': "Accessibility checked",
                'url': "URL structure examined",
            }

            for future in as_completed(futures):
                name, result, error = future.result()
                self.results[name] = result
                if error:
                    self.errors.append(error)
                emit(f"✓ {status_messages.get(name, name)}")
    def _calculate_score(self) -> dict:
        breakdown = {}
        breakdown['on_page'] = self._score_on_page()
        breakdown['technical'] = self._score_technical()
        breakdown['performance'] = self._score_performance()
        breakdown['accessibility'] = self._score_accessibility()

        total_score = 0
        total_score += breakdown['on_page']['score'] * 0.35
        total_score += breakdown['technical']['score'] * 0.25
        total_score += breakdown['performance']['score'] * 0.20
        total_score += breakdown['accessibility']['score'] * 0.20

        if total_score >= 90:
            grade, grade_color = 'A', 'success'
        elif total_score >= 80:
            grade, grade_color = 'B', 'success'
        elif total_score >= 70:
            grade, grade_color = 'C', 'warning'
        elif total_score >= 60:
            grade, grade_color = 'D', 'warning'
        else:
            grade, grade_color = 'F', 'error'

        return {
            'total': int(total_score),
            'max': 100,
            'percentage': int(total_score),
            'grade': grade,
            'grade_color': grade_color,
            'breakdown': breakdown,
            'max_breakdown': {'on_page': 35, 'technical': 25, 'performance': 20, 'accessibility': 20}
        }

    def _score_on_page(self) -> dict:
        on_page_score = 0
        on_page_details = []
        meta = self.results.get('meta', {})
        content = self.results.get('content', {})
        relevance = self.results.get('relevance', {})

        title_data = meta.get('title', {})
        title_status = title_data.get('status')
        if title_status == 'success':
            on_page_score += 25
            on_page_details.append({'label': 'Title', 'value': 'Optimal', 'impact': '+25 Pts', 'status': 'success'})
        elif title_data.get('exists'):
            length = title_data.get('length', 0)
            if length < META_TITLE_MIN:
                closeness = max(0, length / META_TITLE_MIN)
            else:
                closeness = max(0, 1 - (length - META_TITLE_MAX) / META_TITLE_MAX)
            partial = int(10 + closeness * 14)
            on_page_score += partial
            on_page_details.append({'label': 'Title Length', 'value': f'{length} chars', 'impact': f'+{partial} Pts', 'status': 'warning'})
        else:
            on_page_details.append({'label': 'Title', 'value': 'Missing', 'impact': '-25 Loss', 'status': 'error'})

        desc_data = meta.get('description', {})
        desc_status = desc_data.get('status')
        if desc_status == 'success':
            on_page_score += 25
            on_page_details.append({'label': 'Description', 'value': 'Optimal', 'impact': '+25 Pts', 'status': 'success'})
        elif desc_data.get('exists'):
            length = desc_data.get('length', 0)
            if length < META_DESCRIPTION_MIN:
                closeness = max(0, length / META_DESCRIPTION_MIN)
            else:
                closeness = max(0, 1 - (length - META_DESCRIPTION_MAX) / META_DESCRIPTION_MAX)
            partial = int(10 + closeness * 14)
            on_page_score += partial
            on_page_details.append({'label': 'Description Length', 'value': f'{length} chars', 'impact': f'+{partial} Pts', 'status': 'warning'})
        else:
            on_page_details.append({'label': 'Description', 'value': 'Missing', 'impact': '-25 Loss', 'status': 'error'})

        rel_score = relevance.get('score', 0)
        rel_points = int(rel_score * 20 / 100)
        on_page_score += rel_points
        if rel_score > 60:
            on_page_details.append({'label': 'Title-H1 Match', 'value': f'{rel_score}%', 'impact': f'+{rel_points} Pts', 'status': 'success'})
        elif rel_score > 30:
            on_page_details.append({'label': 'Title-H1 Match', 'value': f'{rel_score}%', 'impact': f'+{rel_points} Pts', 'status': 'warning'})
        else:
            on_page_details.append({'label': 'Title-H1 Match', 'value': f'{rel_score}%', 'impact': f'+{rel_points} Pts', 'status': 'error'})

        if meta.get('canonical', {}).get('exists'):
            on_page_score += 10
            on_page_details.append({'label': 'Canonical URL', 'value': 'Exists', 'impact': '+10 Pts', 'status': 'success'})
        else:
            on_page_details.append({'label': 'Canonical URL', 'value': 'Missing', 'impact': '-10 Loss', 'status': 'warning'})

        if meta.get('viewport', {}).get('status') == 'success':
            on_page_score += 10
            on_page_details.append({'label': 'Mobile Friendly', 'value': 'OK', 'impact': '+10 Pts', 'status': 'success'})
        else:
            on_page_details.append({'label': 'Mobile Friendly', 'value': 'Error', 'impact': '-10 Loss', 'status': 'error'})

        if meta.get('charset', {}).get('status') == 'success':
            on_page_score += 10
            on_page_details.append({'label': 'Charset', 'value': 'UTF-8', 'impact': '+10 Pts', 'status': 'success'})
        else:
            on_page_details.append({'label': 'Charset', 'value': 'Error', 'impact': '-10 Loss', 'status': 'error'})

        deprecated = content.get('deprecated_tags', {})
        if deprecated.get('has_deprecated'):
            dep_count = deprecated.get('count', 0)
            if dep_count <= 3:
                penalty = 5
            elif dep_count <= 7:
                penalty = 10
            else:
                penalty = 15
            on_page_score = max(0, on_page_score - penalty)
            on_page_details.append({'label': 'Deprecated Tags', 'value': f"{dep_count} count", 'impact': f"-{penalty} Pts", 'status': 'error'})

        word_count = content.get('word_count', {}).get('total', 0)
        text_ratio = content.get('text_html_ratio', {}).get('percentage', 0)
        content_bonus = 0
        if word_count >= 1000:
            content_bonus += 5
            on_page_details.append({'label': 'Rich Content', 'value': f'{word_count} words', 'impact': '+5 Bonus', 'status': 'success'})
        elif word_count >= 300:
            content_bonus += 3
            on_page_details.append({'label': 'Adequate Content', 'value': f'{word_count} words', 'impact': '+3 Bonus', 'status': 'success'})
        if text_ratio > 10:
            content_bonus += 2
        on_page_score = min(100, on_page_score + content_bonus)

        return {
            'score': int(on_page_score),
            'weight': 35,
            'details': on_page_details
        }

    def _score_technical(self) -> dict:
        tech_score = 0
        tech_details = []
        ssl = self.results.get('ssl', {})
        sr = self.results.get('sitemap_robots', {})
        network = self.results.get('network', {})
        url_struct = self.results.get('url', {})

        ssl_status = ssl.get('status')
        if ssl_status == 'success':
            tech_score += 25
            tech_details.append({'label': 'SSL Certificate', 'value': 'Valid', 'impact': '+25 Pts', 'status': 'success'})
        elif ssl_status == 'warning':
            days = ssl.get('days_remaining', 0)
            partial = 15 if days and days > 7 else 8
            tech_score += partial
            tech_details.append({'label': 'SSL Certificate', 'value': f'{days} days left', 'impact': f'+{partial} Pts', 'status': 'warning'})
        else:
            tech_details.append({'label': 'SSL Certificate', 'value': 'Invalid', 'impact': '-25 Loss', 'status': 'error'})

        total_links = network.get('links', {}).get('total', 1)
        broken = network.get('links', {}).get('total_broken', 0)
        if broken == 0:
            tech_score += 25
            tech_details.append({'label': 'Broken Links', 'value': 'None', 'impact': '+25 Pts', 'status': 'success'})
        else:
            broken_ratio = min(1.0, broken / max(total_links, 1))
            link_points = max(0, int(25 * (1 - broken_ratio * 2)))
            tech_score += link_points
            status = 'error' if broken_ratio > 0.1 else 'warning'
            tech_details.append({'label': 'Broken Links', 'value': f"{broken}/{total_links}", 'impact': f'+{link_points} Pts', 'status': status})

        url_checks = 0
        if url_struct.get('parameters', {}).get('is_clean'): url_checks += 1
        if url_struct.get('depth', {}).get('status') == 'success': url_checks += 1
        if url_struct.get('separators', {}).get('status') == 'success': url_checks += 1
        if url_struct.get('length', {}).get('status') == 'success': url_checks += 1
        url_points = url_checks * 5
        tech_score += url_points
        if url_points == 20:
            tech_details.append({'label': 'URL Structure', 'value': 'Ideal', 'impact': f'+{url_points} Pts', 'status': 'success'})
        elif url_points >= 10:
            tech_details.append({'label': 'URL Structure', 'value': f'{url_checks}/4 checks', 'impact': f'+{url_points} Pts', 'status': 'warning'})
        else:
            tech_details.append({'label': 'URL Structure', 'value': f'{url_checks}/4 checks', 'impact': f'+{url_points} Pts', 'status': 'error'})

        rs_points = 0
        if sr.get('robots', {}).get('exists'): rs_points += 7.5
        if sr.get('sitemap', {}).get('status') != 'error': rs_points += 7.5
        tech_score += int(rs_points)
        if rs_points == 15:
            tech_details.append({'label': 'Robots & Sitemap', 'value': 'Exists', 'impact': '+15 Pts', 'status': 'success'})
        elif rs_points > 0:
            tech_details.append({'label': 'Robots & Sitemap', 'value': 'Partial', 'impact': f"+{int(rs_points)} Pts", 'status': 'warning'})
        else:
            tech_details.append({'label': 'Robots & Sitemap', 'value': 'Missing', 'impact': '-15 Loss', 'status': 'error'})

        if not network.get('mixed_content', {}).get('has_mixed', False):
            tech_score += 15
            tech_details.append({'label': 'Mixed Content', 'value': 'Clean', 'impact': '+15 Pts', 'status': 'success'})
        else:
            tech_details.append({'label': 'Mixed Content', 'value': 'Risky', 'impact': '-15 Loss', 'status': 'error'})

        return {
            'score': min(100, int(tech_score)),
            'weight': 25,
            'details': tech_details
        }

    def _score_performance(self) -> dict:
        perf_score = 0
        perf_details = []
        media = self.results.get('media', {})
        content = self.results.get('content', {})
        network = self.results.get('network', {})
        doc = self.results.get('document', {})

        resp_time = doc.get('response_time', 1.0)
        if resp_time < 0.3:
            resp_points = 40
            resp_status = 'success'
        elif resp_time < 0.5:
            resp_points = 35
            resp_status = 'success'
        elif resp_time < 1.0:
            resp_points = 25
            resp_status = 'warning'
        elif resp_time < 2.0:
            resp_points = 10
            resp_status = 'warning'
        else:
            resp_points = 0
            resp_status = 'error'
        perf_score += resp_points
        perf_details.append({'label': 'Response Time', 'value': f"{resp_time:.2f}s", 'impact': f'+{resp_points} Pts', 'status': resp_status})

        network_assets = network.get('assets', {})
        css_size = network_assets.get('css', {}).get('total_size_bytes', 0) or 0
        js_size = network_assets.get('js', {}).get('total_size_bytes', 0) or 0
        html_size = content.get('html_size_bytes', 0) or 0
        media_size = media.get('summary', {}).get('total_size_bytes', 0) or 0
        total_size = css_size + js_size + html_size + media_size

        if total_size < 500_000:
            size_points = 30
            size_status = 'success'
        elif total_size < 1_500_000:
            size_points = 20
            size_status = 'success'
        elif total_size < 3_000_000:
            size_points = 10
            size_status = 'warning'
        else:
            size_points = 0
            size_status = 'error'
        perf_score += size_points
        perf_details.append({'label': 'Page Size', 'value': f"{int(total_size/1024)}KB", 'impact': f'+{size_points} Pts', 'status': size_status})

        img_data = media.get('images', {})
        img_total = img_data.get('total', 0)
        if img_total > 0:
            issues = img_data.get('issues', {})
            missing_alt = issues.get('missing_alt', 0)
            legacy_format = issues.get('legacy_format', 0)
            needs_lazy = issues.get('needs_lazy_load', 0)
            has_lazy = issues.get('has_lazy_load', 0)
            alt_ratio = 1 - (missing_alt / img_total)
            format_ratio = 1 - (legacy_format / img_total)
            lazy_ratio = 1 if needs_lazy == 0 else (has_lazy / max(needs_lazy, 1))
            img_quality = (alt_ratio * 0.5 + format_ratio * 0.3 + lazy_ratio * 0.2)
            img_points = int(img_quality * 30)
            if img_points >= 25:
                img_status = 'success'
            elif img_points >= 15:
                img_status = 'warning'
            else:
                img_status = 'error'
        else:
            img_points = 30
            img_status = 'success'
        perf_score += img_points
        perf_details.append({'label': 'Image Optimization', 'value': f'{img_total} images', 'impact': f'+{img_points} Pts', 'status': img_status})

        return {
            'score': min(100, int(perf_score)),
            'weight': 20,
            'details': perf_details
        }

    def _score_accessibility(self) -> dict:
        a11y = self.results.get('accessibility', {})
        a11y_raw_score = a11y.get('score', 0)
        a11y_details = []
        if a11y_raw_score >= 90:
             a11y_details.append({'label': 'Overall Accessibility', 'value': 'Excellent', 'impact': f"{int(a11y_raw_score)}/100", 'status': 'success'})
        elif a11y_raw_score >= 70:
             a11y_details.append({'label': 'Overall Accessibility', 'value': 'Good', 'impact': f"{int(a11y_raw_score)}/100", 'status': 'success'})
        elif a11y_raw_score >= 50:
             a11y_details.append({'label': 'Overall Accessibility', 'value': 'Fair', 'impact': f"{int(a11y_raw_score)}/100", 'status': 'warning'})
        else:
             a11y_details.append({'label': 'Overall Accessibility', 'value': 'Poor', 'impact': f"{int(a11y_raw_score)}/100", 'status': 'error'})
        issues_count = len(a11y.get('issues', []))
        if issues_count > 0:
            a11y_details.append({'label': 'Critical Issues', 'value': f"{issues_count} count", 'impact': 'Negative', 'status': 'error'})
        return {
            'score': int(a11y_raw_score),
            'weight': 20,
            'details': a11y_details
        }

    def _check_relevance(self) -> dict:
        meta = self.results.get('meta', {})
        structure = self.results.get('structure', {})
        title = meta.get('title', {}).get('content', '')
        h1_text = ''
        if structure.get('headings'):
            for h in structure.get('headings'):
                if h['level'] == 1:
                    h1_text = h['text']
                    break
        if not title or not h1_text:
            return {
                'score': 0,
                'status': 'error',
                'message': 'Comparison failed (Title or H1 missing)',
                'common_words': []
            }
        clean_title = clean_text(title)
        clean_h1 = clean_text(h1_text)
        title_tokens = get_tokens(clean_title)
        h1_tokens = get_tokens(clean_h1)
        if not title_tokens or not h1_tokens:
             return {
                'score': 0,
                'status': 'warning',
                'message': 'Not enough words found',
                'common_words': []
            }
        common_words = set()
        intersection = title_tokens.intersection(h1_tokens)
        common_words.update(intersection)
        def _bidirectional_fuzzy_coverage(tokens_a, tokens_b):
            a_matched = 0
            b_matched_set = set()
            for s_tok in tokens_a:
                if s_tok in tokens_b:
                    a_matched += 1
                    b_matched_set.add(s_tok)
                    continue
                for t_tok in tokens_b:
                    if len(s_tok) > 3 and len(t_tok) > 3 and (s_tok in t_tok or t_tok in s_tok):
                        a_matched += 1
                        b_matched_set.add(t_tok)
                        shortest = s_tok if len(s_tok) < len(t_tok) else t_tok
                        common_words.add(f"{shortest}*")
                        break
            b_matched = len(b_matched_set)
            for t_tok in tokens_b:
                if t_tok in b_matched_set:
                    continue
                if t_tok in tokens_a:
                    b_matched += 1
                    continue
                for s_tok in tokens_a:
                    if len(t_tok) > 3 and len(s_tok) > 3 and (t_tok in s_tok or s_tok in t_tok):
                        b_matched += 1
                        break
            return a_matched, b_matched

        title_matched, h1_matched = _bidirectional_fuzzy_coverage(title_tokens, h1_tokens)
        coverage_score = title_matched / len(title_tokens) if title_tokens else 0
        sequence_score = SequenceMatcher(None, clean_title, clean_h1).ratio()
        h1_in_title = (h1_matched / len(h1_tokens) >= 0.8) if h1_tokens else False
        title_in_h1 = (title_matched / len(title_tokens) >= 0.8) if title_tokens else False
        final_score = max(coverage_score, sequence_score) * 100
        if h1_in_title or title_in_h1:
            final_score = max(final_score, 95)
        elif coverage_score < 0.5 and sequence_score > 0.6:
            final_score = (coverage_score * 0.3 + sequence_score * 0.7) * 100 + 10
        score = int(min(100, final_score))
        status = 'success'
        if score < 30:
            status = 'error'
            message = 'Weak connection between Title and H1'
        elif score < 60:
            status = 'warning'
            message = 'Title and H1 are partially matched'
        else:
            message = 'Title and H1 are matched'
        return {
            'score': score,
            'status': status,
            'message': message,
            'common_words': sorted(list(common_words)),
            'title_snippet': title[:30] + '...' if len(title) > 30 else title,
            'h1_snippet': h1_text[:30] + '...' if len(h1_text) > 30 else h1_text
        }
    def _get_critical_issues(self) -> list:
        critical = []
        meta = self.results.get('meta', {})
        if meta.get('title', {}).get('status') == 'error':
            critical.append({
                'category': 'Meta',
                'severity': 'error',
                'message': meta.get('title', {}).get('message', 'Title tag is missing')
            })
        if meta.get('description', {}).get('status') == 'error':
            critical.append({
                'category': 'Meta',
                'severity': 'error',
                'message': meta.get('description', {}).get('message', 'Description is missing')
            })
        if meta.get('viewport', {}).get('status') == 'error':
            critical.append({
                'category': 'Meta',
                'severity': 'error',
                'message': 'Viewport tag is missing (Mobile compatibility will be affected)'
            })
        structure = self.results.get('structure', {})
        h1_status = structure.get('h1_status', {})
        if h1_status.get('status') == 'error':
            critical.append({
                'category': 'Headings',
                'severity': 'error',
                'message': h1_status.get('message', 'H1 heading is missing')
            })
        media = self.results.get('media', {})
        images = media.get('images', {})
        missing_alt = images.get('issues', {}).get('missing_alt', 0)
        if missing_alt > 0:
            critical.append({
                'category': 'Images',
                'severity': 'error',
                'message': f'{missing_alt} images missing alt tag'
            })
        empty_alt = images.get('empty_alt', 0)
        if empty_alt > 0:
            critical.append({
                'category': 'Images',
                'severity': 'warning',
                'message': f'{empty_alt} images have empty alt tags (Decorative)'
            })
        if not media.get('favicon', {}).get('exists'):
            critical.append({
                'category': 'Images',
                'severity': 'warning',
                'message': 'Favicon is not defined'
            })
        network = self.results.get('network', {})
        broken_links = network.get('links', {}).get('total_broken', 0)
        if broken_links > 0:
            critical.append({
                'category': 'Links',
                'severity': 'error',
                'message': f'{broken_links} broken links detected'
            })
        ssl = self.results.get('ssl', {})
        if ssl.get('status') == 'error':
            critical.append({
                'category': 'SSL',
                'severity': 'error',
                'message': ssl.get('message', 'SSL certificate issue')
            })
        elif ssl.get('status') == 'warning':
            critical.append({
                'category': 'SSL',
                'severity': 'warning',
                'message': ssl.get('message', 'SSL certificate will expire soon')
            })
        sr = self.results.get('sitemap_robots', {})
        if not sr.get('robots', {}).get('exists'):
            critical.append({
                'category': 'Files',
                'severity': 'warning',
                'message': 'robots.txt file not found'
            })
        if sr.get('sitemap', {}).get('status') == 'error':
            critical.append({
                'category': 'Files',
                'severity': 'warning',
                'message': 'sitemap.xml file not found'
            })
        critical.sort(key=lambda x: 0 if x['severity'] == 'error' else 1)
        return critical
    def _build_response(self, success: bool) -> dict:
        return {
            'success': success,
            'url': self.url,
            'results': self.results,
            'errors': self.errors
        }