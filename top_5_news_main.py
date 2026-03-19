import feedparser
from newspaper import Article
from textblob import TextBlob
import pymongo
from datetime import datetime
import time
import os
import certifi

MONGO_URI = os.getenv("MONGO_URI")

client = pymongo.MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.finance_robot
collection = db.articles

RSS_FEEDS = {
    'CNN Business': 'http://rss.cnn.com/rss/money_latest.rss',
    'BBC Business': 'http://feeds.bbci.co.uk/news/business/rss.xml',
    'Yahoo Finance': 'https://finance.yahoo.com/news/rssindex'
}

def get_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    score = (polarity + 1) / 2
    intensity = abs(polarity)
    return score, intensity

def calculate_importance(content, sentiment_score):
    keywords = ['fed','surge','rally','ATH','outperform','plunge','plummet','sell-out','slide','dip','guidance','bullish','bearish','blue-chip','ipo','hawkish','dovish','fomc','YTD','YoY','QoQ','inflation','rate cut','earnings','nasdaq','s&p 500','DJIA','QQQ','apple','meta','google','nvidia']
    hit_count = sum(1 for word in keywords if word in content.lower())
    kw_score = min(hit_count / 3, 1.0)
    len_score = min(len(content) / 800, 1.0)
    total_score = (0.4 * sentiment_score) + (0.4 * kw_score) + (0.2 * len_score)
    return round(total_score, 3)

def main():
    for name, url in RSS_FEEDS.items():
        print(f"正在掃描 {name}...")
        feed = feedparser.parse(url)

        for entry in feed.entries[:10]:
            link = entry.link

            # 去重邏輯
            if collection.find_one({"link": link}):
                continue

            try:
                article = Article(link)
                article.download()
                article.parse()

                content = article.text
                title = entry.title

                sent_score, intensity = get_sentiment(title)
                final_score = calculate_importance(content, sent_score)

                news_obj = {
                    "title": title,
                    "link": link,
                    "source": name,
                    "content": content[:500],
                    "sentiment_score": sent_score,
                    "importance_score": final_score,
                    "published": entry.get('published', ''),
                    "created_at": datetime.now()
                }

                collection.insert_one(news_data)
                print(f"成功新增: [{final_score}] {title[:30]}...")
                time.sleep(1) 

            except Exception as e:
                print(f"解析失敗 {link}: {e}")

    print(f"--- 任務結束 ---")

if __name__ == "__main__":
    main()
