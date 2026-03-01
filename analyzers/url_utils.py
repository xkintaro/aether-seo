from urllib.parse import urlparse, urljoin

def normalize_url(url: str) -> str:
    url = url.strip()
    if url.startswith(('http://', 'https://')):
        return url
    is_local = url.startswith('localhost') or url.startswith('127.0.0.1')
    protocol = 'http' if is_local else 'https'
    return f"{protocol}://{url}"

def strip_protocol(url: str) -> str:
    clean = url.strip()
    clean = clean.replace('https://', '').replace('http://', '')
    return clean.rstrip('/')

def build_full_url(domain: str) -> str:
    is_local = domain.startswith('localhost') or domain.startswith('127.0.0.1')
    protocol = 'http' if is_local else 'https'
    return f'{protocol}://{domain}'

def get_base_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def is_internal_link(url: str, domain: str) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            return True
        site_domain = domain.lower().replace('www.', '')
        link_domain = parsed.netloc.lower().replace('www.', '')
        return site_domain == link_domain
    except Exception:
        return False