from bs4 import BeautifulSoup

class ElementCache:
    def __init__(self, soup: BeautifulSoup):
        self.images = soup.find_all('img')
        self.links = soup.find_all('a', href=True)
        self.headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        self.videos = soup.find_all('video')
        self.audios = soup.find_all('audio')
        self.iframes = soup.find_all('iframe')
        self.svgs = soup.find_all('svg')
        self.buttons = soup.find_all('button')
        self.inputs = soup.find_all(['input', 'select', 'textarea'])
        self.forms = soup.find_all('form')
        self.tables = soup.find_all('table')
        self.scripts = soup.find_all('script')
        self.styles = soup.find_all('style')
        self.link_tags = soup.find_all('link')
        self.all_with_style = soup.find_all(attrs={'style': True})
        self.embed_tags = soup.find_all('embed')
        self.object_tags = soup.find_all('object')

    def as_dict(self) -> dict:
        return {
            'images': self.images,
            'links': self.links,
            'headings': self.headings,
            'videos': self.videos,
            'audios': self.audios,
            'iframes': self.iframes,
            'svgs': self.svgs,
            'buttons': self.buttons,
            'inputs': self.inputs,
            'forms': self.forms,
            'tables': self.tables,
        }
