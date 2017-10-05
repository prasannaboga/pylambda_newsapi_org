# -*- coding: utf-8 -*-
import boto3
import json
import logging
import os
import random
import requests
from lxml import etree
from datetime import datetime
from dateutil import tz

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
  try:
    base_url = 'https://newsapi.org/'
    version = 'v1/'
    
    articles_url = '{0}{1}articles'.format(base_url, version)
  
    payload = {'source': os.environ['source'], 'sortBy': 'latest', 'apiKey': os.environ['apiKey']}
    request = requests.get(articles_url, params=payload)
    
    article = random.choice(request.json()['articles'])
    
    root = etree.Element("Root")
    data_items = etree.SubElement(root, "DataItems")
    etree.SubElement(data_items, "DataItem", description=article['description'])
    etree.SubElement(data_items, "DataItem", title=article['title'])
    if article['author']:
      etree.SubElement(data_items, "DataItem", author=article['author'])

    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('Asia/Calcutta')
    utc = datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
    utc = utc.replace(tzinfo=from_zone)
    ist = utc.astimezone(to_zone)
    
    etree.SubElement(data_items, "DataItem", published_at=ist.strftime('%b %d, %Y'))

  except Exception, e:
    logger.exception("lambda_handler caught error")
    root = etree.Element("Root")
    data_items = etree.SubElement(root, "DataItems")
    etree.SubElement(data_items, "DataItem", description=str(e))
    raise
  finally:
    xml = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='ISO-8859-1')
    print(xml)
    s3 = boto3.resource('s3')
    s3.Bucket('the-shire').put_object(Key='message_board/newsapi.xml',
                                      Body=xml,
                                      ContentType='text/xml',
                                      ACL='public-read',
                                      ContentEncoding='UTF-16')

  return True
