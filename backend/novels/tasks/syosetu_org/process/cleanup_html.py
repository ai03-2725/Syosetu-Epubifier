
from bs4 import BeautifulSoup

def cleanup_html(soup: BeautifulSoup):
    """
    Cleans up misc unnecessary HTML bits before conversion to text
    Should run after all other postprocessing
    """
    
    for p_tag in soup.find_all('p'):
        # syosetu.org adds an id="int" attribute to every single authored p element in the honbun section
        # Remove them since they're unnecessary
        id_attr = p_tag.attrs.get('id')
        if isinstance(id_attr, str) and id_attr.isdecimal():
            del p_tag['id']
        # Empty p tags (i.e. completely empty, not even whitespace within) don't render as newlines properly in KOReader
        # Fix by inserting spaces - fullwidth just to be safe
        if len(p_tag.get_text()) == 0:
            p_tag.string = "　"
    
    #return soup
    # Parameter soup should be modified in place