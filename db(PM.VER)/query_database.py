#데이터베이스에서 정보를 찾고 보는 도구"
#하는 일:
#지역별 정책 검색 (경기, 인천, 서울)
#키워드로 정책 찾기 (예: "월세", "청년")
#연령대별 정책 검색
#데이터베이스 통계 보기
#언제 사용: 저장된 정책 정보를 찾거나 확인할 때






import sqlite3
import json
from typing import List, Dict, Any

def connect_database(db_path: str = "welfare_policies.db"):
    """데이터베이스 연결"""
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return None

def get_database_info(conn):
    """데이터베이스 기본 정보 조회"""
    cursor = conn.cursor()
    
    # 테이블 정보
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("📋 데이터베이스 테이블:")
    for table in tables:
        print(f"   - {table[0]}")
    
    # 전체 데이터 수
    cursor.execute('SELECT COUNT(*) FROM welfare_policies')
    total_count = cursor.fetchone()[0]
    print(f"\n📊 전체 정책 수: {total_count}개")
    
    # 지역별 통계
    cursor.execute('SELECT region, COUNT(*) FROM welfare_policies GROUP BY region')
    region_stats = cursor.fetchall()
    print("📊 지역별 정책 수:")
    for region, count in region_stats:
        print(f"   {region}: {count}개")

def search_policies_by_region(conn, region: str):
    """지역별 정책 검색"""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT title, application_period, age_range 
        FROM welfare_policies 
        WHERE region = ? 
        ORDER BY title
    ''', (region,))
    
    policies = cursor.fetchall()
    print(f"\n🔍 {region} 지역 정책 ({len(policies)}개):")
    for i, (title, period, age_range) in enumerate(policies, 1):
        age_list = json.loads(age_range) if age_range else []
        print(f"   {i}. {title}")
        print(f"      기간: {period}")
        print(f"      연령: {age_list}")
        print()

def search_policies_by_keyword(conn, keyword: str):
    """키워드로 정책 검색"""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT title, region, benefits 
        FROM welfare_policies 
        WHERE title LIKE ? OR benefits LIKE ? OR conditions LIKE ?
        ORDER BY region, title
    ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
    
    policies = cursor.fetchall()
    print(f"\n🔍 '{keyword}' 관련 정책 ({len(policies)}개):")
    for i, (title, region, benefits) in enumerate(policies, 1):
        print(f"   {i}. {title} ({region})")
        if benefits:
            print(f"      혜택: {benefits[:100]}...")
        print()

def search_policies_by_age(conn, age: int):
    """특정 연령대 정책 검색"""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT title, region, age_range, application_period 
        FROM welfare_policies 
        WHERE age_range LIKE ?
        ORDER BY region, title
    ''', (f'%{age}%',))
    
    policies = cursor.fetchall()
    print(f"\n🔍 {age}세 대상 정책 ({len(policies)}개):")
    for i, (title, region, age_range, period) in enumerate(policies, 1):
        age_list = json.loads(age_range) if age_range else []
        print(f"   {i}. {title} ({region})")
        print(f"      연령: {age_list}")
        print(f"      기간: {period}")
        print()

def get_recent_policies(conn, limit: int = 10):
    """최근 추가된 정책 조회"""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT title, region, created_at 
        FROM welfare_policies 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (limit,))
    
    policies = cursor.fetchall()
    print(f"\n🕒 최근 추가된 정책 (상위 {len(policies)}개):")
    for i, (title, region, created_at) in enumerate(policies, 1):
        print(f"   {i}. {title} ({region}) - {created_at}")

def export_sample_data(conn, limit: int = 5):
    """샘플 데이터 내보내기"""
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT title, region, age_range, application_period, conditions, benefits 
        FROM welfare_policies 
        ORDER BY RANDOM() 
        LIMIT ?
    ''', (limit,))
    
    policies = cursor.fetchall()
    print(f"\n📋 샘플 데이터 ({len(policies)}개):")
    for i, (title, region, age_range, period, conditions, benefits) in enumerate(policies, 1):
        age_list = json.loads(age_range) if age_range else []
        print(f"\n   {i}. {title}")
        print(f"      지역: {region}")
        print(f"      연령: {age_list}")
        print(f"      기간: {period}")
        print(f"      조건: {conditions[:100]}...")
        print(f"      혜택: {benefits[:100]}...")

def main():
    """메인 함수"""
    print("🔍 복지정책 데이터베이스 조회\n")
    
    # 데이터베이스 연결
    conn = connect_database()
    if not conn:
        return
    
    try:
        # 기본 정보 조회
        get_database_info(conn)
        
        # 지역별 정책 검색
        search_policies_by_region(conn, "gyeonggi")
        search_policies_by_region(conn, "incheon")
        search_policies_by_region(conn, "seoul")
        
        # 키워드 검색
        search_policies_by_keyword(conn, "월세")
        search_policies_by_keyword(conn, "청년")
        
        # 연령대 검색
        search_policies_by_age(conn, 20)
        
        # 최근 정책
        get_recent_policies(conn, 5)
        
        # 샘플 데이터
        export_sample_data(conn, 3)
        
    finally:
        conn.close()
    
    print("\n✅ 데이터베이스 조회 완료!")

if __name__ == "__main__":
    main() 