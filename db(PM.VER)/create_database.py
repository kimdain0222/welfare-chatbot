#"실제 데이터베이스를 만들고 데이터를 넣는 도구"
#하는 일:
#새로운 데이터베이스 파일 생성
#JSON 파일의 데이터를 DB에 저장
#중복 데이터 체크 및 업데이트
#언제 사용: 처음 DB를 만들거나 새로운 데이터를 추가할 때



import json
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any

def create_database(db_path: str = "welfare_policies.db"):
    """복지정책 데이터베이스 생성"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 복지정책 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS welfare_policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT,
            region TEXT,
            age_range TEXT,  -- JSON 형태로 저장
            application_period TEXT,
            conditions TEXT,
            benefits TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 인덱스 생성 (검색 성능 향상)
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_region ON welfare_policies(region)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON welfare_policies(title)')
    
    conn.commit()
    return conn

def load_json_data(filename: str) -> List[Dict[str, Any]]:
    """JSON 파일 로드"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ {filename} 로드 실패: {e}")
        return []

def insert_data_to_db(conn, data: List[Dict[str, Any]], region: str):
    """데이터를 DB에 삽입"""
    cursor = conn.cursor()
    
    success_count = 0
    error_count = 0
    
    for item in data:
        try:
            # age_range를 JSON 문자열로 변환
            age_range_json = json.dumps(item.get('age_range', []), ensure_ascii=False)
            
            # 중복 체크 (URL 기준)
            cursor.execute('SELECT id FROM welfare_policies WHERE url = ?', (item.get('url', ''),))
            existing = cursor.fetchone()
            
            if existing:
                # 기존 데이터 업데이트
                cursor.execute('''
                    UPDATE welfare_policies 
                    SET title = ?, region = ?, age_range = ?, application_period = ?, 
                        conditions = ?, benefits = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE url = ?
                ''', (
                    item.get('title', ''),
                    region,
                    age_range_json,
                    item.get('application_period', ''),
                    item.get('conditions', ''),
                    item.get('benefits', ''),
                    item.get('url', '')
                ))
                print(f"   업데이트: {item.get('title', '제목 없음')}")
            else:
                # 새 데이터 삽입
                cursor.execute('''
                    INSERT INTO welfare_policies 
                    (title, url, region, age_range, application_period, conditions, benefits)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item.get('title', ''),
                    item.get('url', ''),
                    region,
                    age_range_json,
                    item.get('application_period', ''),
                    item.get('conditions', ''),
                    item.get('benefits', '')
                ))
                print(f"   삽입: {item.get('title', '제목 없음')}")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ 데이터 처리 실패: {e}")
            print(f"   문제 데이터: {item.get('title', '제목 없음')}")
            error_count += 1
    
    conn.commit()
    return success_count, error_count

def display_database_stats(conn):
    """데이터베이스 통계 표시"""
    cursor = conn.cursor()
    
    # 전체 데이터 수
    cursor.execute('SELECT COUNT(*) FROM welfare_policies')
    total_count = cursor.fetchone()[0]
    print(f"\n📊 데이터베이스 통계:")
    print(f"   전체 정책 수: {total_count}개")
    
    # 지역별 데이터 수
    cursor.execute('SELECT region, COUNT(*) FROM welfare_policies GROUP BY region')
    region_counts = cursor.fetchall()
    print("   지역별 정책 수:")
    for region, count in region_counts:
        print(f"     {region}: {count}개")
    
    # 최근 업데이트된 정책
    cursor.execute('''
        SELECT title, region, updated_at 
        FROM welfare_policies 
        ORDER BY updated_at DESC 
        LIMIT 5
    ''')
    recent_policies = cursor.fetchall()
    print("\n   최근 업데이트된 정책:")
    for title, region, updated_at in recent_policies:
        print(f"     {title} ({region}) - {updated_at}")

def test_database_queries(conn):
    """데이터베이스 쿼리 테스트"""
    cursor = conn.cursor()
    
    print("\n🔍 데이터베이스 쿼리 테스트:")
    
    # 1. 특정 지역의 정책 검색
    print("\n1. 경기도 정책 검색:")
    cursor.execute('''
        SELECT title, application_period 
        FROM welfare_policies 
        WHERE region = 'gyeonggi' 
        LIMIT 3
    ''')
    gyeonggi_policies = cursor.fetchall()
    for title, period in gyeonggi_policies:
        print(f"   {title} - {period}")
    
    # 2. 특정 연령대 정책 검색
    print("\n2. 20대 대상 정책 검색:")
    cursor.execute('''
        SELECT title, region, age_range 
        FROM welfare_policies 
        WHERE age_range LIKE '%20%' 
        LIMIT 3
    ''')
    age_policies = cursor.fetchall()
    for title, region, age_range in age_policies:
        age_list = json.loads(age_range) if age_range else []
        print(f"   {title} ({region}) - 연령: {age_list}")
    
    # 3. 월세 관련 정책 검색
    print("\n3. 월세 관련 정책 검색:")
    cursor.execute('''
        SELECT title, region, benefits 
        FROM welfare_policies 
        WHERE title LIKE '%월세%' OR benefits LIKE '%월세%'
        LIMIT 3
    ''')
    rent_policies = cursor.fetchall()
    for title, region, benefits in rent_policies:
        print(f"   {title} ({region})")
        print(f"     혜택: {benefits[:100]}...")

def main():
    """메인 함수"""
    print("🗄️ 복지정책 데이터베이스 생성 시작\n")
    
    # 데이터베이스 생성
    db_path = "welfare_policies.db"
    conn = create_database(db_path)
    print(f"✅ 데이터베이스 생성 완료: {db_path}")
    
    # JSON 파일들 로드 및 삽입
    regions = ['gyeonggi', 'incheon', 'seoul']
    total_success = 0
    total_error = 0
    
    for region in regions:
        filename = f"crawling/{region}.json"
        print(f"\n📁 {filename} 처리 중...")
        
        data = load_json_data(filename)
        if data:
            success, error = insert_data_to_db(conn, data, region)
            total_success += success
            total_error += error
            print(f"   결과: 성공 {success}개, 실패 {error}개")
        else:
            print(f"   ❌ {filename}에서 데이터를 로드할 수 없습니다.")
    
    print(f"\n📊 전체 결과: 성공 {total_success}개, 실패 {total_error}개")
    
    # 데이터베이스 통계 표시
    display_database_stats(conn)
    
    # 쿼리 테스트
    test_database_queries(conn)
    
    conn.close()
    
    print(f"\n🎉 데이터베이스 생성 완료!")
    print(f"📁 파일 위치: {os.path.abspath(db_path)}")
    print(f"📊 총 {total_success}개의 정책이 저장되었습니다.")

if __name__ == "__main__":
    main() 