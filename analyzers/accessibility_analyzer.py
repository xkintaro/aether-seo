from bs4 import BeautifulSoup
from collections import Counter
import re
import config
LANDMARK_ROLES = config.LANDMARK_ROLES
WIDGET_ROLES = config.WIDGET_ROLES
STRUCTURE_ROLES = config.STRUCTURE_ROLES
MUST_HAVE_ACCESSIBLE_NAME = config.MUST_HAVE_ACCESSIBLE_NAME
INTERACTIVE_ELEMENTS = config.INTERACTIVE_ELEMENTS
ARIA_ATTRIBUTES = config.ARIA_ATTRIBUTES
class AccessibilityAnalyzer:
    def __init__(self, soup: BeautifulSoup, base_url: str, cached_elements: dict = None):
        self.soup = soup
        self.base_url = base_url
        self.issues = []
        self.warnings = []
        self._cache_elements(cached_elements)
    def _cache_elements(self, cached_elements: dict = None):
        if cached_elements:
            self._images = cached_elements.get('images', self.soup.find_all('img'))
            self._links = cached_elements.get('links', self.soup.find_all('a', href=True))
            self._headings = cached_elements.get('headings', self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
            self._videos = cached_elements.get('videos', self.soup.find_all('video'))
            self._audios = cached_elements.get('audios', self.soup.find_all('audio'))
            self._iframes = cached_elements.get('iframes', self.soup.find_all('iframe'))
            self._svgs = cached_elements.get('svgs', self.soup.find_all('svg'))
            self._buttons = cached_elements.get('buttons', self.soup.find_all('button'))
            self._inputs = cached_elements.get('inputs', self.soup.find_all(['input', 'select', 'textarea']))
            self._forms = cached_elements.get('forms', self.soup.find_all('form'))
            self._tables = cached_elements.get('tables', self.soup.find_all('table'))
        else:
            self._images = self.soup.find_all('img')
            self._links = self.soup.find_all('a', href=True)
            self._headings = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            self._videos = self.soup.find_all('video')
            self._audios = self.soup.find_all('audio')
            self._iframes = self.soup.find_all('iframe')
            self._svgs = self.soup.find_all('svg')
            self._buttons = self.soup.find_all('button')
            self._inputs = self.soup.find_all(['input', 'select', 'textarea'])
            self._forms = self.soup.find_all('form')
            self._tables = self.soup.find_all('table')
    def analyze(self) -> dict:
        aria_usage = self._analyze_aria_usage()
        landmarks = self._analyze_landmarks()
        images = self._analyze_images()
        forms = self._analyze_forms()
        interactive = self._analyze_interactive_elements()
        headings = self._analyze_heading_structure()
        links = self._analyze_links()
        focus = self._analyze_focus_management()
        contrast = self._analyze_contrast_hints()
        language = self._analyze_language()
        tables = self._analyze_tables()
        media = self._analyze_media_accessibility()
        keyboard = self._analyze_keyboard_accessibility()
        live_regions = self._analyze_live_regions()
        page_structure = self._analyze_page_structure()
        semantic = self._analyze_semantic_html()
        touch_targets = self._analyze_touch_targets()
        text_alternatives = self._analyze_text_alternatives()
        timing = self._analyze_timing_controls()
        warning_count = len(self.warnings)
        error_count = len(self.issues)
        total_checks = error_count + warning_count
        score_data = self._calculate_weighted_score(
            images, forms, interactive, aria_usage, headings, links, language, keyboard
        )
        score = score_data['total_score']
        breakdown = score_data['breakdown']
        if score >= 95 and error_count == 0:
            grade = 'A+'
        elif score >= 90 and error_count == 0:
            grade = 'A'
        elif score >= 80 and error_count <= 1:
            grade = 'B+'
        elif score >= 70:
            grade = 'B'
        elif score >= 60:
            grade = 'C+'
        elif score >= 50:
            grade = 'C'
        elif score >= 40:
            grade = 'D'
        else:
            grade = 'F'
        if error_count > 5:
            status = 'error'
        elif error_count > 2 or warning_count > 5:
            status = 'warning'
        else:
            status = 'success'
        return {
            'score': score,
            'grade': grade,
            'status': status,
            'aria_usage': aria_usage,
            'landmarks': landmarks,
            'images': images,
            'forms': forms,
            'interactive': interactive,
            'headings': headings,
            'links': links,
            'focus': focus,
            'contrast': contrast,
            'language': language,
            'tables': tables,
            'media': media,
            'score_breakdown': breakdown,
            'keyboard': keyboard,
            'live_regions': live_regions,
            'page_structure': page_structure,
            'semantic': semantic,
            'touch_targets': touch_targets,
            'text_alternatives': text_alternatives,
            'timing': timing,
            'issues': self.issues[:30],
            'warnings': self.warnings[:30],
            'empty_alt_images': images.get('empty_alt_images', []),
            'summary': {
                'total_checks': total_checks,
                'passed': 0,
                'warnings': warning_count,
                'errors': error_count,
                'wcag_level': self._determine_wcag_level(error_count, warning_count)
            }
        }
    def _determine_wcag_level(self, errors: int, warnings: int) -> str:
        if errors == 0 and warnings <= 2:
            return 'AAA'
        elif errors <= 2 and warnings <= 5:
            return 'AA'
        elif errors <= 5:
            return 'A'
        return 'Non-compliant'
    def _get_element_details(self, element) -> dict:
        if isinstance(element, str):
            return {'selector': element, 'snippet': None}
        selector = element.name
        if element.get('id'):
            selector += f"#{element['id']}"
        elif element.get('class'):
            selector += f".{'.'.join(element['class'])}"
        parent = element.find_parent()
        if parent:
            parent_sel = parent.name
            if parent.get('id'):
                parent_sel += f"#{parent['id']}"
            elif parent.get('class'):
                parent_sel += f".{parent['class'][0]}"
            selector = f"{parent_sel} > {selector}"
        snippet = str(element)
        if len(snippet) > 150:
            attrs = ' '.join([f'{k}="{v}"' if isinstance(v, str) else f'{k}="{" ".join(v)}"' for k, v in element.attrs.items()])
            snippet = f"<{element.name} {attrs}>...</{element.name}>"
            if len(snippet) > 150:
                snippet = snippet[:147] + "..."
        return {
            'selector': selector,
            'snippet': snippet
        }
    def _analyze_aria_usage(self) -> dict:
        aria_elements = []
        aria_counts = Counter()
        role_counts = Counter()
        for element in self.soup.find_all(
            lambda tag: any(attr.startswith('aria-') for attr in tag.attrs) or tag.get('role')
        ):
            role = element.get('role')
            aria_attrs = {}
            for attr in element.attrs:
                if attr.startswith('aria-'):
                    aria_attrs[attr] = element.get(attr)
                    aria_counts[attr] += 1
            if role:
                role_counts[role] += 1
                aria_attrs['role'] = role
            if role or aria_attrs:
                aria_elements.append({
                    'tag': element.name,
                    'attributes': aria_attrs,
                    'text': element.get_text()[:50] if element.get_text() else ''
                })
        self._check_aria_misuses()
        return {
            'total_aria_elements': len(aria_elements),
            'aria_attribute_counts': dict(aria_counts.most_common(10)),
            'role_counts': dict(role_counts.most_common(10)),
            'elements': aria_elements[:15],
            'has_aria': len(aria_elements) > 0
        }

    def _check_aria_misuses(self):
        hidden_focusable = self.soup.find_all(
            lambda tag: tag.get('aria-hidden') == 'true' and
            (tag.name in INTERACTIVE_ELEMENTS or tag.get('tabindex'))
        )
        for elem in hidden_focusable[:3]:
            details = self._get_element_details(elem)
            self.issues.append({
                'type': 'error',
                'category': 'ARIA',
                'element': details['selector'],
                'snippet': details['snippet'],
                'issue': 'aria-hidden="true" on focusable element',
                'fix': 'Do not hide focusable elements with aria-hidden'
            })
        role_buttons = self.soup.find_all(attrs={'role': 'button'})
        for btn in role_buttons:
            if btn.name not in ['button', 'input'] and not btn.get('tabindex'):
                details = self._get_element_details(btn)
                self.issues.append({
                    'type': 'error',
                    'category': 'ARIA',
                    'element': details['selector'],
                    'snippet': details['snippet'],
                    'issue': 'role="button" without keyboard access',
                    'fix': 'Add tabindex="0" or use <button>'
                })
        labeled_non_interactive = self.soup.find_all(
            lambda tag: tag.get('aria-label') and
            tag.name in ['div', 'span', 'p'] and
            not tag.get('role') and
            not tag.get('tabindex')
        )
        for elem in labeled_non_interactive[:3]:
            details = self._get_element_details(elem)
            self.warnings.append({
                'type': 'warning',
                'category': 'ARIA',
                'element': details['selector'],
                'snippet': details['snippet'],
                'issue': 'aria-label on non-interactive element',
                'fix': 'Add an appropriate role or tabindex'
            })
        buttons_with_role = self.soup.find_all('button', attrs={'role': 'button'})
        for btn in buttons_with_role[:2]:
            details = self._get_element_details(btn)
            self.warnings.append({
                'type': 'warning',
                'category': 'ARIA',
                'element': details['selector'],
                'snippet': details['snippet'],
                'issue': 'Unnecessary role="button"',
                'fix': '<button> already has button role'
            })
    def _analyze_landmarks(self) -> dict:
        landmarks = {
            'main': [], 'navigation': [], 'banner': [], 'contentinfo': [],
            'complementary': [], 'search': [], 'form': [], 'region': []
        }
        tag_to_landmark = {
            'main': 'main', 'nav': 'navigation',
            'aside': 'complementary'
        }
        target_tags = {'main', 'nav', 'header', 'footer', 'aside'}
        for el in self.soup.find_all(
            lambda tag: tag.name in target_tags or tag.get('role') in landmarks
        ):
            role = el.get('role')
            if role and role in landmarks:
                landmarks[role].append({'tag': el.name, 'label': el.get('aria-label', '')})
            elif el.name in tag_to_landmark:
                landmarks[tag_to_landmark[el.name]].append(
                    {'tag': el.name, 'label': el.get('aria-label', '')}
                )
            elif el.name == 'header':
                if not el.find_parent(['article', 'aside', 'main', 'nav', 'section']):
                    landmarks['banner'].append({'tag': 'header', 'label': el.get('aria-label', '')})
            elif el.name == 'footer':
                if not el.find_parent(['article', 'aside', 'main', 'nav', 'section']):
                    landmarks['contentinfo'].append({'tag': 'footer', 'label': el.get('aria-label', '')})
        main_count = len(landmarks['main'])
        if main_count == 0:
            self.issues.append({
                'type': 'error', 'category': 'Landmarks', 'element': 'main',
                'issue': '<main> or role="main" not found',
                'fix': 'Add <main> tag for main content'
            })
        elif main_count > 1:
            self.warnings.append({
                'type': 'warning', 'category': 'Landmarks', 'element': 'main',
                'issue': f'Multiple main landmarks ({main_count} count)',
                'fix': 'There should be only one <main> on the page'
            })
        nav_count = len(landmarks['navigation'])
        if nav_count > 1:
            self.warnings.append({
                'type': 'warning', 'category': 'Landmarks', 'element': 'nav',
                'issue': f'Multiple navigation landmarks ({nav_count} count)',
                'fix': 'Use aria-label to distinguish or reduce the count'
            })
        has_all_critical = main_count > 0 and nav_count > 0
        if main_count > 0 and nav_count == 0:
            self.warnings.append({
                'type': 'warning', 'category': 'Landmarks', 'element': 'nav',
                'issue': 'Navigation landmark not found',
                'fix': 'Add <nav> tag or role="navigation"'
            })
        if len(landmarks['banner']) == 0:
            self.warnings.append({
                'type': 'warning', 'category': 'Landmarks', 'element': 'header',
                'issue': 'Banner landmark (header) not found',
                'fix': 'Add <header> tag'
            })
        if len(landmarks['contentinfo']) == 0:
            self.warnings.append({
                'type': 'warning', 'category': 'Landmarks', 'element': 'footer',
                'issue': 'Contentinfo landmark (footer) not found',
                'fix': 'Add <footer> tag'
            })
        return {
            'landmarks': landmarks,
            'has_main': main_count > 0,
            'has_navigation': nav_count > 0,
            'has_header': len(landmarks['banner']) > 0,
            'has_footer': len(landmarks['contentinfo']) > 0,
            'total_landmarks': sum(len(v) for v in landmarks.values()),
            'missing_critical': [] if has_all_critical else (
                (['main'] if main_count == 0 else []) +
                (['nav'] if nav_count == 0 else [])
            )
        }
    def _analyze_images(self) -> dict:
        images = self._images
        missing_alt = []
        empty_alt = []
        decorative = []
        informative = []
        for img in images:
            src = img.get('src', '')[:60]
            alt = img.get('alt')
            if alt is None:
                missing_alt.append({'src': src})
                details = self._get_element_details(img)
                self.issues.append({
                    'type': 'error',
                    'category': 'Images',
                    'element': details['selector'],
                    'snippet': details['snippet'],
                    'issue': f'alt attribute missing: {src[:30]}...',
                    'fix': 'Add alt attribute to all images'
                })
            elif alt == '':
                empty_alt.append({'src': src})
                decorative.append({'src': src})
            else:
                informative.append({'src': src, 'alt': alt[:50], 'element': img})
        for img_data in informative[:5]:
            img_element = img_data['element']
            alt = img_data.get('alt', '')
            if alt.lower() in ['image', 'img', 'photo', 'picture', 'resim', 'görsel']:
                details = self._get_element_details(img_element)
                self.warnings.append({
                    'type': 'warning',
                    'category': 'Images',
                    'element': details['selector'],
                    'snippet': details['snippet'],
                    'issue': 'Generic alt text used',
                    'fix': 'Use descriptive alt text'
                })
        return {
            'total': len(images),
            'missing_alt': len(missing_alt),
            'empty_alt': len(empty_alt),
            'decorative': len(decorative),
            'informative': len(informative),
            'status': 'success' if len(missing_alt) == 0 else 'error',
            'samples': informative[:5],
            'empty_alt_images': empty_alt
        }
    def _analyze_forms(self) -> dict:
        forms = self._forms
        inputs = self._inputs
        issues_found = []
        unlabeled = 0
        labeled = 0
        for inp in inputs:
            inp_type = inp.get('type', 'text')
            if inp_type in ['hidden', 'submit', 'button', 'reset', 'image']:
                continue
            inp_id = inp.get('id')
            has_label = False
            if inp_id:
                label = self.soup.find('label', attrs={'for': inp_id})
                if label:
                    has_label = True
            if inp.get('aria-label') or inp.get('aria-labelledby'):
                has_label = True
            parent_label = inp.find_parent('label')
            if parent_label:
                has_label = True
            if inp.get('placeholder') and not has_label:
                details = self._get_element_details(inp)
                self.warnings.append({
                    'type': 'warning',
                    'category': 'Forms',
                    'element': details['selector'],
                    'snippet': details['snippet'],
                    'issue': 'Placeholder used only as label',
                    'fix': 'Add <label> or aria-label'
                })
            if has_label:
                labeled += 1
            else:
                unlabeled += 1
                details = self._get_element_details(inp)
                self.issues.append({
                    'type': 'error',
                    'category': 'Forms',
                    'element': details['selector'],
                    'snippet': details['snippet'],
                    'issue': f'Form element without label ({inp.get("name", inp.get("type", "unknown"))})',
                    'fix': 'Match with <label for="...">'
                })
        required_inputs = self.soup.find_all(['input', 'select', 'textarea'], attrs={'required': True})
        aria_required = self.soup.find_all(['input', 'select', 'textarea'], attrs={'aria-required': 'true'})
        return {
            'total_forms': len(forms),
            'total_inputs': len(inputs),
            'labeled': labeled,
            'unlabeled': unlabeled,
            'required_fields': len(required_inputs) + len(aria_required),
            'status': 'success' if unlabeled == 0 else 'error'
        }
    def _analyze_interactive_elements(self) -> dict:
        buttons = self._buttons
        empty_buttons = [b for b in buttons if not b.get_text(strip=True) and not b.get('aria-label')]
        for btn in empty_buttons[:3]:
            details = self._get_element_details(btn)
            self.issues.append({
                'type': 'error',
                'category': 'Interactive',
                'element': details['selector'],
                'snippet': details['snippet'],
                'issue': 'Empty button (no text or aria-label)',
                'fix': 'Add button content or aria-label'
            })
        clickable_divs = self.soup.find_all('div', attrs={'onclick': True})
        for div in clickable_divs[:3]:
            if not div.get('role') and not div.get('tabindex'):
                details = self._get_element_details(div)
                self.issues.append({
                    'type': 'error',
                    'category': 'Interactive',
                    'element': details['selector'],
                    'snippet': details['snippet'],
                    'issue': 'Clickable div is not accessible',
                    'fix': 'Add role="button" and tabindex="0"'
                })
        def _safe_positive_tabindex(x):
            try:
                return x is not None and int(x) > 0
            except (ValueError, TypeError):
                return False
        positive_tabindex = self.soup.find_all(attrs={'tabindex': _safe_positive_tabindex})
        if positive_tabindex:
            details = self._get_element_details(positive_tabindex[0])
            self.warnings.append({
                'type': 'warning',
                'category': 'Interactive',
                'element': details['selector'],
                'snippet': details['snippet'],
                'issue': f'{len(positive_tabindex)} positive tabindex uses',
                'fix': 'Prefer tabindex="0" or "-1"'
            })
        return {
            'total': len(buttons) + len(clickable_divs),
            'buttons': len(buttons),
            'empty_buttons': len(empty_buttons),
            'clickable_divs': len(clickable_divs),
            'positive_tabindex': len(positive_tabindex),
            'elements': [
                {'tag': 'button', 'text': b.get_text(strip=True)[:30] or 'Empty', 'type': 'Button'} for b in buttons
            ] + [
                {'tag': 'div', 'text': d.get_text(strip=True)[:30], 'type': 'Clickable Div'} for d in clickable_divs
            ]
        }
    def _analyze_heading_structure(self) -> dict:
        headings = []
        prev_level = 0
        skip_issues = []
        for h in self._headings:
            level = int(h.name[1])
            text = h.get_text(strip=True)[:50]
            headings.append({'level': level, 'text': text})
            if prev_level > 0 and level > prev_level + 1:
                skip_issues.append({'from': prev_level, 'to': level, 'element': h})
            prev_level = level
        for issue in skip_issues:
            details = self._get_element_details(issue['element'])
            self.warnings.append({
                'type': 'warning',
                'category': 'Headings',
                'element': details['selector'],
                'snippet': details['snippet'],
                'issue': f'Heading level skipped: H{issue["from"]} → H{issue["to"]}',
                'fix': 'Fix heading hierarchy (should be sequential)'
            })
        h1s = [h for h in headings if h['level'] == 1]
        if len(h1s) == 0:
            self.issues.append({
                'type': 'error',
                'category': 'Headings',
                'element': 'h1',
                'issue': 'H1 heading not found',
                'fix': 'Add a single H1 heading for the page'
            })
        return {
            'total': len(headings),
            'structure': headings[:10],
            'skip_issues': skip_issues,
            'has_h1': len(h1s) > 0
        }
    def _analyze_links(self) -> dict:
        links = self._links
        empty_links = []
        generic_links = []
        new_tab_links = []
        generic_texts = ['click here', 'read more', 'learn more', 'tıklayın', 'devamı', 'daha fazla', 'buraya tıklayın']
        for link in links:
            href = link.get('href', '').strip()
            if not href or href.startswith(('javascript:', '#')):
                continue
            text = link.get_text(strip=True)
            aria_label = link.get('aria-label', '')
            target = link.get('target', '')
            effective_text = aria_label or text
            if not effective_text:
                img = link.find('img')
                if img and img.get('alt'):
                    effective_text = img.get('alt')
            if not effective_text:
                empty_links.append({'href': href[:50], 'element': link})
            elif effective_text.lower() in generic_texts:
                generic_links.append({'text': effective_text, 'href': href[:30], 'element': link})
            if target == '_blank':
                if 'external' not in (link.get('class', []) or []) and 'new tab' not in aria_label.lower():
                    new_tab_links.append({'text': effective_text[:30] if effective_text else '[empty]', 'element': link})
        for link_data in empty_links[:3]:
            details = self._get_element_details(link_data['element'])
            self.issues.append({
                'type': 'error',
                'category': 'Links',
                'element': details['selector'],
                'snippet': details['snippet'],
                'issue': f'Empty link: {link_data["href"][:30]}',
                'fix': 'Add link text or aria-label'
            })
        for link_data in generic_links[:2]:
            details = self._get_element_details(link_data['element'])
            self.warnings.append({
                'type': 'warning',
                'category': 'Links',
                'element': details['selector'],
                'snippet': details['snippet'],
                'issue': f'Generic link text: "{link_data["text"]}"',
                'fix': 'Use descriptive link text'
            })
        if new_tab_links:
            details = self._get_element_details(new_tab_links[0]['element'])
            self.warnings.append({
                'type': 'warning',
                'category': 'Links',
                'element': details['selector'],
                'snippet': details['snippet'],
                'issue': f'{len(new_tab_links)} links open in a new tab (without warning)',
                'fix': 'Add "Opens in new tab" indicator'
            })
        return {
            'empty': len(empty_links),
            'generic': len(generic_links),
            'new_tab': len(new_tab_links),
            'status': 'success' if len(empty_links) == 0 else 'error'
        }
    def _analyze_focus_management(self) -> dict:
        skip_link = (self.soup.find('a', href='#main') or
                     self.soup.find('a', href='#content') or
                     self.soup.find('a', string=re.compile(r'skip|atla|içeriğe', re.I)))
        has_skip_link = skip_link is not None
        if not has_skip_link:
            self.warnings.append({
                'type': 'warning',
                'category': 'Focus',
                'element': 'skip-link',
                'issue': 'Skip link not found',
                'fix': 'Add "Skip to main content" link'
            })
        styles = self.soup.find_all('style')
        inline_styles = self.soup.find_all(attrs={'style': lambda x: x and 'outline' in x.lower()})
        outline_removed = False
        for style in styles:
            if style.string and ('outline: none' in style.string or 'outline:none' in style.string):
                outline_removed = True
                break
        if outline_removed or inline_styles:
            self.warnings.append({
                'type': 'warning',
                'category': 'Focus',
                'element': 'style',
                'issue': 'Focus outline might be removed',
                'fix': 'Do not remove focus indicator or provide an alternative'
            })
        return {
            'has_skip_link': has_skip_link,
            'outline_issues': outline_removed or len(inline_styles) > 0
        }
    def _analyze_contrast_hints(self) -> dict:
        small_text_indicators = self.soup.find_all(
            lambda tag: tag.get('style') and
            ('font-size' in tag.get('style', '') and
             any(size in tag.get('style', '') for size in ['10px', '9px', '8px', '0.6em', '0.5em']))
        )
        if small_text_indicators:
            self.warnings.append({
                'type': 'warning',
                'category': 'Contrast',
                'element': '*',
                'issue': f'{len(small_text_indicators)} potential very small text',
                'fix': 'Use minimum 12px font size'
            })
        color_indicators = self.soup.find_all(
            lambda tag: tag.get('style') and
            'color' in tag.get('style', '') and
            tag.name in ['span', 'div'] and
            not tag.get('aria-label')
        )
        return {
            'small_text_count': len(small_text_indicators),
            'color_only_count': len(color_indicators),
            'status': 'success' if not small_text_indicators else 'warning'
        }
    def _analyze_language(self) -> dict:
        html_tag = self.soup.find('html')
        lang = html_tag.get('lang', '') if html_tag else ''
        xml_lang = html_tag.get('xml:lang', '') if html_tag else ''
        if not lang and not xml_lang:
            self.issues.append({
                'type': 'error',
                'category': 'Dil',
                'element': 'html',
                'issue': 'Page language is not defined',
                'fix': 'Specify language like <html lang="en">'
            })
        lang_changes = self.soup.find_all(attrs={'lang': True})
        lang_changes = [el for el in lang_changes if el.name != 'html']
        hreflang_tags = self.soup.find_all('link', attrs={'hreflang': True})
        hreflang_meta = self.soup.find_all('a', attrs={'hreflang': True})
        total_hreflang = len(hreflang_tags) + len(hreflang_meta)
        alternate_languages = set()
        for tag in hreflang_tags:
            hreflang_val = tag.get('hreflang', '')
            if hreflang_val and hreflang_val != 'x-default':
                alternate_languages.add(hreflang_val)
        is_multilingual = total_hreflang > 0 or len(lang_changes) > 0
        return {
            'primary_language': lang or xml_lang,
            'has_language': bool(lang or xml_lang),
            'language_changes': len(lang_changes),
            'hreflang_count': total_hreflang,
            'alternate_languages': list(alternate_languages)[:5],
            'is_multilingual': is_multilingual,
            'status': 'success' if lang or xml_lang else 'error'
        }
    def _analyze_tables(self) -> dict:
        tables = self._tables
        data_tables = []
        layout_tables = []
        issues = []
        for table in tables:
            if table.get('role') == 'presentation':
                layout_tables.append(table)
                continue
            headers = table.find_all('th')
            caption = table.find('caption')
            summary = table.get('summary', '')
            scope_count = len(table.find_all(attrs={'scope': True}))
            table_info = {
                'has_headers': len(headers) > 0,
                'has_caption': caption is not None,
                'has_summary': bool(summary),
                'header_count': len(headers),
                'scope_count': scope_count
            }
            data_tables.append(table_info)
            if len(headers) == 0:
                self.issues.append({
                    'type': 'error',
                    'category': 'Tablolar',
                    'element': 'table',
                    'issue': 'Table heading (<th>) not found',
                    'fix': 'Add <th> tags for table columns'
                })
            elif scope_count == 0 and len(headers) > 1:
                self.warnings.append({
                    'type': 'warning',
                    'category': 'Tablolar',
                    'element': 'th',
                    'issue': 'Scope attribute missing in table headings',
                    'fix': 'Add <th scope="col"> or <th scope="row">'
                })
            if not caption and not summary:
                self.warnings.append({
                    'type': 'warning',
                    'category': 'Tablolar',
                    'element': 'table',
                    'issue': 'Table caption missing',
                    'fix': 'Explain table purpose with <caption>'
                })
        return {
            'total': len(tables),
            'data_tables': len(data_tables),
            'layout_tables': len(layout_tables),
            'tables': data_tables[:5],
            'status': 'success' if not issues else 'warning'
        }
    def _analyze_media_accessibility(self) -> dict:
        videos = self._videos
        audios = self._audios
        iframes = self._iframes
        videos_with_captions = 0
        videos_with_controls = 0
        for video in videos:
            tracks = video.find_all('track')
            captions = [t for t in tracks if t.get('kind') in ['captions', 'subtitles']]
            if captions:
                videos_with_captions += 1
            else:
                self.warnings.append({
                    'type': 'warning',
                    'category': 'Medya',
                    'element': 'video',
                    'issue': 'Video captions not found',
                    'fix': 'Add subtitles with <track kind="captions">'
                })
            if video.get('controls') is not None:
                videos_with_controls += 1
        video_embeds = [i for i in iframes if any(
            platform in i.get('src', '')
            for platform in ['youtube', 'vimeo', 'dailymotion']
        )]
        for embed in video_embeds[:3]:
            if not embed.get('title'):
                self.warnings.append({
                    'type': 'warning',
                    'category': 'Medya',
                    'element': 'iframe',
                    'issue': 'Video iframe has no title',
                    'fix': 'Add title attribute to iframe element'
                })
        for audio in audios:
            if not audio.get('controls'):
                self.warnings.append({
                    'type': 'warning',
                    'category': 'Medya',
                    'element': 'audio',
                    'issue': 'Audio controls missing',
                    'fix': 'Add controls attribute'
                })
        return {
            'videos': len(videos),
            'audios': len(audios),
            'video_embeds': len(video_embeds),
            'videos_with_captions': videos_with_captions,
            'videos_with_controls': videos_with_controls,
            'status': 'success' if videos_with_captions == len(videos) or len(videos) == 0 else 'warning'
        }
    def _analyze_keyboard_accessibility(self) -> dict:
        issues_found = []
        warnings_found = []
        try:
            negative_tabindex = []
            for tag in self.soup.find_all(attrs={'tabindex': True}):
                try:
                    tabindex_val = int(tag.get('tabindex', 0))
                    if tabindex_val < -1:
                        negative_tabindex.append(tag)
                except (ValueError, TypeError):
                    pass
        except Exception:
            negative_tabindex = []
        click_handlers = ['onclick', 'onmousedown', 'onmouseup', 'ondblclick']
        unique_click_elements = self.soup.find_all(
            lambda tag: any(tag.get(h) for h in click_handlers)
        )
        inaccessible_clicks = []
        for el in unique_click_elements:
            tag_name = el.name.lower()
            if tag_name in ['a', 'button', 'input', 'select', 'textarea', 'summary']:
                continue
            if el.find_parent('a') or el.find_parent('button'):
                continue
            has_role = el.get('role') in ['button', 'link', 'menuitem', 'tab', 'checkbox', 'radio', 'switch']
            has_tabindex = el.get('tabindex') is not None
            if not has_role and not has_tabindex:
                inaccessible_clicks.append({
                    'tag': tag_name,
                    'text': el.get_text(strip=True)[:30] or '[empty]',
                    'handler': [h for h in click_handlers if el.get(h)][:1][0] if any(el.get(h) for h in click_handlers) else 'onclick'
                })
        for item in inaccessible_clicks[:5]:
            self.issues.append({
                'type': 'error',
                'category': 'Klavye',
                'element': f'{item["tag"]}[{item["handler"]}]',
                'issue': f'Klavye ile erişilemeyen element: "{item["text"]}"',
                'fix': 'tabindex="0" ve role="button" ekleyin veya <button> kullanın'
            })
        mouse_only_handlers = ['onmouseover', 'onmouseout', 'onmouseenter', 'onmouseleave']
        mouse_only_elements = []
        for handler in mouse_only_handlers:
            for el in self.soup.find_all(attrs={handler: True}):
                has_keyboard_alt = el.get('onfocus') or el.get('onblur') or el.get('onkeydown') or el.get('onkeyup')
                if not has_keyboard_alt:
                    mouse_only_elements.append({
                        'tag': el.name,
                        'handler': handler
                    })
        for item in mouse_only_elements[:3]:
            self.warnings.append({
                'type': 'warning',
                'category': 'Klavye',
                'element': f'{item["tag"]}[{item["handler"]}]',
                'issue': 'Mouse-only etkileşim, klavye alternatifi yok',
                'fix': 'onfocus/onblur veya onkeydown ekleyin'
            })
        accesskeys = self.soup.find_all(attrs={'accesskey': True})
        accesskey_values = [el.get('accesskey', '').lower() for el in accesskeys]
        duplicates = [k for k in set(accesskey_values) if accesskey_values.count(k) > 1 and k]
        if duplicates:
            self.warnings.append({
                'type': 'warning',
                'category': 'Klavye',
                'element': '*[accesskey]',
                'issue': f'Çakışan accesskey değerleri: {", ".join(duplicates)}',
                'fix': 'Her accesskey benzersiz olmalı'
            })
        modals = self.soup.find_all(attrs={'role': 'dialog'})
        modals.extend(self.soup.find_all(attrs={'role': 'alertdialog'}))
        for modal in modals[:2]:
            if not modal.get('aria-modal'):
                self.warnings.append({
                    'type': 'warning',
                    'category': 'Klavye',
                    'element': 'dialog',
                    'issue': 'Modal dialog aria-modal özelliği eksik',
                    'fix': 'aria-modal="true" ekleyin'
                })
        total_click_handlers = len(unique_click_elements)
        inaccessible_count = len(inaccessible_clicks)
        if inaccessible_count > 0:
            status = 'error'
            status_message = f'{inaccessible_count} element klavye ile erişilemiyor'
        elif len(mouse_only_elements) > 0:
            status = 'warning'
            status_message = f'{len(mouse_only_elements)} mouse-only element'
        elif total_click_handlers == 0:
            status = 'info'
            status_message = 'Inline click handler bulunamadı'
        else:
            status = 'success'
            status_message = 'Tüm elementler erişilebilir'
        return {
            'total_click_handlers': total_click_handlers,
            'onclick_inaccessible': inaccessible_count,
            'inaccessible_elements': inaccessible_clicks[:5],
            'mouse_only_events': len(mouse_only_elements),
            'negative_tabindex': len(negative_tabindex),
            'accesskey_duplicates': len(duplicates),
            'modals_checked': len(modals),
            'status': status,
            'status_message': status_message
        }
    def _analyze_live_regions(self) -> dict:
        live_regions = self.soup.find_all(attrs={'aria-live': True})
        alerts = self.soup.find_all(attrs={'role': 'alert'})
        status = self.soup.find_all(attrs={'role': 'status'})
        log = self.soup.find_all(attrs={'role': 'log'})
        for region in live_regions:
            live_value = region.get('aria-live')
            if live_value not in ['polite', 'assertive', 'off']:
                self.warnings.append({
                    'type': 'warning',
                    'category': 'Live Regions',
                    'element': region.name,
                    'issue': f'Geçersiz aria-live değeri: {live_value}',
                    'fix': 'polite, assertive veya off kullanın'
                })
        has_live_regions = len(live_regions) + len(alerts) + len(status) + len(log) > 0
        return {
            'total': len(live_regions) + len(alerts) + len(status) + len(log),
            'aria_live': len(live_regions),
            'alerts': len(alerts),
            'status': len(status),
            'log': len(log),
            'has_live_regions': has_live_regions
        }
    def _analyze_page_structure(self) -> dict:
        title = self.soup.find('title')
        title_text = title.get_text(strip=True) if title else ''
        if not title_text:
            self.issues.append({
                'type': 'error',
                'category': 'Sayfa Yapısı',
                'element': 'title',
                'issue': 'Sayfa başlığı (<title>) bulunamadı',
                'fix': 'Anlamlı bir <title> etiketi ekleyin'
            })
        elif len(title_text) < 10:
            self.warnings.append({
                'type': 'warning',
                'category': 'Sayfa Yapısı',
                'element': 'title',
                'issue': 'Sayfa başlığı çok kısa',
                'fix': 'Daha açıklayıcı bir başlık kullanın'
            })
        viewport = self.soup.find('meta', attrs={'name': 'viewport'})
        viewport_content = viewport.get('content', '') if viewport else ''
        if viewport and 'user-scalable=no' in viewport_content:
            self.issues.append({
                'type': 'error',
                'category': 'Sayfa Yapısı',
                'element': 'meta[viewport]',
                'issue': 'Kullanıcı yakınlaştırması engellenmiş',
                'fix': 'user-scalable=no kaldırın, minimum-scale/maximum-scale kullanmayın'
            })
        elif viewport and 'maximum-scale=1' in viewport_content:
            self.warnings.append({
                'type': 'warning',
                'category': 'Sayfa Yapısı',
                'element': 'meta[viewport]',
                'issue': 'Yakınlaştırma sınırlandırılmış',
                'fix': 'maximum-scale kısıtlamasını kaldırın'
            })
        return {
            'has_title': bool(title_text),
            'title_length': len(title_text),
            'title_text': title_text[:60],
            'has_viewport': viewport is not None,
            'zoom_disabled': 'user-scalable=no' in viewport_content if viewport else False
        }
    def _analyze_semantic_html(self) -> dict:
        semantic_tag_names = ['header', 'main', 'nav', 'footer', 'article', 'section',
                              'aside', 'figure', 'figcaption', 'time', 'mark', 'details']
        all_tags = semantic_tag_names + ['div', 'span']
        from collections import Counter as _Counter
        found = self.soup.find_all(all_tags)
        counts = _Counter(el.name for el in found)
        semantic_elements = {tag: counts.get(tag, 0) for tag in semantic_tag_names}
        total_semantic = sum(semantic_elements.values())
        all_divs = counts.get('div', 0)
        all_spans = counts.get('span', 0)
        div_ratio = all_divs / (total_semantic + 1) if total_semantic > 0 else float('inf')
        if total_semantic == 0:
            self.warnings.append({
                'type': 'warning',
                'category': 'Semantik',
                'element': '*',
                'issue': 'Semantik HTML elementleri kullanılmamış',
                'fix': 'header, main, nav, footer gibi semantik etiketler kullanın'
            })
        elif div_ratio > 10:
            self.warnings.append({
                'type': 'warning',
                'category': 'Semantik',
                'element': 'div',
                'issue': f'Çok fazla div kullanımı ({all_divs} div)',
                'fix': 'Uygun yerlerde semantik elementler tercih edin'
            })
        b_tags = len(self.soup.find_all('b'))
        i_tags = len(self.soup.find_all('i'))
        strong_tags = len(self.soup.find_all('strong'))
        em_tags = len(self.soup.find_all('em'))
        if b_tags > strong_tags:
            self.warnings.append({
                'type': 'warning',
                'category': 'Semantik',
                'element': 'b',
                'issue': f'<b> yerine <strong> tercih edilmeli ({b_tags} b, {strong_tags} strong)',
                'fix': 'Önem için <strong>, stil için CSS kullanın'
            })
        return {
            'elements': semantic_elements,
            'total_semantic': total_semantic,
            'div_count': all_divs,
            'span_count': all_spans,
            'div_ratio': round(div_ratio, 2) if div_ratio != float('inf') else 'N/A',
            'status': 'success' if total_semantic > 0 else 'warning'
        }
    def _analyze_touch_targets(self) -> dict:
        clickable_elements = self.soup.find_all(['a', 'button', 'input', 'select', 'textarea'])
        small_targets = []
        inline_styles_checked = 0
        for el in clickable_elements:
            style = el.get('style', '')
            if style:
                inline_styles_checked += 1
                if any(size in style for size in ['width:1', 'height:1', 'width: 1', 'height: 1']):
                    small_targets.append(el.name)
        short_links = []
        for link in self.soup.find_all('a'):
            text = link.get_text(strip=True)
            if text and len(text) <= 2 and not link.get('aria-label'):
                short_links.append({'text': text, 'href': link.get('href', '')[:30]})
        if short_links and len(short_links) > 2:
            self.warnings.append({
                'type': 'warning',
                'category': 'Touch Targets',
                'element': 'a',
                'issue': f'{len(short_links)} çok kısa link metni',
                'fix': 'Daha uzun link metni veya daha büyük tıklama alanı sağlayın'
            })
        return {
            'total_clickable': len(clickable_elements),
            'short_links': len(short_links),
            'short_link_samples': short_links[:5],
            'status': 'success' if len(short_links) <= 2 else 'warning'
        }
    def _analyze_text_alternatives(self) -> dict:
        svgs = self.soup.find_all('svg')
        svg_issues = []
        for svg in svgs:
            has_title = svg.find('title') is not None
            has_desc = svg.find('desc') is not None
            has_aria_label = svg.get('aria-label') or svg.get('aria-labelledby')
            has_role = svg.get('role')
            if not (has_title or has_aria_label):
                if has_role != 'presentation' and has_role != 'img':
                    svg_issues.append('missing_accessible_name')
        if svg_issues and len(svg_issues) > 0:
            self.warnings.append({
                'type': 'warning',
                'category': 'Metin Alternatifleri',
                'element': 'svg',
                'issue': f'{len(svg_issues)} SVG erişilebilir isim yok',
                'fix': '<title> veya aria-label ekleyin'
            })
        icon_elements = self.soup.find_all(
            lambda tag: tag.name == 'i' and
            any(cls.startswith(('fa-', 'icon-', 'glyphicon')) for cls in tag.get('class', []))
        )
        icons_without_label = []
        for icon in icon_elements:
            parent = icon.parent
            if parent:
                parent_text = parent.get_text(strip=True)
                parent_label = parent.get('aria-label', '')
                if not parent_text and not parent_label:
                    icons_without_label.append(icon)
        if icons_without_label and len(icons_without_label) > 3:
            self.warnings.append({
                'type': 'warning',
                'category': 'Metin Alternatifleri',
                'element': 'i.icon',
                'issue': f'{len(icons_without_label)} ikon etiketsiz',
                'fix': 'aria-hidden="true" veya sr-only metin ekleyin'
            })
        return {
            'svgs': len(svgs),
            'svg_issues': len(svg_issues),
            'icon_fonts': len(icon_elements),
            'icons_without_label': len(icons_without_label),
            'status': 'success' if len(svg_issues) == 0 else 'warning'
        }
    def _analyze_timing_controls(self) -> dict:
        meta_refresh = self.soup.find('meta', attrs={'http-equiv': 'refresh'})
        if meta_refresh:
            content = meta_refresh.get('content', '')
            self.issues.append({
                'type': 'error',
                'category': 'Zamanlama',
                'element': 'meta[refresh]',
                'issue': f'Meta refresh kullanılıyor: {content[:30]}',
                'fix': 'Otomatik yenileme yerine kullanıcı kontrolü sağlayın'
            })
        autoplay_videos = self.soup.find_all('video', attrs={'autoplay': True})
        autoplay_audios = self.soup.find_all('audio', attrs={'autoplay': True})
        for video in autoplay_videos:
            if not video.get('muted'):
                self.issues.append({
                    'type': 'error',
                    'category': 'Zamanlama',
                    'element': 'video[autoplay]',
                    'issue': 'Sesli video otomatik oynatılıyor',
                    'fix': 'muted özelliği ekleyin veya autoplay kaldırın'
                })
        if autoplay_audios:
            self.issues.append({
                'type': 'error',
                'category': 'Zamanlama',
                'element': 'audio[autoplay]',
                'issue': 'Audio otomatik oynatılıyor',
                'fix': 'Autoplay kaldırın, kullanıcının başlatmasına izin verin'
            })
        marquees = self.soup.find_all('marquee')
        blinks = self.soup.find_all('blink')
        if marquees:
            self.issues.append({
                'type': 'error',
                'category': 'Zamanlama',
                'element': 'marquee',
                'issue': f'{len(marquees)} hareketli yazı (marquee)',
                'fix': 'Marquee kullanmayın, CSS animasyonlarını durdurmayı sağlayın'
            })
        return {
            'has_meta_refresh': meta_refresh is not None,
            'autoplay_videos': len(autoplay_videos),
            'autoplay_audios': len(autoplay_audios),
            'marquees': len(marquees),
            'blinks': len(blinks),
            'status': 'error' if (meta_refresh or autoplay_audios or marquees) else 'success'
        }
    def _calculate_weighted_score(self, images, forms, interactive, aria, headings, links, language, keyboard):
        breakdown = {}
        total_weighted_score = 0
        active_weight = 0.0
        img_total = images.get('total', 0)
        img_score = 100
        img_details = []
        if img_total > 0:
            missing_alt = images.get('missing_alt', 0)
            empty_alt = images.get('empty_alt', 0)
            img_details.append({'label': 'Toplam Görsel', 'value': f"{img_total} adet", 'status': 'neutral'})
            if missing_alt > 0:
                deduction = min(100, (missing_alt / img_total) * 150)
                img_score -= deduction
                img_details.append({
                    'label': 'Eksik Alt Etiketi',
                    'value': f"{missing_alt} adet",
                    'impact': f"-{int(deduction)} Puan",
                    'status': 'error'
                })
            else:
                img_details.append({'label': 'Alt Etiketleri', 'value': 'Tamam', 'impact': '+20 Puan', 'status': 'success'})
            if empty_alt > 0:
                img_details.append({'label': 'Boş Alt (Dekoratif)', 'value': f"{empty_alt} adet", 'status': 'warning'})
            img_score = max(0, int(img_score))
            active_weight += 0.20
            total_weighted_score += img_score * 0.20
            breakdown['images'] = {
                'score': img_score,
                'weight': 20,
                'details': img_details
            }
        else:
            breakdown['images'] = None
        form_total = forms.get('total_inputs', 0)
        form_score = 100
        form_details = []
        if form_total > 0:
            unlabeled = forms.get('unlabeled', 0)
            form_details.append({'label': 'Form Elemanları', 'value': f"{form_total} adet", 'status': 'neutral'})
            if unlabeled > 0:
                deduction = min(100, (unlabeled / form_total) * 120)
                form_score -= deduction
                form_details.append({
                    'label': 'Etiketsiz Alanlar',
                    'value': f"{unlabeled} adet",
                    'impact': f"-{int(deduction)} Puan",
                    'status': 'error'
                })
            else:
                form_details.append({'label': 'Etiketleme', 'value': 'Kusursuz', 'impact': '+20 Puan', 'status': 'success'})
            form_score = max(0, int(form_score))
            active_weight += 0.20
            total_weighted_score += form_score * 0.20
            breakdown['forms'] = {
                'score': form_score,
                'weight': 20,
                'details': form_details
            }
        else:
            breakdown['forms'] = None
        int_score = 100
        int_details = []
        if keyboard.get('status') == 'error':
            int_score -= 40
            int_details.append({'label': 'Klavye Erişimi', 'value': 'Hatalı', 'impact': '-40 Puan', 'status': 'error'})
        else:
            int_details.append({'label': 'Klavye Erişimi', 'value': 'Uygun', 'impact': '+15 Puan', 'status': 'success'})
        onclick_bad = keyboard.get('onclick_inaccessible', 0)
        if onclick_bad > 0:
            int_score -= 20
            int_details.append({'label': 'Erişilmez Tıklamalar', 'value': f"{onclick_bad} adet", 'impact': '-20 Puan', 'status': 'warning'})
        empty_btns = interactive.get('empty_buttons', 0)
        if empty_btns > 0:
            deduction = min(30, empty_btns * 10)
            int_score -= deduction
            int_details.append({'label': 'Boş Butonlar', 'value': f"{empty_btns} adet", 'impact': f"-{deduction} Puan", 'status': 'error'})
        int_score = max(0, int(int_score))
        active_weight += 0.25
        total_weighted_score += int_score * 0.25
        breakdown['interactive'] = {
            'score': int_score,
            'weight': 25,
            'details': int_details
        }
        struct_score = 100
        struct_details = []
        headings_total = headings.get('total', 0)
        if headings_total == 0:
            struct_details.append({'label': 'Başlık Yapısı', 'value': 'Yok', 'impact': 'Bilgi', 'status': 'neutral'})
        else:
            if not headings.get('has_h1'):
                struct_score -= 25
                struct_details.append({'label': 'H1 Başlığı', 'value': 'Eksik', 'impact': '-25 Puan', 'status': 'error'})
            else:
                struct_details.append({'label': 'H1 Başlığı', 'value': 'Mevcut', 'impact': '+10 Puan', 'status': 'success'})
            skip_issues = len(headings.get('skip_issues', []))
            if skip_issues > 0:
                deduction = min(20, skip_issues * 5)
                struct_score -= deduction
                struct_details.append({'label': 'Hiyerarşi Hatası', 'value': f"{skip_issues} adet", 'impact': f"-{deduction} Puan", 'status': 'warning'})
        link_empty = links.get('empty', 0)
        if link_empty > 0:
            deduction = min(25, link_empty * 5)
            struct_score -= deduction
            struct_details.append({'label': 'Boş Linkler', 'value': f"{link_empty} adet", 'impact': f"-{deduction} Puan", 'status': 'error'})
        struct_score = max(0, int(struct_score))
        active_weight += 0.20
        total_weighted_score += struct_score * 0.20
        breakdown['structure'] = {
            'score': struct_score,
            'weight': 20,
            'details': struct_details
        }
        aria_score = 100
        aria_details = []
        if not language.get('has_language'):
            aria_score -= 40
            aria_details.append({'label': 'Dil Tanımı (<html lang>)', 'value': 'Eksik', 'impact': '-40 Puan', 'status': 'error'})
        else:
            aria_details.append({'label': 'Dil Tanımı', 'value': language.get('primary_language'), 'impact': '+20 Puan', 'status': 'success'})
        aria_issues_count = len([i for i in self.issues if i.get('category') == 'ARIA'])
        if aria_issues_count > 0:
            deduction = min(60, aria_issues_count * 10)
            aria_score -= deduction
            aria_details.append({'label': 'ARIA Hataları', 'value': f"{aria_issues_count} adet", 'impact': f"-{deduction} Puan", 'status': 'error'})
        aria_score = max(0, int(aria_score))
        active_weight += 0.15
        total_weighted_score += aria_score * 0.15
        breakdown['aria'] = {
            'score': aria_score,
            'weight': 15,
            'details': aria_details
        }
        if active_weight > 0:
            final_score = total_weighted_score / active_weight
        else:
            final_score = 0
        return {
            'total_score': int(final_score),
            'breakdown': breakdown
        }