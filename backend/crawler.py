import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import sqlite3
import pandas as pd
import os
import sys

# 현재 파일의 디렉토리를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db

class DongACrawler:
    def __init__(self):
        self.base_url = "https://www.donga.com"
        self.health_url = "https://www.donga.com/news/Health"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.age_keywords = [
            '50대', '60대', '70대', '중장년', '중년', '노년', '어르신',
            '갱년기', '폐경', '전립선', '골다공증', '고혈압', '당뇨',
            '관절염', '치매', '노인', '시니어', '중노년',
            '뇌졸중', '심근경색', '혈관 건강', '콜레스테롤', '만성질환',
            '영양소', '비타민', '근력 운동', '유산소 운동', '건강검진',
            '정신 건강', '우울증', '불면증', '소화불량', '예방 접종'
        ]

    def _get_article_content(self, url):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
            # 사용자가 제공한 소스를 기반으로 정확한 선택자로 수정
            content_area = soup.find('section', class_='news_view')
            if content_area:
                for unwanted in content_area.find_all(['div', 'script', 'figure', 'section', 'header'], class_=re.compile(r'(ad|related|thumb|head|poll|byline|news_view|expression|comment|sub_inner|reporter)')):
                    unwanted.decompose()
                return content_area.get_text('\n', strip=True)
            return ""
        except Exception as e:
            print(f"본문 파싱 오류 ({url}): {e}")
            return ""

    def crawl_health_articles(self):
        articles = []
        try:
            response = self.session.get(self.health_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding='utf-8')
            
            latest_news_container = soup.select_one('div.latest_news')
            if not latest_news_container:
                print("최신 뉴스 컨테이너('div.latest_news')를 찾지 못했습니다.")
                return []

            article_elements = latest_news_container.select('ul.row_list > li')
            print(f"{len(article_elements)}개의 기사 요소를 찾았습니다.")

            for element in article_elements:
                try:
                    news_card = element.find('article', class_='news_card')
                    if not news_card:
                        continue

                    title_elem = news_card.select_one('h4.tit a')
                    if not title_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    href = title_elem.get('href', '')

                    if not href:
                        continue

                    if href and not href.startswith('http'):
                        href = self.base_url + href

                    if len(title) > 5 and 'news' in href:
                        conn = init_db()
                        c = conn.cursor()
                        c.execute("SELECT id FROM articles WHERE url = ?", (href,))
                        if c.fetchone():
                            conn.close()
                            continue
                        conn.close()

                        summary_elem = news_card.select_one('p.desc')
                        summary = summary_elem.get_text(strip=True) if summary_elem else ''

                        print(f"\n기사 상세 페이지 방문: {href}")
                        content = self._get_article_content(href)
                        if not content:
                            print(f"본문이 없는 기사를 건너뜁니다: {title}")
                            continue

                        if not summary:
                            summary = content[:150] + "..."

                        full_text = f"{title} {summary} {content}".lower()
                        is_age_relevant = any(keyword in full_text for keyword in self.age_keywords)
                        matched_keywords = [kw for kw in self.age_keywords if kw in full_text]

                        articles.append({
                            'title': title,
                            'summary': summary,
                            'content': content,
                            'url': href,
                            'is_age_relevant': is_age_relevant,
                            'keywords': ', '.join(matched_keywords) if matched_keywords else ''
                        })
                except Exception as e:
                    print(f"Error processing element: {e}")
                    continue
        except Exception as e:
            print(f"[ERROR] Crawling error: {str(e)}")
            articles = []
        return articles

    def save_articles(self, articles, conn):
        if not articles:
            return 0, 0
        c = conn.cursor()
        new_articles, age_relevant_count = 0, 0
        for article in articles:
            try:
                c.execute("SELECT id FROM articles WHERE url = ?", (article['url'],))
                if not c.fetchone():
                    c.execute("""
                        INSERT INTO articles 
                        (title, summary, content, url, crawled_date, is_age_relevant, keywords)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        article['title'], 
                        article['summary'], 
                        article['content'], 
                        article['url'], 
                        datetime.now(), 
                        article['is_age_relevant'], 
                        article['keywords']
                    ))
                    new_articles += 1
                    if article['is_age_relevant']:
                        age_relevant_count += 1
            except sqlite3.IntegrityError:
                continue
            except Exception as e:
                print(f"Error saving article {article.get('url')}: {e}")
                continue
        conn.commit()
        return new_articles, age_relevant_count