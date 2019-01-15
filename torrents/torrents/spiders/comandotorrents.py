import scrapy
import re

from bs4 import BeautifulSoup


class TorrentSpider(scrapy.Spider):
    name = "comandotorrents"
    start_urls = [
        'https://www.comandotorrents.com/'
    ]

    def parse(self, response):
        for href in response.css('.entry-title a::attr(href)').extract():
            yield response.follow(href, callback=self.parse_torrent_page)

        for href in response.css('.nextpostslink::attr(href)'):
            yield response.follow(href, self.parse)
    
    def parse_torrent_page(self, response):
        def extract_with_css(query):
            result = response.css(query).extract_first()
            return result.strip() if result else ''

        content = self.parse_content(response.css('.entry-content.cf').pop())
        categories = response.css('.entry-categories a::text').extract()

        if categories:
            categories = ', '.join(categories).upper()

        if not 'magnet_urls' in content.keys():
            return

        yield {
            'title': extract_with_css('.entry-header.cf .entry-title a::text'),
            'date_upload': extract_with_css('.entry-date a::text'),
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

        magnet_urls = content.css(
            '[href*=magnet]::attr(href)'
        ).extract()
        if magnet_urls:
            data['magnet_urls'] = magnet_urls
        return data
