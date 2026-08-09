


from bs4 import BeautifulSoup


def replace_hrs(text: str):
    """
    Replace <hr/>s in the document with less visually intrusive breaks
    """
    
    soup = BeautifulSoup(text, "html.parser")
    
    for hr in soup.find_all("hr"):
        divider_alt = soup.new_tag("p")
        divider_alt.string = "　　ーーー"
        hr.replace_with(divider_alt) 
        
    return str(soup)