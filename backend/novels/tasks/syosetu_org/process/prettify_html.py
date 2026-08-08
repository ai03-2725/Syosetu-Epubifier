from bs4 import BeautifulSoup


def prettify_html(input: str):
    
    soup = BeautifulSoup(input, "html.parser", preserve_whitespace_tags=["p", "span", "h1", "h2", "h3", "h4", "h5", "h6"])
    return soup.prettify()