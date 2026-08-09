
import re
from bs4 import Tag

# - For "is_only_symbols", the following unicode ranges are checked
#   - 2000-206F: General Punctuation
#   - 2200-22FF: Mathematical Operators
#   - The entire 2500-27BF range
#     - 2500-257F: Box drawing
#     - 2580-259F: Block Elements
#     - 25A0-25FF: Geometric Shapes (seems to be the most common for dividers)
#     - 2600-26FF: Misc Symbols
#     - 2700-27BF: Dingbats
#  - Plus some common symbols that are hard to catch with a big unicode block
def is_only_divider_symbols(text: str):
    return bool(re.fullmatch(r"\d+|[\u2000-\u206F]+|[\u2200-\u22FF]+|[\u2500-\u27BF]+|[＊*＝=＃#－-＿_￣￭￮§]+", text))

def is_symbol_divider(tag: Tag):
    """
    Determines whether a bs4 Tag is a p comprised of only commonly used geometric symbols which are used for text dividers/separators
    """
    
    if tag is None:
        return False
    return tag.name == 'p' and is_only_divider_symbols(tag.get_text())

def is_hr_divider(tag: Tag):
    if tag is None:
        return False
    return tag.name == "hr"