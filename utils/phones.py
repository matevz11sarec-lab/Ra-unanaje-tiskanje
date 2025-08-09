import re
from typing import Optional
from playwright.sync_api import Page

# Slovenian phone number regex covering +386 and 0xx with spaces or dashes
PHONE_REGEX = re.compile(r'(?:\+386\s?\d{1,2}[\s\-]?\d{3}[\s\-]?\d{3,4}|0\d{1,2}[\s\-]?\d{3}[\s\-]?\d{3,4})')


def normalize_phone_number(raw_phone: str) -> str:
    """Normalize phone number by trimming and collapsing whitespace.

    Dashes and other separators are preserved; only excess spaces are removed.
    """
    if not raw_phone:
        return ''
    # Replace non-breaking spaces and collapse multiple spaces
    cleaned = raw_phone.replace('\xa0', ' ').strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned


def extract_phone_from_text(text: str) -> Optional[str]:
    """Extract a phone number from free text using PHONE_REGEX.

    Returns the first match found, normalized. If none found, returns None.
    """
    if not text:
        return None
    match = PHONE_REGEX.search(text)
    if match:
        return normalize_phone_number(match.group(0))
    return None


def extract_phone_from_tel_href(href: str) -> Optional[str]:
    """Extract phone number from a tel: href value.

    Returns the number portion as-is (minus the leading tel:) and normalized for spaces.
    """
    if not href:
        return None
    if href.lower().startswith('tel:'):
        number_part = href.split(':', 1)[1]
        # Some sites include spaces or formatting in tel: value; normalize spaces only
        return normalize_phone_number(number_part)
    return None


def find_phone_on_page(page: Page) -> Optional[str]:
    """Find a phone number on the current page.

    Strategy:
    1) Prefer an <a href="tel:"> link if present.
    2) Otherwise, search the visible body text with regex.
    """
    try:
        tel_link = page.locator('a[href^="tel:"]').first
        if tel_link.count() > 0:
            try:
                # Try the visible text first (often better formatted)
                link_text = tel_link.inner_text(timeout=2000).strip()
            except Exception:
                link_text = ''
            if link_text:
                extracted_from_text = extract_phone_from_text(link_text)
                if extracted_from_text:
                    return extracted_from_text
            # Fallback to href attribute
            href_val = tel_link.get_attribute('href')
            phone_from_href = extract_phone_from_tel_href(href_val or '')
            if phone_from_href:
                return phone_from_href
    except Exception:
        # Ignore and move to regex search
        pass

    # Regex search across the body text as a robust fallback
    try:
        body_text = page.locator('body').inner_text(timeout=3000)
        return extract_phone_from_text(body_text)
    except Exception:
        return None