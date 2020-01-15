from config.api_keys import CRYPTOPANIC_API_KEY

from collections import namedtuple
from bs4 import BeautifulSoup
import requests
import pickle
import json

URL = 'https://cryptopanic.com/api/v1/posts/?auth_token={}&public=true&page={}'
News = namedtuple('News', 'title description source created_at currencies url')

news = []
for page in range(1, 10):
    r = requests.get(URL.format(CRYPTOPANIC_API_KEY, page))
    response = json.loads(r.text)
    results = response['results']
    for r in results:
        if r['kind'] != 'news':
            continue
        url = r['url']
        details = requests.get(url)
        soup = BeautifulSoup(details.text, 'html.parser')
        description = soup.find("meta", property="og:description")
        description = description['content']
        news.append(News(r['title'], description, r['domain'], r['created_at'],
                         [currency['code'] for currency in r['currencies']] if 'currencies' in r else [],
                         url))


with open('news.pickle', 'wb') as f:
    pickle.dump(news, f)
