


from bs4 import BeautifulSoup


def replace_hrs(soup: BeautifulSoup):
    """
    Replace <hr/>s in the document with less visually intrusive breaks
    """
    
    for hr in soup.find_all("hr"):
        divider_alt = soup.new_tag("p")
        divider_alt.string = "　─────"
        hr.replace_with(divider_alt) 
        
    return soup