from bs4 import BeautifulSoup
import budoux 

def budoux_parse_html(input_html: str):
    """
    Passes entire input through BudouX to add word wrap points
    """
    parser = budoux.load_default_japanese_parser()
    output_raw = parser.translate_html_string(input_html)
    # translate_html_string doesn't break nested HTML tags, but force-wraps the entire input in a <span>
    return output_raw.removeprefix('<span style="word-break: keep-all; overflow-wrap: anywhere;">').removesuffix('</span>').replace('\u200B', '<wbr>').replace('\u2060', '')

def add_budoux_wrap_class_to_all_p(input_html: str):
    """
    Adds the .bwr (budoux word wrap) CSS class to all p and span elements
    """
    soup = BeautifulSoup(input_html, "html.parser")
    p_elements = soup.find_all("p")
    for p_element in p_elements:
        if p_element.get("class"):
            p_element['class'].append("bwr")
        else:
            p_element['class'] = "bwr"
    span_elements = soup.find_all("span")
    for span_element in span_elements:
            if span_element.get("class"):
                span_element['class'].append("bwr")
            else:
                span_element['class'] = "bwr"
                
    return str(soup)
