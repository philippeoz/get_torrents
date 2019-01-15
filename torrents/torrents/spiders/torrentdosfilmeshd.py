import scrapy
import re
import logging

from bs4 import BeautifulSoup
from torrents.pipelines import driver as DRIVER


class TorrentSpider(scrapy.Spider):
    name = "torrentdosfilmeshd"
    start_urls = [
        'https://www.torrentdosfilmeshd.net/'
    ]

    def parse(self, response):
        for href in response.css('.title a::attr(href)').extract():
            yield response.follow(href, callback=self.parse_torrent_page)

        next_page_number = response.css('.page.larger::text').extract_first()
        next_page = response.css('.page.larger::attr(href)').extract_first()
        if next_page_number.isdigit() and next_page is not None:
            yield response.follow(next_page, self.parse)

    def parse_torrent_page(self, response):
        def extract_with_css(query):
            result = response.css(query).extract_first()
            return result.strip() if result else ''

        content = self.parse_content(response.css('.content').pop())
        categories = response.css('.tags a::text').extract()
        title = extract_with_css('.title h1 a::text')

        if categories:
            categories = ', '.join(categories).upper()

        if 'magnet_urls' not in content.keys():
            logging.info(f'MAGNETLINK NOT FOUND - {title}')
            return

        yield {
            'title': title,
            'date_upload': extract_with_css('.date::text'),
            'categories': categories,
            **content
        }

    def parse_content(self, content):
        data = {}
        cover_image = content.css('img.alignleft::attr(src)').extract_first()
        if cover_image:
            data['cover_image'] = cover_image

        content_soup = BeautifulSoup(content.get(), 'html.parser')
        for p in content_soup.find_all('p'):
            if 'INFORMAÇÕES' in p.text:
                data['informations'] = p.text
            elif 'SINOPSE' in p.text:
                data['synopsis'] = p.text

        magnet_urls = content.css('a[href*=masterads]::attr(href)').extract()
        if magnet_urls:
            data['magnet_urls'] = self.get_magnet_link(magnet_urls)
        return data

    def get_magnet_link(self, urls):
        if not isinstance(urls, list):
            urls = [urls]
        magnet_urls = []

        for url in urls:
            DRIVER.get(url)
            button = DRIVER.find_element_by_css_selector('a[href*=magnet]')
            if button:
                magnet_urls.append(button.get_attribute('href'))

        return magnet_urls
