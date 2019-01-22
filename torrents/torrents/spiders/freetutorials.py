import scrapy
import re

from bs4 import BeautifulSoup


class TorrentSpider(scrapy.Spider):
    name = "freetutorials"
    start_urls = [
        'https://www.freetutorials.eu/'
    ]

    def parse(self, response):
        courses_links = response.css(
            '.entry-title.post-title a::attr(href)').extract()
        for href in courses_links:
            yield response.follow(href, callback=self.parse_torrent_page)

        if '/page/' not in response.url:
            yield response.follow(f'{response.url}/page/2/', self.parse)
        else:
            for href in response.css('a.next.page-numbers::attr(href)'):
                yield response.follow(href, self.parse)

    def parse_torrent_page(self, response):
        def extract_with_css(query):
            result = response.css(query).extract_first()
            return result.strip() if result else ''

        content = self.parse_content(response.css('div.entry-content').pop())
        categories = response.css('a[rel=category tag]::text').extract_all()

        if 'magnet_urls' not in content.keys():
            return

        yield {
            'title': extract_with_css('h1.entry-title::text'),
            'date_upload': extract_with_css('span.posted::text'),
            'categories': categories,
            **content
        }

    def parse_content(self, content):
        data = {}
        cover_image = content.css(
            'img.aligncenter[src*=udemy-images]::attr(src)').extract_first()
        if cover_image:
            data['cover_image'] = cover_image

        content_soup = BeautifulSoup(content.get(), 'html.parser')
        data['informations'] = "Views:{}".format(
            content_soup.text.split('Views:')[1]
        ).replace(
            '(adsbygoogle = window.adsbygoogle || []).push({});', '').strip()
        # for p in content_soup.find_all('p'):
        #     if 'INFORMAÇÕES' in p.text:
        #         data['informations'] = p.text
        #     elif 'SINOPSE' in p.text:
        #         data['synopsis'] = p.text

        magnet_urls = content.css(
            '[href*=magnet]::attr(href)'
        ).extract()
        if magnet_urls:
            data['magnet_urls'] = magnet_urls
        return data
