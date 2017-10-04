# -*- coding: utf-8 -*-
import boto3
import json
import logging
import os
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
    
    first_article = request.json()['articles'][0]
    
    root = etree.Element("Root")
    data_items = etree.SubElement(root, "DataItems")
    etree.SubElement(data_items, "DataItem", description=first_article['description'])
    etree.SubElement(data_items, "DataItem", title=first_article['title'])
    etree.SubElement(data_items, "DataItem", author=first_article['author'])

    from_zone = tz.gettz('UTC')
    to_zone = tz.gettz('Asia/Calcutta')
    utc = datetime.strptime(first_article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')
    utc = utc.replace(tzinfo=from_zone)
    ist = utc.astimezone(to_zone)
    
    etree.SubElement(data_items, "DataItem", published_at=ist.strftime('%b %d, %Y'))
    etree.write(root, encoding='UTF-16', xml_declaration=True)

  except Exception, e:
    logger.exception("lambda_handler caught error")
    root = etree.Element("Root")
    data_items = etree.SubElement(root, "DataItems")
    etree.SubElement(data_items, "DataItem", description=str(e))
    raise
  finally:
    print(etree.tostring(root, pretty_print=True))
    s3 = boto3.resource('s3')
    s3.Bucket('the-shire').put_object(Key='message_board/newsapi.xml',
                                      Body=etree.tostring(root, pretty_print=True),
                                      ContentType='text/xml',
                                      ACL='public-read',
                                      ContentEncoding='UTF-16')

  return True
