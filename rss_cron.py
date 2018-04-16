import logging
logging.basicConfig(filename='/home/dale/local_news/rss_update.log',level=logging.INFO, format='%(asctime)s %(message)s')

import pandas as pd
import requests
from bs4 import BeautifulSoup
import sys
import time
import utils

from dbWrapper import dbWrapper

db = dbWrapper()


local_news = db.execute("SELECT DISTINCT ON (name) * FROM local_news WHERE rss_link != 'None'")

# Some of the rss links don't include the base url
def addBaseUrl(row):
    if 'http' in row['rss_link']:
            return row['rss_link']
    return row['url'] + row['rss_link']

local_news['rss_link'] = local_news.apply(addBaseUrl, axis=1)

def getArticles(row):
    # this is a bug many sites seem to have--including this line prevents any news articles from being included
    rss_link = row['rss_link'].replace('&k[]=%23topstory', '')
    r = requests.get(rss_link)
    bs = BeautifulSoup(r.text, 'html5lib')
    articles = pd.DataFrame([(item.find('title').text, 
      item.find('pubdate').text,
      item.find('description').text,
      item.find('link').next_element.strip(),
     )
    for item in bs.find_all('item')], columns=['headline', 'pub_date', 'description', 'link'])
    
    articles['pub_date'] = pd.to_datetime(articles['pub_date'])
    articles['pub_name'] = row['name']
    articles['pub_id'] = row['id']
    
    # the primary id for the rss_articles table is the positive 
    # hash of the concatinated pub_name and headline
    articles['id'] = articles.apply(lambda x: utils.hash(x['pub_name'] + x['headline']), axis=1)
    
    # drop duplicates
    return articles[~articles.duplicated('id')]

def updateRss(pub_row):
    try:
        articles = getArticles(pub_row)
    except Exception as e:
        logging.error("Error getting articles for %s: %s" % (pub_row['name'], str(e)))
        return
        
    for row in articles.iterrows():
        x = row[1]
        try:
            db.execute("""
                INSERT INTO rss_articles (headline, pub_date, description, link, pub_name, pub_id, id) VALUES
                (%s, %s, %s, %s, %s, {pub_id}, {id}) ON CONFLICT (id) DO NOTHING""".format(**x), 
                            [x['headline'], x['pub_date'], x['description'], x['link'], x['pub_name']])
        except Exception as e:
            logging.error("Error writing db for %s: %s" % (pub_row['name'], str(e)))
            return
            
    logging.info("Fetched %d articles for %s" % (len(articles), pub_row['name']))
    
    
def job():
    local_news.apply(updateRss, axis=1)

if __name__ == "__main__":
	job()
