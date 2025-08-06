import json
import sqlite3
import os
from datetime import datetime

class WelfareDataImporter:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def connect_db(self):
        """DB 연결"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print(f"✅ DB 연결 성공: {self.db_path}")
        except Exception as e:
            print(f"❌ DB 연결 실패: {e}")
            raise
    
    def create_table(self):
        """테이블 생성"""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS welfare_policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    region TEXT NOT NULL,
                    age_min INTEGER,
                    age_max INTEGER,
                    application_period TEXT,
                    conditions TEXT,
                    benefits TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 인덱스 생성
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_region ON welfare_policies(region)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_age_range ON welfare_policies(age_min, age_max)')
            
            self.conn.commit()
            print("✅ 테이블 및 인덱스 생성 완료")
            
        except Exception as e:
            print(f"❌ 테이블 생성 실패: {e}")
            raise
    
    def load_json_data(self, json_path):
        """JSON 파일 로드"""
        try:
            if not os.path.exists(json_path):
                raise FileNotFoundError(f"JSON 파일이 없습니다: {json_path}")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"✅ JSON 파일 로드 완료: {len(data)}개 정책")
            return data
            
        except Exception as e:
            print(f"❌ JSON 파일 로드 실패: {e}")
            raise
    
    def normalize_data(self, data):
        """데이터 정규화"""
        normalized_data = []
        
        for item in data:
            try:
                # region 정규화 (문자열로 통일)
                region = item.get('region', '')
                if isinstance(region, list):
                    region = ', '.join(region)
                elif not region:
                    region = '미정'
                
                # age_range 정규화
                age_range = item.get('age_range', [])
                if isinstance(age_range, list) and len(age_range) > 0:
                    age_min = min(age_range)
                    age_max = max(age_range)
                else:
                    age_min = -1
                    age_max = -1
                
                # 기타 필드 정규화
                normalized_item = {
                    'title': item.get('title', '').strip(),
                    'url': item.get('url', '').strip(),
                    'region': region.strip(),
                    'age_min': age_min,
                    'age_max': age_max,
                    'application_period': item.get('application_period', '').strip(),
                    'conditions': item.get('conditions', '').strip(),
                    'benefits': item.get('benefits', '').strip()
                }
                
                # 필수 필드 검증
                if normalized_item['title'] and normalized_item['url']:
                    normalized_data.append(normalized_item)
                else:
                    print(f"⚠️ 필수 필드 누락: {item.get('title', '제목없음')}")
                    
            except Exception as e:
                print(f"❌ 데이터 정규화 에러: {e}")
                continue
        
        return normalized_data
    
    def insert_data(self, data):
        """데이터 삽입"""
        try:
            # 기존 데이터 삭제 (선택사항)
            self.cursor.execute('DELETE FROM welfare_policies')
            print("🗑️ 기존 데이터 삭제 완료")
            
            # 새 데이터 삽입
            for i, item in enumerate(data):
                try:
                    self.cursor.execute('''
                        INSERT INTO welfare_policies 
                        (title, url, region, age_min, age_max, application_period, conditions, benefits)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item['title'],
                        item['url'],
                        item['region'],
                        item['age_min'],
                        item['age_max'],
                        item['application_period'],
                        item['conditions'],
                        item['benefits']
                    ))
                    
                    if (i + 1) % 10 == 0:
                        print(f"📝 {i + 1}개 정책 삽입 완료")
                        
                except Exception as e:
                    print(f"❌ 정책 삽입 에러 ({item.get('title', '제목없음')}): {e}")
                    continue
            
            self.conn.commit()
            print(f"✅ 총 {len(data)}개 정책 삽입 완료")
            
        except Exception as e:
            print(f"❌ 데이터 삽입 실패: {e}")
            self.conn.rollback()
            raise
    
    def verify_data(self):
        """데이터 검증"""
        try:
            # 전체 개수 확인
            self.cursor.execute('SELECT COUNT(*) FROM welfare_policies')
            total_count = self.cursor.fetchone()[0]
            
            # 지역별 개수 확인
            self.cursor.execute('SELECT region, COUNT(*) FROM welfare_policies GROUP BY region')
            region_counts = self.cursor.fetchall()
            
            # 나이 범위별 개수 확인
            self.cursor.execute('''
                SELECT 
                    CASE 
                        WHEN age_min = -1 THEN '나이정보없음'
                        WHEN age_min >= 0 AND age_max <= 29 THEN '20대'
                        WHEN age_min >= 30 AND age_max <= 39 THEN '30대'
                        ELSE '기타'
                    END as age_group,
                    COUNT(*)
                FROM welfare_policies 
                GROUP BY age_group
            ''')
            age_counts = self.cursor.fetchall()
            
            print(f"\n📊 데이터 검증 결과:")
            print(f"총 정책 수: {total_count}개")
            print(f"\n지역별 분포:")
            for region, count in region_counts:
                print(f"  {region}: {count}개")
            print(f"\n나이대별 분포:")
            for age_group, count in age_counts:
                print(f"  {age_group}: {count}개")
            
            return total_count > 0
            
        except Exception as e:
            print(f"❌ 데이터 검증 실패: {e}")
            return False
    
    def close_db(self):
        """DB 연결 종료"""
        if self.conn:
            self.conn.close()
            print("✅ DB 연결 종료")

def main():
    # 설정
    db_path = r'C:\B조\DB\ibm_data.db'
    json_path = r'C:\B조\crawling\welfare_policies.json'
    
    # JSON 파일이 없으면 기존 파일들 사용
    if not os.path.exists(json_path):
        print("⚠️ welfare_policies.json 파일이 없습니다. 기존 파일들을 통합합니다.")
        
        # 기존 JSON 파일들 로드
        seoul_path = r'C:\B조\crawling\seoul.json'
        incheon_path = r'C:\B조\crawling\incheon.json'
        gyeonggi_path = r'C:\B조\crawling\gyeonggi.json'
        
        all_data = []
        
        for path in [seoul_path, incheon_path, gyeonggi_path]:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        all_data.extend(data)
                        print(f"✅ {path} 로드 완료: {len(data)}개")
                except Exception as e:
                    print(f"❌ {path} 로드 실패: {e}")
        
        # 통합 데이터를 임시 파일로 저장
        json_path = r'C:\B조\crawling\combined_policies.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 통합 데이터 저장: {json_path}")
    
    # 데이터 임포트 실행
    importer = WelfareDataImporter(db_path)
    
    try:
        # 1. DB 연결
        importer.connect_db()
        
        # 2. 테이블 생성
        importer.create_table()
        
        # 3. JSON 데이터 로드
        data = importer.load_json_data(json_path)
        
        # 4. 데이터 정규화
        normalized_data = importer.normalize_data(data)
        print(f"✅ 정규화 완료: {len(normalized_data)}개 정책")
        
        # 5. 데이터 삽입
        importer.insert_data(normalized_data)
        
        # 6. 데이터 검증
        success = importer.verify_data()
        
        if success:
            print("\n🎉 데이터 임포트 성공!")
        else:
            print("\n⚠️ 데이터 임포트에 문제가 있을 수 있습니다.")
            
    except Exception as e:
        print(f"\n❌ 데이터 임포트 실패: {e}")
        
    finally:
        importer.close_db()

if __name__ == "__main__":
    main() 