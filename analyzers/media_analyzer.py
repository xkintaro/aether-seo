from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import struct
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import (
    RECOMMENDED_IMAGE_FORMATS, LEGACY_IMAGE_FORMATS,
    RECOMMENDED_VIDEO_FORMATS, LEGACY_VIDEO_FORMATS,
    LAZY_LOAD_THRESHOLD_PX,
    REQUEST_TIMEOUT, REQUEST_HEADERS,
    ECO_MODE, ECO_DELAY, ECO_MAX_WORKERS, MAX_CONCURRENT_REQUESTS,
    MAX_MEDIA_WORKERS, MAX_IMAGES_TO_CHECK, FAVICON_TIMEOUT,
    MEDIA_HEAD_TIMEOUT
)
import time
from .utils import create_session
class MediaAnalyzer:
    def __init__(self, soup: BeautifulSoup, base_url: str, session=None, cached_elements=None):
        self.soup = soup
        self.base_url = base_url
        self.session = session or create_session()
        self._cached_elements = cached_elements
    def analyze(self) -> dict:
        images = self._analyze_images()
        videos = self._analyze_videos()
        favicon = self._analyze_favicon()
        return {
            'images': images,
            'videos': videos,
            'favicon': favicon,
            'summary': self._generate_summary(images, videos, favicon)
        }
    def _analyze_images(self) -> dict:
        images = []
        img_tags = self._cached_elements.images if self._cached_elements else self.soup.find_all('img')
        issues = {
            'missing_alt': 0,
            'empty_alt': 0,
            'legacy_format': 0,
            'needs_lazy_load': 0,
            'has_lazy_load': 0
        }
        effective_index = 0
        for idx, img in enumerate(img_tags):
            src = img.get('src', '') or img.get('data-src', '')
            src_full = urljoin(self.base_url, src) if src else None
            alt = img.get('alt')
            alt_status = self._get_alt_status(alt)
            if alt_status == 'missing':
                issues['missing_alt'] += 1
            elif alt_status == 'empty':
                issues['empty_alt'] += 1
            format_info = self._get_format_info(src, 'image')
            if format_info['is_legacy']:
                issues['legacy_format'] += 1
            classes = img.get('class', [])
            if isinstance(classes, str):
                classes = classes.split()
            classes_str = ' '.join(classes).lower()
            is_icon = self._is_small_icon(img, classes_str)
            is_header = self._is_in_header_or_nav(img)
            is_logo = self._is_likely_logo(img, classes_str)
            lazy_load_info = self._analyze_lazy_load(img, effective_index, is_icon, is_header, is_logo, classes_str)
            if lazy_load_info['needs_lazy']:
                issues['needs_lazy_load'] += 1
            if lazy_load_info['has_lazy']:
                issues['has_lazy_load'] += 1
            if not is_icon and not is_header and not is_logo:
                effective_index += 1
            images.append({
                'index': idx,
                'src': src,
                'src_full': src_full,
                'alt': alt,
                'alt_status': alt_status,
                'alt_text': alt if alt else '',
                'format': format_info['format'],
                'is_legacy_format': format_info['is_legacy'],
                'format_recommendation': format_info['recommendation'],
                'lazy_load': lazy_load_info,
                'width': img.get('width'),
                'height': img.get('height'),
                'has_dimensions': bool(img.get('width') and img.get('height')),
                'classes': img.get('class', []),
                'status_code': None,
                'size_bytes': None,
                'size_kb': None,
                'size_formatted': None
            })
        self._batch_fetch_media_info(images)
        images.sort(key=lambda x: (
            x['alt_status'] != 'missing',
            x['alt_status'] != 'empty',
            x['is_legacy_format'] != True,
            not (x['lazy_load']['needs_lazy'] and not x['lazy_load']['has_lazy'])
        ))
        return {
            'total': len(images),
            'data': images,
            'issues': issues,
            'status': 'error' if issues['missing_alt'] > 0 else
                     ('warning' if issues['empty_alt'] > 0 or issues['legacy_format'] > 0 else 'success')
        }
    def _analyze_videos(self) -> dict:
        videos = []
        video_tags = self._cached_elements.videos if self._cached_elements else self.soup.find_all('video')
        iframe_tags = self._cached_elements.iframes if self._cached_elements else self.soup.find_all('iframe')
        embed_tags = self._cached_elements.embed_tags if self._cached_elements else self.soup.find_all('embed')
        object_tags = self._cached_elements.object_tags if self._cached_elements else self.soup.find_all('object')
        issues = {
            'legacy_format': 0,
            'needs_lazy_load': 0,
            'has_lazy_load': 0,
            'missing_poster': 0
        }
        effective_index = 0
        for idx, video in enumerate(video_tags):
            src = video.get('src', '')
            poster = video.get('poster', '')
            source_tags = video.find_all('source')
            sources = []
            for source in source_tags:
                source_src = source.get('src', '')
                try:
                    format_info = self._get_format_info(source_src, 'video')
                except Exception:
                    format_info = {'format': 'unknown', 'is_legacy': False}
                sources.append({
                    'src': source_src,
                    'type': source.get('type', ''),
                    'format': format_info['format'],
                    'is_legacy': format_info['is_legacy']
                })
            if not src and sources:
                src = sources[0]['src']
            src_full = urljoin(self.base_url, src) if src else self.base_url
            format_info = self._get_format_info(src, 'video') if src else {'format': None, 'is_legacy': False, 'recommendation': None}
            has_legacy = format_info.get('is_legacy', False) or any(s.get('is_legacy', False) for s in sources)
            if has_legacy:
                issues['legacy_format'] += 1
            if not poster:
                issues['missing_poster'] += 1
            classes = video.get('class', [])
            if isinstance(classes, str):
                classes = classes.split()
            classes_str = ' '.join(classes).lower()
            is_header = self._is_in_header_or_nav(video)
            lazy_load_info = self._analyze_lazy_load(video, effective_index, is_icon=False, is_header=is_header, is_logo=False, classes_str=classes_str)
            if lazy_load_info['needs_lazy']:
                issues['needs_lazy_load'] += 1
            if lazy_load_info['has_lazy']:
                issues['has_lazy_load'] += 1
            if not is_header:
                effective_index += 1
            videos.append({
                'index': idx,
                'type': 'html5',
                'src': src_full if src else 'Video source not found',
                'src_full': src_full if src else None,
                'sources': sources,
                'poster': poster,
                'has_poster': bool(poster),
                'format': format_info.get('format', 'unknown') if src else 'unknown',
                'is_legacy_format': has_legacy,
                'lazy_load': lazy_load_info,
                'autoplay': video.has_attr('autoplay'),
                'muted': video.has_attr('muted'),
                'loop': video.has_attr('loop'),
                'controls': video.has_attr('controls'),
                'status_code': None,
                'size_bytes': None,
                'size_kb': None,
                'size_formatted': None
            })
        start_idx = len(video_tags)
        embedded_tags = iframe_tags + embed_tags + object_tags
        video_providers = ['youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com', 'twitch.tv']
        for i, tag in enumerate(embedded_tags):
            src = tag.get('src', '') or tag.get('data', '')
            if not src:
                continue
            is_video_provider = any(provider in src for provider in video_providers)
            if is_video_provider:
                classes = tag.get('class', [])
                if isinstance(classes, str):
                    classes = classes.split()
                classes_str = ' '.join(classes).lower()
                is_header = self._is_in_header_or_nav(tag)
                lazy_load_info = self._analyze_lazy_load(tag, effective_index, is_icon=False, is_header=is_header, is_logo=False, classes_str=classes_str)
                if lazy_load_info['needs_lazy']:
                    issues['needs_lazy_load'] += 1
                if lazy_load_info['has_lazy']:
                    issues['has_lazy_load'] += 1
                if not is_header:
                    effective_index += 1
                videos.append({
                    'index': start_idx + i,
                    'type': 'embed',
                    'src': src,
                    'src_full': src,
                    'format': 'embed',
                    'is_legacy_format': False,
                    'lazy_load': lazy_load_info,
                    'width': tag.get('width'),
                    'height': tag.get('height'),
                    'title': tag.get('title'),
                    'autoplay': False,
                    'muted': False,
                    'loop': False,
                    'controls': False,
                    'status_code': 200,
                    'size_bytes': 0,
                    'size_kb': 0,
                    'size_formatted': 'External'
                })
        html5_videos = [v for v in videos if v['type'] == 'html5' and v.get('src_full')]
        if html5_videos:
            self._batch_fetch_media_info(html5_videos)
        videos.sort(key=lambda x: (
            not x.get('missing_poster', False),
            not x.get('is_legacy_format', False)
        ))
        return {
            'total': len(videos),
            'data': videos,
            'issues': issues,
            'status': 'error' if issues['missing_poster'] > 0 else
                     ('warning' if issues['legacy_format'] > 0 else 'success')
        }
    def _analyze_favicon(self) -> dict:
        favicon_selectors = [
            {'rel': 'icon'},
            {'rel': 'shortcut icon'},
            {'rel': 'apple-touch-icon'},
            {'rel': 'apple-touch-icon-precomposed'}
        ]
        favicons = []
        for selector in favicon_selectors:
            links = self.soup.find_all('link', attrs=selector)
            for link in links:
                href = link.get('href', '')
                if href:
                    favicons.append({
                        'href': href,
                        'href_full': urljoin(self.base_url, href),
                        'rel': link.get('rel', []),
                        'type': link.get('type', ''),
                        'sizes': link.get('sizes', '')
                    })
        best_favicon = None
        if favicons:
            processed_favicons = []
            for fav in favicons:
                width, height = self._get_favicon_size(fav)
                fav['width'] = width
                fav['height'] = height
                is_sufficient = False
                if width and height:
                     is_sufficient = (width % 48 == 0) and (width == height)
                fav['is_sufficient'] = is_sufficient
                processed_favicons.append(fav)
            best_favicon = max(processed_favicons, key=lambda x: (x.get('width') or 0))
            warnings = []
            is_absolute = best_favicon.get('href', '').startswith(('http://', 'https://'))
            if not is_absolute:
                warnings.append('Absolute URL is not used (e.g. https://...).')
            if best_favicon.get('width'):
                width = best_favicon['width']
                height = best_favicon['height']
                if width != height:
                     warnings.append(f'Not square ({width}x{height}), should be 1:1.')
                if width < 48 or width % 48 != 0:
                    warnings.append(f'Dimensions ({width}x{height}) are not multiples of 48px.')
            else:
                warnings.append('Dimensions could not be determined.')
            if warnings:
                return {
                    'exists': True,
                    'data': processed_favicons,
                    'primary': best_favicon,
                    'status': 'warning',
                    'message': ' | '.join(warnings)
                }
            return {
                'exists': True,
                'data': processed_favicons,
                'primary': best_favicon,
                'status': 'success',
                'message': f'Favicon dimensions ({width}x{height}px) and structure are excellent.'
            }
        return {
            'exists': False,
            'data': [],
            'primary': None,
            'status': 'error',
            'message': 'Favicon definition not found'
        }
    def _get_alt_status(self, alt) -> str:
        if alt is None:
            return 'missing'
        elif alt.strip() == '':
            return 'empty'
        return 'valid'
    def _get_format_info(self, src: str, media_type: str) -> dict:
        if not src:
            return {
                'format': None,
                'is_legacy': False,
                'recommendation': None
            }
        path = src.split('?')[0].split('#')[0].lower()
        if '.' in path:
            ext = path.rsplit('.', 1)[-1]
        else:
            return {
                'format': 'unknown',
                'is_legacy': False,
                'recommendation': None
            }
        if media_type == 'image':
            if ext in RECOMMENDED_IMAGE_FORMATS:
                return {
                    'format': ext,
                    'is_legacy': False,
                    'recommendation': None
                }
            elif ext in LEGACY_IMAGE_FORMATS:
                return {
                    'format': ext,
                    'is_legacy': True,
                    'recommendation': 'Convert to WebP or AVIF format'
                }
        elif media_type == 'video':
            if ext in RECOMMENDED_VIDEO_FORMATS:
                return {
                    'format': ext,
                    'is_legacy': False,
                    'recommendation': None
                }
            elif ext in LEGACY_VIDEO_FORMATS:
                return {
                    'format': ext,
                    'is_legacy': True,
                    'recommendation': 'Convert to WebM format'
                }
        return {
            'format': ext,
            'is_legacy': False,
            'recommendation': None
        }

    def _analyze_lazy_load(self, element, index: int, is_icon: bool, is_header: bool, is_logo: bool, classes_str: str) -> dict:
        loading_attr = element.get('loading', '').lower()
        has_lazy_attr = loading_attr == 'lazy'
        has_eager_attr = loading_attr == 'eager'
        has_data_src = bool(element.get('data-src'))
        lazy_classes = ['lazy', 'lazyload', 'lazy-load', 'lozad', 'b-lazy']
        has_lazy_class = any(lc in classes_str for lc in lazy_classes)
        is_lazy_implemented = has_lazy_attr or has_data_src or has_lazy_class
        is_hero_structure = self._is_hero_element(element, classes_str)
        is_hero = is_hero_structure and index < 3
        is_lcp_candidate = (index < 2)
        is_likely_above_fold = (
            is_lcp_candidate or
            is_hero or
            is_header or
            is_logo
        )
        needs_lazy = False
        recommendation = ""
        status = "success"
        if is_likely_above_fold:
            needs_lazy = False
            if has_lazy_attr:
                recommendation = "Found above-the-fold. 'loading=lazy' usage may increase LCP time, it is recommended to remove it or use 'eager'."
                status = "warning"
            else:
                recommendation = "At the top of the screen (LCP candidate, Logo, or Hero). Lazy load not required."
                status = "success"
        elif is_icon:
            needs_lazy = False
            recommendation = "Detected as a small icon/decorative image. Lazy load is not mandatory."
            status = "success"
        else:
            needs_lazy = True
            if is_lazy_implemented:
                recommendation = "Lazy load successfully implemented."
                status = "success"
            else:
                recommendation = "You should use lazy-load (loading='lazy') for this image below the fold for performance improvement."
                status = "warning"
        return {
            'has_lazy': is_lazy_implemented,
            'needs_lazy': needs_lazy,
            'loading_attr': loading_attr,
            'is_above_fold': is_likely_above_fold,
            'is_logo': is_logo,
            'is_icon': is_icon,
            'is_hero': is_hero,
            'recommendation': recommendation,
            'status': status
        }
    def _is_likely_logo(self, element, classes_str: str) -> bool:
        alt = (element.get('alt') or '').lower()
        if 'logo' in alt or 'brand' in alt:
            return True
        img_id = (element.get('id') or '').lower()
        if 'logo' in classes_str or 'brand' in classes_str:
            return True
        if 'logo' in img_id or 'brand' in img_id:
            return True
        src = (element.get('src') or element.get('data-src') or '').lower()
        if 'logo' in src:
            return True
        parent = element.parent
        if parent and parent.name == 'a':
            href = parent.get('href', '')
            if href in ['/', 'index.html', '#', 'index.php']:
                return True
        return False
    def _fetch_media_info(self, url: str) -> dict:
        info = {'status_code': None, 'size_bytes': None, 'size_kb': None, 'size_formatted': None}
        try:
            response = self.session.head(url, timeout=MEDIA_HEAD_TIMEOUT, allow_redirects=True)
            info['status_code'] = response.status_code
            content_length = response.headers.get('Content-Length')
            if content_length:
                size_bytes = int(content_length)
                info['size_bytes'] = size_bytes
                info['size_kb'] = round(size_bytes / 1024, 2)
                info['size_formatted'] = f"{info['size_kb']} KB"
        except Exception:
            pass
        return info

    def _is_small_icon(self, element, classes_str: str = '') -> bool:
        large_indicators = ['w-100', 'w-75', 'w-50', 'w-auto', 'img-fluid', 'cover', 'hero', 'banner']
        if any(ind in classes_str for ind in large_indicators):
            return False
        try:
            width = element.get('width')
            height = element.get('height')
            if width: width = int(''.join(filter(str.isdigit, str(width))))
            if height: height = int(''.join(filter(str.isdigit, str(height))))
            if width and height:
                if width > 50 or height > 50:
                    return False
                return True
        except Exception:
            pass
        src = (element.get('src') or '').lower()
        if 'icon' in src or 'logo' in src:
            return True
        if src.endswith('.svg'):
            if 'icon' in classes_str:
                return True
            return False
        return False
    def _is_hero_element(self, element, classes_str: str) -> bool:
        hero_keywords = ['hero', 'banner', 'slider', 'carousel', 'jumbotron', 'masthead', 'intro', 'featured']
        if any(k in classes_str for k in hero_keywords):
            return True
        current = element.parent
        for _ in range(4):
            if not current or not hasattr(current, 'get'):
                break
            p_classes = current.get('class', [])
            if isinstance(p_classes, list):
                p_classes = ' '.join(p_classes).lower()
            elif isinstance(p_classes, str):
                p_classes = p_classes.lower()
            else:
                p_classes = ""
            p_id = (current.get('id') or '').lower()
            if any(k in p_classes for k in hero_keywords) or any(k in p_id for k in hero_keywords):
                return True
            current = current.parent
        return False
    def _is_in_header_or_nav(self, element) -> bool:
        return element.find_parent(['header', 'nav']) is not None

    def _generate_summary(self, images: dict, videos: dict, favicon: dict) -> dict:
        total_issues = (
            images['issues']['missing_alt'] +
            images['issues']['empty_alt'] +
            images['issues']['legacy_format'] +
            videos['issues']['legacy_format'] +
            videos['issues']['missing_poster']
        )
        total_image_size = sum(img.get('size_bytes', 0) or 0 for img in images['data'])
        total_video_size = sum(vid.get('size_bytes', 0) or 0 for vid in videos['data'])
        if images['issues']['missing_alt'] > 0:
            status = 'error'
        elif total_issues > 0:
            status = 'warning'
        else:
            status = 'success'
        return {
            'total_images': images['total'],
            'total_videos': videos['total'],
            'has_favicon': favicon['exists'],
            'total_issues': total_issues,
            'total_size_bytes': total_image_size + total_video_size,
            'status': status
        }
    def _batch_fetch_media_info(self, items: list) -> None:
        targets = [(i, item) for i, item in enumerate(items) if item.get('src_full')]
        if not targets:
            return
        targets = targets[:MAX_IMAGES_TO_CHECK]

        def fetch_single(entry):
            idx, item = entry
            info = self._fetch_media_info(item['src_full'])
            return idx, info

        max_workers = ECO_MAX_WORKERS if ECO_MODE else min(MAX_CONCURRENT_REQUESTS, MAX_MEDIA_WORKERS)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_single, entry): entry for entry in targets}
            for future in as_completed(futures):
                idx, info = future.result()
                items[idx].update(info)
    def _get_favicon_size(self, favicon_data: dict) -> tuple:
        sizes = favicon_data.get('sizes', '')
        if sizes and sizes != 'any':
            try:
                parts = sizes.split()
                max_w = 0
                max_h = 0
                for part in parts:
                    if 'x' in part:
                        w, h = map(int, part.lower().split('x'))
                        if w > max_w:
                            max_w = w
                            max_h = h
                if max_w > 0:
                    return max_w, max_h
            except Exception:
                pass
        try:
            url = favicon_data['href_full']
            response = self.session.get(url, stream=True, timeout=FAVICON_TIMEOUT)
            content = response.raw.read(4096)
            response.close()
            if not content:
                return 0, 0
            if content.startswith(b'\x89PNG\r\n\x1a\n'):
                w, h = struct.unpack('>LL', content[16:24])
                return int(w), int(h)
            if content.startswith(b'\x00\x00\x01\x00'):
                count = struct.unpack('<H', content[4:6])[0]
                max_w = 0
                max_h = 0
                offset = 6
                for _ in range(count):
                    w = content[offset]
                    h = content[offset+1]
                    if w == 0: w = 256
                    if h == 0: h = 256
                    if w > max_w:
                        max_w = w
                        max_h = h
                    offset += 16
                return max_w, max_h
            if content.startswith(b'GIF87a') or content.startswith(b'GIF89a'):
                w, h = struct.unpack('<HH', content[6:10])
                return int(w), int(h)
        except Exception:
            pass
        return 0, 0