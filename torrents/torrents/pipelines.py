# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import peewee
import logging

from .models import Torrent, MagnetLink, db

import os

from selenium import webdriver


OPTIONS = webdriver.ChromeOptions()
prefs = {
    'profile.managed_default_content_settings.images': 2,
    'disk-cache-size': 4096
}
OPTIONS.add_experimental_option("prefs", prefs)
OPTIONS.add_argument('headless')
OPTIONS.add_argument('window-size=1200x600')

driver_path = os.path.join(os.path.dirname(__file__), 'chromedriver')
driver = webdriver.Chrome(
    executable_path=driver_path, chrome_options=OPTIONS)
driver.implicitly_wait(3)


class TorrentsPipeline(object):
    def open_spider(self, spider):
        db.connect()
        try:
            db.create_tables([Torrent, MagnetLink])
        except peewee.OperationalError:
            pass

    def close_spider(self, spider):
        db.close()
        driver.quit()

    def process_item(self, item, spider):
        magnet_urls = item.pop('magnet_urls')
        magnet_exists = False

        for link in magnet_urls:
            magnet = MagnetLink.get_or_none(MagnetLink.link == link)
            if magnet:
                magnet_exists = magnet
                break
        else:
            try:
                torrent = Torrent.create(**item)
                for url in magnet_urls:
                    MagnetLink.create(torrent=torrent, link=url)
                msg = f"CREATED - {item['title']}"
                logging.info(msg)
                return msg
            except Exception as error:
                msg = f"ERROR - {error}"
                logging.info(msg)
                return msg

        torrent = magnet.torrent
        updated = False
        for link in magnet_urls:
            magnet = MagnetLink.get_or_none(MagnetLink.link == link)
            if not magnet:
                MagnetLink.create(torrent=torrent, link=link)
                updated = True
        msg = f"{'UPDATED' if updated else 'OK'} - {item['title']}"
        logging.info(msg)
        return msg
