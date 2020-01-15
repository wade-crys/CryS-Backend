from collections import namedtuple
import pickle

News = namedtuple('News', 'title description source created_at currencies url')

with open('news.pickle', 'rb') as f:
    news = pickle.load(f)

for n in news:
    print(n)
