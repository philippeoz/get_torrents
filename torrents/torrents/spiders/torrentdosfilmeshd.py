import scrapy
import re
import logging

from bs4 import BeautifulSoup
from torrents.pipelines import driver as DRIVER

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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

        title = extract_with_css('.title h1 a::text')
        content = self.parse_content(response.css('.content').pop(), title)
        categories = response.css('.tags a::text').extract()

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

    def parse_content(self, content, title):
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

        magnet_pre_urls = content.css(
            'a[href*=masterads]::attr(href)').extract()
        if magnet_pre_urls:
            magnet_urls = self.get_magnet_link(magnet_pre_urls, title)
            if magnet_urls:
                data['magnet_urls'] = magnet_urls
        return data

    def get_magnet_link(self, urls, title):
        if not isinstance(urls, list):
            urls = [urls]
        magnet_urls = []
        for url in urls:
            done = False
            while not done:
                try:
                    DRIVER.get(url)
                    wait = WebDriverWait(DRIVER, 10)
                    button = wait.until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, 'a[href*=magnet]')
                        )
                    )
                    if button and button.get_attribute('href'):
                        magnet_urls.append(button.get_attribute('href'))
                        done = True
                except Exception as err:
                    logging.info(
                        f'MAGNETLINK NOT FOUND ON {title} - TRYING AGAIN')
        return magnet_urls
