

from bs4 import BeautifulSoup
import regex

def _starts_with_alphanumeric_or_japanese_char(text: str):
    
    if not text:
        return False
    first_char = text[0]
    
    # Test against unicode scripts
    # Hira/kata/han for ja
    # Latin for en
    # 0-9 for numerics - avoid testing symbols since those are more likely to be dividers handled separately in indent_separators()
    pattern = r'^[\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Han}\p{Script=Latin}\p0-9]$'
    return bool(regex.match(pattern, first_char))


def indent_text(soup: BeautifulSoup):
    """
    Auto indent lines which begin with either a ja or en character with one fullwidth space
    """
    for p_tag in soup.find_all("p", recursive=False):
        line_text = p_tag.get_text(strip=False)
        if _starts_with_alphanumeric_or_japanese_char(line_text):
            p_tag.insert(0, "　")
    
    #return soup
    # Parameter soup should be modified in place