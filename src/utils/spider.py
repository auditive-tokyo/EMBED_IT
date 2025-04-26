from scrapy.spiders import Spider, SitemapSpider
from bs4 import BeautifulSoup
from scrapy.http import TextResponse
from src.schema.items import MyItem
import json
import os
import re
from typing import List

class BaseSpider(Spider):
    def __init__(self, exclude_tags=None, exclude_elements=None, *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)
        self.exclude_tags = exclude_tags.split(',') if exclude_tags else []
        self.exclude_elements = exclude_elements.split(',') if exclude_elements else []
    
    def parse(self, response):
        # Check if the response is text-based
        if 'text' in response.headers['Content-Type'].decode():
            # Parse the response text with BeautifulSoup
            soup = BeautifulSoup(response.text, 'lxml')
            for tag in soup.find_all(self.exclude_tags):
                tag.decompose()

            # Remove unwanted elements
            for element in self.exclude_elements:
                unwanted_elements = soup.select(element)
                for unwanted_element in unwanted_elements:
                    unwanted_element.decompose()

            # Extract the title
            title = soup.find('meta', property='og:title')
            if title:
                title = title['content']
            else:
                title = soup.title.string if soup.title else 'No title'
                
            # Remove site_name from title if it exists in settings.json
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                    site_name = settings.get('scrape_url', {}).get('site_name', '')
                    if site_name and site_name in title:
                        title = title.replace(site_name, '').strip()
                        title = re.sub(r'\s*[-|]\s*$', '', title)

            # Convert the BeautifulSoup object back to a Scrapy Response
            response = TextResponse(url=response.url, body=str(soup), encoding='utf-8')
            
            return response, title
        else:
            print(f'Skipped non-text response: {response.url}\n')            

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
        if response is None and title is None:
            return
            
        # ...
            
        # Check if the user input is in XPath format
        if "[" in self.include_elements and "]" in self.include_elements and self.include_elements.startswith('//') and self.include_elements.endswith('//text()'):
            # If it's in complete XPath format, use it directly
            xpath_expr = self.include_elements
        else:
            # If it's not in complete XPath format, convert it to XPath format
            xpath_expr = ' | '.join(f'//{el.strip()}//text()' for el in self.include_elements.split(','))

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

        # Return the item
        return item

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
        if response is None and title is None:
            return

        # ...

        # Check if the user input is in XPath format
        if "[" in self.include_elements and "]" in self.include_elements and self.include_elements.startswith('//') and self.include_elements.endswith('//text()'):
            # If it's in complete XPath format, use it directly
            xpath_expr = self.include_elements
        else:
            # If it's not in complete XPath format, convert it to XPath format
            xpath_expr = ' | '.join(f'//{el.strip()}//text()' for el in self.include_elements.split(','))

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

        # Return the item
        return item
