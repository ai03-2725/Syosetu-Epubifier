
from bs4 import BeautifulSoup, Tag


def _process_maegaki_atogaki(soup: BeautifulSoup, root: Tag):
    """
    The maegaki and atogaki sections are simply text (+ brs) dumped into a div with no p wrapper
    Force loose text into p tags for consistency
    Wrap standalone spans and standalone brs in p tags for consistency as well
    """
    
    # Process children first
    for child in list(root.contents):
        if child.name in { None, "span", "br" }:
            wrapper = soup.new_tag('p')
            child.wrap(wrapper)
    # Once children have been formatted, remove the outer div to drop the rest of the items into the regular document flow 
    # i.e. no div groupings that could mess with rendering
    root.unwrap()
            


def cleanup_html(input: str):
    
    soup = BeautifulSoup(input, "html.parser")
    
    # Process raw HTML from syosetu.org
    
    # Handle unformatted maegaki/atogaki sections (if they exist)
    # maegaki_div = soup.find("div", id="maegaki")
    # atogaki_div = soup.find("div", id="atogaki")
    # if maegaki_div is not None:
    #     _process_maegaki_atogaki(soup, maegaki_div)
    # if atogaki_div is not None:
    #     _process_maegaki_atogaki(soup, atogaki_div)
    
    # Disabled for now since it messes with line formatting
    
    # syosetu.org adds an id="int" attribute to every single authored p element
    # Can use it to find the document p tags
    # Remove them by default since they're unnecessary
    for p_tag in soup.find_all('p'):
        id_attr = p_tag.attrs.get('id')
        if isinstance(id_attr, str) and id_attr.isdecimal():
            del p_tag['id']
    
    # return soup.prettify(formatter="minimal") # This breaks the subsequent soup calls for some reason - image tag lookups no longer work
    return str(soup)