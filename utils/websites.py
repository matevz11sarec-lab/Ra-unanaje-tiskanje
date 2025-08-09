from typing import Optional
from urllib.parse import urlparse
from playwright.sync_api import Page

SOCIAL_DOMAINS = {
    'facebook.com', 'instagram.com', 'linkedin.com', 'x.com', 'twitter.com',
    'youtube.com', 'tiktok.com'
}

EXCLUDE_HOSTS = {
    'bizi.si', 'www.bizi.si',
    'companywall.si', 'www.companywall.si',
    'google.com', 'www.google.com', 'maps.google.com', 'goo.gl',
}


def _is_external_company_site(url: str) -> bool:
    if not url or url.startswith(('mailto:', 'tel:', 'javascript:')):
        return False
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    host = (parsed.netloc or '').lower()
    if not host:
        return False
    if host in EXCLUDE_HOSTS:
        return False
    # Filter obvious social/media platforms
    for sd in SOCIAL_DOMAINS:
        if host.endswith(sd):
            return False
    return parsed.scheme in ('http', 'https')


def find_website_on_page(page: Page) -> Optional[str]:
    """Return the first external website URL likely belonging to the company.

    Scans all anchor tags and picks the first http(s) URL that is not an internal host,
    not mailto/tel/javascript, and not a common social/map domain.
    """
    try:
        links = page.locator('a[href]')
        count = links.count()
        for i in range(min(count, 150)):
            href = links.nth(i).get_attribute('href') or ''
            if _is_external_company_site(href):
                return href
    except Exception:
        pass
    return None