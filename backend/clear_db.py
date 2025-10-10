import os
import sys
import sqlite3

# 현재 파일의 디렉토리를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DB_FILE, init_db

def clear_database_tables():
    """
    새로운 시작을 위해 'articles'와 'videos' 테이블의 모든 레코드를 삭제합니다.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        print("'videos' 테이블의 모든 레코드를 삭제합니다...")
        c.execute("DELETE FROM videos")
        print("'videos' 테이블 삭제 완료.")

        print("'articles' 테이블의 모든 레코드를 삭제합니다...")
        c.execute("DELETE FROM articles")
        print("'articles' 테이블 삭제 완료.")

        conn.commit()
        print("데이터베이스의 모든 기사와 영상 데이터가 성공적으로 삭제되었습니다.")

    except Exception as e:
        print(f"데이터베이스를 비우는 중 오류가 발생했습니다: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("데이터베이스 테이블 구조를 확인하고 초기화합니다...")
    # 테이블이 존재하지 않을 경우를 대비해 init_db() 호출
    init_db()
    
    # 테이블 데이터 삭제 실행
    clear_database_tables()
