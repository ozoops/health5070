import os
import sys
from crawler import DongACrawler
from database import init_db

# 현재 파일의 디렉토리를 sys.path에 추가하여 모듈을 임포트할 수 있도록 함
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_test_crawl(article_limit=10):
    """
    테스트 목적으로 제한된 수의 기사를 크롤링하고 저장합니다.
    """
    print(f"🚀 {article_limit}개 기사 테스트 크롤링을 시작합니다...")

    # 1. 데이터베이스 연결 초기화
    conn = init_db()
    print("✅ 데이터베이스가 초기화되었습니다.")

    # 2. 크롤러 초기화
    crawler = DongACrawler()
    print("🕷️ 크롤러가 초기화되었습니다. 헬스동아에서 기사를 수집합니다...")

    # 3. 기사 크롤링
    articles = crawler.crawl_health_articles()

    if not articles:
        print("⚠️ 크롤링 중 새로운 기사를 찾지 못했습니다.")
        conn.close()
        return

    print(f"📰 총 {len(articles)}개의 기사를 찾았습니다. 최대 {article_limit}개를 처리합니다.")

    # 4. 테스트를 위해 기사 수를 10개로 제한
    articles_to_save = articles[:article_limit]

    # 5. 제한된 수의 기사를 데이터베이스에 저장
    print(f"💾 {len(articles_to_save)}개의 기사를 데이터베이스에 저장합니다...")
    new_count, age_relevant_count = crawler.save_articles(articles_to_save, conn)

    # 6. 결과 출력
    print("\n--- 테스트 크롤링 요약 ---")
    print(f"✨ {new_count}개의 새로운 기사를 성공적으로 저장했습니다.")
    print(f"🎯 50-70대 관련 기사를 {age_relevant_count}개 찾았습니다.")
    print("--------------------------")

    # 7. 데이터베이스 연결 종료
    conn.close()
    print("✅ 테스트 크롤링이 성공적으로 완료되었습니다.")

if __name__ == "__main__":
    run_test_crawl()
