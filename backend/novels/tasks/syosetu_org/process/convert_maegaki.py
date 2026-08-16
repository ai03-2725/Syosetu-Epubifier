

from bs4 import BeautifulSoup, Tag


def _convert_individual_maegaki_atogaki_div(soup_div: Tag):
    # Argument soup_div should be the div tag for the maegaki or atogaki sections
    
    # By default syosetu.org formats the maegaki/atogaki sections differently from honbun which makes it difficult to apply consistent post-processing
    # Specifically the maegaki/atogaki are loose text with manual <br/> newlines whereas honbun is <p>-wrapped individual lines
    # Convert the maegaki/atogaki sections to individual-p format by converting it to raw text and processing that
    
    # Swap <hr> tags located at the beginning/end with inline dashes
    for hr in soup_div.find_all("hr"):
        divider_alt = soup_div.new_tag("p")
        divider_alt.string = "　──────────"
        hr.replace_with(divider_alt) 
    
    # Then replace all brs with newlines - using get_text with separator=\n collapses formatting due to joining multiple newlines together into one
    for br in soup_div.find_all("br"):
        br.replace_with("\n")
        
    # Finally able to conver this entire div into a multiline string while preserving formatting
    processed_text = soup_div.get_text()
    
    # Split into array of lines
    split_text = processed_text.splitlines()
    
    # Then process each line and add it to a new HTML element
    # Clear the original div contents beforehand
    soup_div.clear()
    
    for text_line in split_text:
        new_p = soup_div.new_tag("p")
        
        # If line is empty, append an empty p tag with a space inside to ensure proper rendering
        if not text_line.strip():
            new_p.string = "　"
            
        # Otherwise simply wrap the text
        else:
            new_p.string = text_line
        
        soup_div.append(new_p)
        
    # return soup_div
    # Parameter soup_div should be modified in place


def unwrap_maegaki_atogaki(soup: BeautifulSoup):
    """
    Converts any divs with maegaki/atogaki formatting to honbun format for consistent postprocessing
    """
    maegaki_div = soup.find("div", id="maegaki")
    atogaki_div = soup.find("div", id="atogaki")
    if maegaki_div is not None:
        _convert_individual_maegaki_atogaki_div(maegaki_div)
        maegaki_div.unwrap()
    if atogaki_div is not None:
        _convert_individual_maegaki_atogaki_div(atogaki_div)
        atogaki_div.unwrap()
    