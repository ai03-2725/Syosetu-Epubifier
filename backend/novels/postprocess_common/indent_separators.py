from bs4 import BeautifulSoup

from novels.postprocess_common.util import is_symbol_divider


def indent_separators(soup: BeautifulSoup):
    """
    Gives consistent indentation to symbol-only break separators to ensure that they don't sit too close to the edge of the screen on e-readers
    """
    
    for tag in soup.find_all(recursive=False):
        if is_symbol_divider(tag):
            divider_text = tag.get_text().strip()
            number_of_indents = max(5 - len(divider_text), 1) # 4 space indents for a single-char break, -1 for each additional length up to 1 min
            tag.string = "　" * number_of_indents + divider_text
    
    # return soup
    # Parameter soup should be modified in place