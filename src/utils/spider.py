from scrapy.spiders import Spider, SitemapSpider
from bs4 import BeautifulSoup
from scrapy.http import TextResponse
from src.schema.items import MyItem
from src.config import SETTINGS_JSON
import json
import os
from typing import List

class BaseSpider(Spider):
    def __init__(self, exclude_tags=None, exclude_elements=None, *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)
        self.exclude_tags = exclude_tags.split(',') if exclude_tags else []
        self.exclude_elements = exclude_elements.split(',') if exclude_elements else []
    
    def _is_text_response(self, response):
        """Check if the response is text-based."""
        return 'text' in response.headers['Content-Type'].decode()

    def _clean_soup(self, soup):
        """Remove excluded tags and elements from soup."""
        for tag in soup.find_all(self.exclude_tags):
            tag.decompose()
        for element in self.exclude_elements:
            for unwanted_element in soup.select(element):
                unwanted_element.decompose()

    def _extract_title(self, soup):
        """Extract title from soup."""
        title = soup.find('meta', property='og:title')
        if title:
            return title['content']
        return soup.title.string if soup.title else 'No title'

    def _clean_title(self, title):
        """Remove site_name from title if it exists in settings."""
        if not os.path.exists(SETTINGS_JSON):
            return title
        
        with open(SETTINGS_JSON, 'r') as f:
            settings = json.load(f)
        
        site_name = settings.get('scrape_url', {}).get('site_name', '')
        if not site_name or site_name not in title:
            return title
        
        title = title.replace(site_name, '').strip()
        if title.endswith('-') or title.endswith('|'):
            title = title[:-1].rstrip()
        return title

    def parse(self, response):
        if not self._is_text_response(response):
            print(f'Skipped non-text response: {response.url}\n')
            return None, None

        soup = BeautifulSoup(response.text, 'lxml')
        self._clean_soup(soup)
        
        title = self._extract_title(soup)
        title = self._clean_title(title)
        
        response = TextResponse(url=response.url, body=str(soup), encoding='utf-8')
        return response, title

    def _extract_item(self, response, title, include_elements):
        """Common helper method to extract item from response."""
        if response is None and title is None:
            return None

        # Check if the user input is in XPath format
        if "[" in include_elements and "]" in include_elements and include_elements.startswith('//') and include_elements.endswith('//text()'):
            # If it's in complete XPath format, use it directly
            xpath_expr = include_elements
        else:
            # If it's not in complete XPath format, convert it to XPath format
            xpath_expr = ' | '.join(f'//{el.strip()}//text()' for el in include_elements.split(','))

        print(f"XPath expression in parse: {xpath_expr}")

        # Extract the text
        text = response.xpath(xpath_expr).getall()
        text = ' '.join(text)
        text = text.replace('\n', ' ')  # Remove newlines

        # Create an item and populate it with data
        item = MyItem()
        item['title'] = title
        item['url'] = response.url
        item['text'] = text

        return item

class MySpider(BaseSpider):
    name = 'myspider'
    start_urls: List[str] = []
    custom_settings = {
        'FEED_EXPORT_FIELDS': ['title', 'url', 'text'],
    }
    
    def __init__(self, include_elements=None, *args, **kwargs):
        super(MySpider, self).__init__(*args, **kwargs)
        self.include_elements = include_elements

    def parse(self, response):
        response, title = super().parse(response)
        return self._extract_item(response, title, self.include_elements)

class MySitemapSpider(SitemapSpider, BaseSpider):
    name = 'mysitemapsipder'
    sitemap_urls: List[str] = []
    custom_settings = {
        'FEED_EXPORT_FIELDS': ['title', 'url', 'text'],
    }

    def __init__(self, include_elements=None, exclude_tags=None, exclude_elements=None, *args, **kwargs):
        SitemapSpider.__init__(self, *args, **kwargs)
        BaseSpider.__init__(self, exclude_tags=exclude_tags, exclude_elements=exclude_elements)
        self.include_elements = include_elements

    def parse(self, response):
        response, title = super().parse(response)
        return self._extract_item(response, title, self.include_elements)
