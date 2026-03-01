import os
from typing import Final, FrozenSet, Dict
REQUEST_TIMEOUT: Final[int] = 10
REQUEST_HEADERS: Final[Dict[str, str]] = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}
MAX_CONCURRENT_REQUESTS: Final[int] = 20
META_TITLE_MIN: Final[int] = 30
META_TITLE_MAX: Final[int] = 60
META_DESCRIPTION_MIN: Final[int] = 120
META_DESCRIPTION_MAX: Final[int] = 160
CSS_SIZE_WARNING_KB: Final[int] = 50
JS_SIZE_WARNING_KB: Final[int] = 50
LAZY_LOAD_THRESHOLD_PX: Final[int] = 800
RECOMMENDED_IMAGE_FORMATS: Final[FrozenSet[str]] = frozenset({'webp', 'avif', 'svg'})
LEGACY_IMAGE_FORMATS: Final[FrozenSet[str]] = frozenset({'jpg', 'jpeg', 'png', 'gif', 'bmp'})
RECOMMENDED_VIDEO_FORMATS: Final[FrozenSet[str]] = frozenset({'webm', 'mp4'})
LEGACY_VIDEO_FORMATS: Final[FrozenSet[str]] = frozenset({'avi', 'mov', 'wmv', 'flv'})
SSL_WARNING_DAYS: Final[int] = 30
MAX_SITEMAP_CHECK: Final[int] = 50
CACHE_MAXSIZE: Final[int] = 50
CACHE_TTL: Final[int] = 300
PARALLEL_ANALYZER_WORKERS: Final[int] = 6
CONNECTION_POOL_SIZE: Final[int] = 20
MAX_MEDIA_WORKERS: Final[int] = 10
MAX_LINKS_TO_CHECK: Final[int] = 100
MAX_IMAGES_TO_CHECK: Final[int] = 80
MAX_ASSETS_TO_CHECK: Final[int] = 50
FAVICON_TIMEOUT: Final[int] = 1
MEDIA_HEAD_TIMEOUT: Final[int] = 5
HEAD_FALLBACK_CODES: Final[FrozenSet[int]] = frozenset({405, 403, 501})
LANDMARK_ROLES: Final[FrozenSet[str]] = frozenset({
    'banner', 'navigation', 'main', 'complementary',
    'contentinfo', 'search', 'form', 'region'
})
WIDGET_ROLES: Final[FrozenSet[str]] = frozenset({
    'button', 'checkbox', 'dialog', 'gridcell', 'link', 'menuitem',
    'menuitemcheckbox', 'menuitemradio', 'option', 'progressbar',
    'radio', 'scrollbar', 'searchbox', 'slider', 'spinbutton',
    'switch', 'tab', 'tabpanel', 'textbox', 'treeitem'
})
STRUCTURE_ROLES: Final[FrozenSet[str]] = frozenset({
    'article', 'cell', 'columnheader', 'definition', 'directory',
    'document', 'group', 'heading', 'img', 'list', 'listitem',
    'math', 'note', 'presentation', 'row', 'rowgroup', 'rowheader',
    'separator', 'table', 'term', 'toolbar', 'tooltip'
})
MUST_HAVE_ACCESSIBLE_NAME: Final[FrozenSet[str]] = frozenset({
    'button', 'a', 'input', 'select', 'textarea',
    'img', 'iframe', 'video', 'audio'
})
INTERACTIVE_ELEMENTS: Final[FrozenSet[str]] = frozenset({
    'button', 'a', 'input', 'select', 'textarea', 'details', 'summary'
})
ARIA_ATTRIBUTES: Final[FrozenSet[str]] = frozenset({
    'aria-label', 'aria-labelledby', 'aria-describedby', 'aria-hidden',
    'aria-live', 'aria-expanded', 'aria-selected', 'aria-checked',
    'aria-disabled', 'aria-required', 'aria-invalid', 'aria-haspopup',
    'aria-controls', 'aria-owns', 'aria-busy', 'aria-atomic',
    'aria-relevant', 'aria-current', 'aria-modal', 'aria-pressed',
    'aria-readonly', 'aria-sort', 'aria-valuemax', 'aria-valuemin',
    'aria-valuenow', 'aria-valuetext', 'aria-activedescendant',
    'aria-autocomplete', 'aria-colcount', 'aria-colindex', 'aria-colspan',
    'aria-rowcount', 'aria-rowindex', 'aria-rowspan', 'aria-level',
    'aria-multiline', 'aria-multiselectable', 'aria-orientation',
    'aria-placeholder', 'aria-posinset', 'aria-setsize',
    'aria-errormessage', 'aria-keyshortcuts', 'aria-roledescription'
})
ECO_MODE: Final[bool] = os.environ.get('ECO_MODE', 'true').lower() == 'true'
ECO_DELAY: Final[float] = 0.05
ECO_MAX_WORKERS: Final[int] = 2
ECO_CPU_LABEL: Final[str] = "5%"
APP_TITLE: Final[str] = "Aether SEO"
COPYRIGHT_TEXT: Final[str] = "Developed by Kintaro"
SOCIAL_GITHUB: Final[str] = "https://github.com/xkintaro/aether-seo"
SOCIAL_DISCORD: Final[str] = "https://discord.gg/NSQk27Zdkv"