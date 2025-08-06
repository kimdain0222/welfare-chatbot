#모든 데이터가 DB와 호환되는지 확인하는 코드
#JSON 파일들의 데이터가 데이터베이스와 호환되는지 검사
#언제 사용: 새로운 데이터를 추가하기 전에 확인할 때

import json
import sqlite3
from typing import List, Dict, Any

def load_json_data(filename: str) -> List[Dict[str, Any]]:
    """JSON 파일 로드"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ {filename} 로드 실패: {e}")
        return []

def create_test_database():
    """테스트용 DB 생성"""
    conn = sqlite3.connect(':memory:')  # 메모리 DB 사용
    cursor = conn.cursor()
    
    # 복지정책 테이블 생성
    cursor.execute('''
        CREATE TABLE welfare_policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT,
            region TEXT,
            age_range TEXT,  -- JSON 형태로 저장
            application_period TEXT,
            conditions TEXT,
            benefits TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

def insert_data_to_db(conn, data: List[Dict[str, Any]], region: str):
    """데이터를 DB에 삽입"""
    cursor = conn.cursor()
    
    success_count = 0
    error_count = 0
    
    for item in data:
        try:
            # age_range를 JSON 문자열로 변환
            age_range_json = json.dumps(item.get('age_range', []), ensure_ascii=False)
            
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
            success_count += 1
            
        except Exception as e:
            print(f"❌ 데이터 삽입 실패: {e}")
            print(f"   문제 데이터: {item.get('title', '제목 없음')}")
            error_count += 1
    
    conn.commit()
    return success_count, error_count

def test_data_retrieval(conn):
    """데이터 조회 테스트"""
    cursor = conn.cursor()
    
    # 전체 데이터 수 확인
    cursor.execute('SELECT COUNT(*) FROM welfare_policies')
    total_count = cursor.fetchone()[0]
    print(f"📊 전체 데이터 수: {total_count}개")
    
    # 지역별 데이터 수 확인
    cursor.execute('SELECT region, COUNT(*) FROM welfare_policies GROUP BY region')
    region_counts = cursor.fetchall()
    print("📊 지역별 데이터 수:")
    for region, count in region_counts:
        print(f"   {region}: {count}개")
    
    # 샘플 데이터 조회
    cursor.execute('''
        SELECT title, region, age_range, application_period 
        FROM welfare_policies 
        LIMIT 3
    ''')
    samples = cursor.fetchall()
    print("\n📋 샘플 데이터:")
    for sample in samples:
        title, region, age_range, period = sample
        age_list = json.loads(age_range) if age_range else []
        print(f"   제목: {title}")
        print(f"   지역: {region}")
        print(f"   연령: {age_list}")
        print(f"   기간: {period}")
        print()

def validate_data_structure(data: List[Dict[str, Any]], region: str) -> Dict[str, Any]:
    """데이터 구조 검증"""
    validation_result = {
        'total_items': len(data),
        'valid_items': 0,
        'missing_fields': {},
        'data_types': {},
        'errors': []
    }
    
    required_fields = ['title', 'url', 'region', 'age_range', 'application_period', 'conditions', 'benefits']
    
    for i, item in enumerate(data):
        item_valid = True
        
        # 필수 필드 확인
        for field in required_fields:
            if field not in item:
                if field not in validation_result['missing_fields']:
                    validation_result['missing_fields'][field] = 0
                validation_result['missing_fields'][field] += 1
                item_valid = False
                validation_result['errors'].append(f"항목 {i+1}: {field} 필드 누락")
        
        # 데이터 타입 확인
        if 'age_range' in item and not isinstance(item['age_range'], list):
            validation_result['errors'].append(f"항목 {i+1}: age_range가 리스트가 아님")
            item_valid = False
        
        if 'region' in item and not isinstance(item['region'], (str, list)):
            validation_result['errors'].append(f"항목 {i+1}: region 타입 오류")
            item_valid = False
        
        if item_valid:
            validation_result['valid_items'] += 1
    
    return validation_result

def main():
    """메인 테스트 함수"""
    print("🔍 DB 호환성 테스트 시작\n")
    
    # JSON 파일들 로드
    regions = ['gyeonggi', 'incheon', 'seoul']
    all_data = {}
    
    for region in regions:
        filename = f"crawling/{region}.json"
        data = load_json_data(filename)
        all_data[region] = data
        print(f"📁 {filename}: {len(data)}개 항목 로드됨")
    
    print("\n" + "="*50)
    print("📋 데이터 구조 검증")
    print("="*50)
    
    for region, data in all_data.items():
        print(f"\n🔍 {region.upper()} 데이터 검증:")
        validation = validate_data_structure(data, region)
        
        print(f"   전체 항목: {validation['total_items']}개")
        print(f"   유효 항목: {validation['valid_items']}개")
        
        if validation['missing_fields']:
            print("   누락된 필드:")
            for field, count in validation['missing_fields'].items():
                print(f"     {field}: {count}개")
        
        if validation['errors']:
            print("   오류:")
            for error in validation['errors'][:5]:  # 처음 5개만 표시
                print(f"     {error}")
            if len(validation['errors']) > 5:
                print(f"     ... 외 {len(validation['errors']) - 5}개 오류")
    
    print("\n" + "="*50)
    print("🗄️ DB 호환성 테스트")
    print("="*50)
    
    # DB 생성 및 데이터 삽입 테스트
    conn = create_test_database()
    
    total_success = 0
    total_error = 0
    
    for region, data in all_data.items():
        print(f"\n💾 {region.upper()} 데이터 DB 삽입:")
        success, error = insert_data_to_db(conn, data, region)
        total_success += success
        total_error += error
        print(f"   성공: {success}개, 실패: {error}개")
    
    print(f"\n📊 전체 결과: 성공 {total_success}개, 실패 {total_error}개")
    
    # 데이터 조회 테스트
    test_data_retrieval(conn)
    
    conn.close()
    
    print("\n" + "="*50)
    print("✅ 테스트 완료")
    print("="*50)
    
    if total_error == 0:
        print("🎉 모든 데이터가 DB와 호환됩니다!")
    else:
        print(f"⚠️ {total_error}개의 데이터에 문제가 있습니다. 위의 오류 메시지를 확인해주세요.")

if __name__ == "__main__":
    main() 