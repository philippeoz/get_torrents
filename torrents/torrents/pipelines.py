# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import peewee
import logging

from .models import Torrent, MagnetLink, db


class TorrentsPipeline(object):
    def open_spider(self, spider):
        db.connect()
        try:
            db.create_tables([Torrent, MagnetLink])
        except peewee.OperationalError:
            pass
    
    def close_spider(self, spider):
        db.close()

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
