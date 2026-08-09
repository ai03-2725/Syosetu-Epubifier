# Utility to remove empty lines for novels with way too many line breaks and empty lines
# Simulates something close to what AozoraEpub3 does but in a simpler manner
# On the flipside, this shouldn't be run if wanting to preserve the original novel formatting

# Note to self - AozoraEpub3 characteristics
# - By default removes empty lines
# - If there's multiple empty lines in succession, seems to keep some
#   - 1 blanks -> gets turned into 0
#   - 2 blanks -> gets turned into 1
#   - 3 blanks -> gets turned into 1
#   - 5 blanks -> gets turned into 2
#     - Based on this, likely does some sort of tiering - a quick fit for the above would be math.floor(consecutive_lines/2)
# - Does not seem to remove empty lines before or after "symbol-only" divider lines


import math
from bs4 import BeautifulSoup, Tag
from novels.postprocess_common.util import is_symbol_divider, is_hr_divider

def cleanup_empty_lines(text: str):
    soup = BeautifulSoup(text, "html.parser")
    
    current_group: list[Tag] = []
    
    for tag in soup.find_all(recursive=False):
        # Iterate over top-level tags
        if tag.name == 'p' and not tag.get_text().strip():
            # If element is a blank p, add it to the currently tracked list of consecutive blank ps
            current_group.append(tag)
            print(f"Found empty tag: {tag}")
        else:
            # If reached an element that isn't a blank p, check how many consecutive ones were found
            # If more than 0, process them
            if len(current_group) > 0:
                # Calculate number of blank lines to keep
                num_lines_to_keep = math.floor(len(current_group) / 2)
                # If the tag preceding the first emptyline or following the last emptyline (i.e. current tag iteration) is a text divider, keep at minimum one line
                element_preceding_blanks = current_group[0].find_previous_sibling()
                element_following_blanks = tag
                if is_symbol_divider(element_preceding_blanks) or is_symbol_divider(element_following_blanks) or is_hr_divider(element_preceding_blanks) or is_hr_divider(element_following_blanks):
                    num_lines_to_keep = max(1, num_lines_to_keep)
                    print(f"Found divider: {element_preceding_blanks} or {element_following_blanks}")
                # Using this value, remove unnecessary whitespaces
                for p in current_group[num_lines_to_keep:]:
                    p.decompose()
                # For the former, make sure the ps are fully empty to save space
                # for p in current_group[:num_lines_to_keep]:
                    # p.string = ""
                # Reset blanks list
                current_group = []
                
    return str(soup)