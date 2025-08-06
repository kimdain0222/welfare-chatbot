import sqlite3
import json
import os
from datetime import datetime

class WelfareDataValidator:
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
    
    def validate_data_quality(self):
        """데이터 품질 검증"""
        print("\n🔍 데이터 품질 검증 시작...")
        
        # 1. 기본 통계
        self._show_basic_stats()
        
        # 2. 필수 필드 검증
        self._validate_required_fields()
        
        # 3. 데이터 일관성 검증
        self._validate_data_consistency()
        
        # 4. 중복 데이터 검증
        self._validate_duplicates()
        
        # 5. URL 유효성 검증
        self._validate_urls()
        
        # 6. 나이 범위 검증
        self._validate_age_ranges()
        
        print("\n✅ 데이터 품질 검증 완료")
    
    def _show_basic_stats(self):
        """기본 통계 정보"""
        print("\n📊 기본 통계:")
        
        # 전체 개수
        self.cursor.execute('SELECT COUNT(*) FROM welfare_policies')
        total_count = self.cursor.fetchone()[0]
        print(f"  총 정책 수: {total_count}개")
        
        # 지역별 분포
        self.cursor.execute('''
            SELECT region, COUNT(*) as count 
            FROM welfare_policies 
            GROUP BY region 
            ORDER BY count DESC
        ''')
        region_stats = self.cursor.fetchall()
        print(f"  지역별 분포:")
        for region, count in region_stats:
            percentage = (count / total_count) * 100
            print(f"    {region}: {count}개 ({percentage:.1f}%)")
        
        # 나이대별 분포
        self.cursor.execute('''
            SELECT 
                CASE 
                    WHEN age_min = -1 THEN '나이정보없음'
                    WHEN age_min >= 0 AND age_max <= 19 THEN '10대'
                    WHEN age_min >= 20 AND age_max <= 29 THEN '20대'
                    WHEN age_min >= 30 AND age_max <= 39 THEN '30대'
                    WHEN age_min >= 40 THEN '40대이상'
                    ELSE '기타'
                END as age_group,
                COUNT(*) as count
            FROM welfare_policies 
            GROUP BY age_group 
            ORDER BY count DESC
        ''')
        age_stats = self.cursor.fetchall()
        print(f"  나이대별 분포:")
        for age_group, count in age_stats:
            percentage = (count / total_count) * 100
            print(f"    {age_group}: {count}개 ({percentage:.1f}%)")
    
    def _validate_required_fields(self):
        """필수 필드 검증"""
        print("\n🔍 필수 필드 검증:")
        
        # 제목이 없는 정책
        self.cursor.execute('SELECT COUNT(*) FROM welfare_policies WHERE title IS NULL OR title = ""')
        empty_title_count = self.cursor.fetchone()[0]
        print(f"  제목 없는 정책: {empty_title_count}개")
        
        # URL이 없는 정책
        self.cursor.execute('SELECT COUNT(*) FROM welfare_policies WHERE url IS NULL OR url = ""')
        empty_url_count = self.cursor.fetchone()[0]
        print(f"  URL 없는 정책: {empty_url_count}개")
        
        # 지역 정보가 없는 정책
        self.cursor.execute('SELECT COUNT(*) FROM welfare_policies WHERE region IS NULL OR region = "" OR region = "미정"')
        empty_region_count = self.cursor.fetchone()[0]
        print(f"  지역 정보 없는 정책: {empty_region_count}개")
        
        if empty_title_count > 0 or empty_url_count > 0:
            print("  ⚠️ 필수 필드가 누락된 정책이 있습니다.")
        else:
            print("  ✅ 모든 필수 필드가 완성되어 있습니다.")
    
    def _validate_data_consistency(self):
        """데이터 일관성 검증"""
        print("\n🔍 데이터 일관성 검증:")
        
        # 나이 범위가 이상한 정책 (최소값이 최대값보다 큰 경우)
        self.cursor.execute('''
            SELECT COUNT(*) FROM welfare_policies 
            WHERE age_min > age_max AND age_min != -1 AND age_max != -1
        ''')
        invalid_age_count = self.cursor.fetchone()[0]
        print(f"  나이 범위 이상한 정책: {invalid_age_count}개")
        
        # 너무 긴 제목 (100자 이상)
        self.cursor.execute('SELECT COUNT(*) FROM welfare_policies WHERE LENGTH(title) > 100')
        long_title_count = self.cursor.fetchone()[0]
        print(f"  제목이 너무 긴 정책 (100자 이상): {long_title_count}개")
        
        # 너무 긴 조건/혜택 (1000자 이상)
        self.cursor.execute('SELECT COUNT(*) FROM welfare_policies WHERE LENGTH(conditions) > 1000 OR LENGTH(benefits) > 1000')
        long_content_count = self.cursor.fetchone()[0]
        print(f"  내용이 너무 긴 정책 (1000자 이상): {long_content_count}개")
    
    def _validate_duplicates(self):
        """중복 데이터 검증"""
        print("\n🔍 중복 데이터 검증:")
        
        # 제목 기준 중복
        self.cursor.execute('''
            SELECT title, COUNT(*) as count 
            FROM welfare_policies 
            GROUP BY title 
            HAVING count > 1
            ORDER BY count DESC
        ''')
        duplicate_titles = self.cursor.fetchall()
        print(f"  제목 중복 정책: {len(duplicate_titles)}개")
        
        # URL 기준 중복
        self.cursor.execute('''
            SELECT url, COUNT(*) as count 
            FROM welfare_policies 
            GROUP BY url 
            HAVING count > 1
            ORDER BY count DESC
        ''')
        duplicate_urls = self.cursor.fetchall()
        print(f"  URL 중복 정책: {len(duplicate_urls)}개")
        
        if duplicate_titles or duplicate_urls:
            print("  ⚠️ 중복 데이터가 발견되었습니다.")
        else:
            print("  ✅ 중복 데이터가 없습니다.")
    
    def _validate_urls(self):
        """URL 유효성 검증"""
        print("\n🔍 URL 유효성 검증:")
        
        # HTTP/HTTPS 프로토콜 확인
        self.cursor.execute('''
            SELECT COUNT(*) FROM welfare_policies 
            WHERE url NOT LIKE 'http%'
        ''')
        invalid_protocol_count = self.cursor.fetchone()[0]
        print(f"  HTTP/HTTPS가 아닌 URL: {invalid_protocol_count}개")
        
        # 도메인별 분포
        self.cursor.execute('''
            SELECT 
                CASE 
                    WHEN url LIKE '%seoul%' THEN '서울시'
                    WHEN url LIKE '%incheon%' THEN '인천시'
                    WHEN url LIKE '%gg.go.kr%' THEN '경기도'
                    WHEN url LIKE '%bokjiro%' THEN '복지로'
                    ELSE '기타'
                END as domain,
                COUNT(*) as count
            FROM welfare_policies 
            GROUP BY domain 
            ORDER BY count DESC
        ''')
        domain_stats = self.cursor.fetchall()
        print(f"  도메인별 분포:")
        for domain, count in domain_stats:
            print(f"    {domain}: {count}개")
    
    def _validate_age_ranges(self):
        """나이 범위 검증"""
        print("\n🔍 나이 범위 검증:")
        
        # 나이 정보가 없는 정책
        self.cursor.execute('SELECT COUNT(*) FROM welfare_policies WHERE age_min = -1 OR age_max = -1')
        no_age_count = self.cursor.fetchone()[0]
        print(f"  나이 정보 없는 정책: {no_age_count}개")
        
        # 청년 대상 정책 (20-39세)
        self.cursor.execute('''
            SELECT COUNT(*) FROM welfare_policies 
            WHERE (age_min >= 20 AND age_max <= 39) 
            OR (age_min <= 20 AND age_max >= 20)
            OR (age_min <= 39 AND age_max >= 39)
        ''')
        youth_count = self.cursor.fetchone()[0]
        print(f"  청년 대상 정책 (20-39세): {youth_count}개")
        
        # 특정 나이대별 정책 수
        age_ranges = [
            (0, 19, "10대"),
            (20, 29, "20대"),
            (30, 39, "30대"),
            (40, 100, "40대 이상")
        ]
        
        for min_age, max_age, label in age_ranges:
            self.cursor.execute('''
                SELECT COUNT(*) FROM welfare_policies 
                WHERE (age_min <= ? AND age_max >= ?) 
                OR (age_min >= ? AND age_max <= ?)
                OR (age_min <= ? AND age_max >= ?)
            ''', (max_age, min_age, min_age, max_age, min_age, max_age))
            count = self.cursor.fetchone()[0]
            print(f"  {label} 대상 정책: {count}개")
    
    def generate_report(self):
        """검증 보고서 생성"""
        print("\n📋 검증 보고서 생성 중...")
        
        report = {
            "검증_날짜": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "DB_경로": self.db_path,
            "기본_통계": {},
            "품질_검증": {},
            "권장사항": []
        }
        
        # 기본 통계 수집
        self.cursor.execute('SELECT COUNT(*) FROM welfare_policies')
        total_count = self.cursor.fetchone()[0]
        report["기본_통계"]["총_정책_수"] = total_count
        
        # 지역별 통계
        self.cursor.execute('SELECT region, COUNT(*) FROM welfare_policies GROUP BY region')
        region_stats = dict(self.cursor.fetchall())
        report["기본_통계"]["지역별_분포"] = region_stats
        
        # 품질 검증 결과
        self.cursor.execute('SELECT COUNT(*) FROM welfare_policies WHERE title IS NULL OR title = ""')
        empty_title_count = self.cursor.fetchone()[0]
        report["품질_검증"]["제목_누락"] = empty_title_count
        
        self.cursor.execute('SELECT COUNT(*) FROM welfare_policies WHERE url IS NULL OR url = ""')
        empty_url_count = self.cursor.fetchone()[0]
        report["품질_검증"]["URL_누락"] = empty_url_count
        
        # 권장사항
        if empty_title_count > 0:
            report["권장사항"].append("제목이 누락된 정책을 수정하세요.")
        if empty_url_count > 0:
            report["권장사항"].append("URL이 누락된 정책을 수정하세요.")
        if total_count < 50:
            report["권장사항"].append("더 많은 정책 데이터를 수집하세요.")
        
        # 보고서 저장
        report_path = os.path.join(os.path.dirname(self.db_path), "validation_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 검증 보고서 저장: {report_path}")
        return report
    
    def close_db(self):
        """DB 연결 종료"""
        if self.conn:
            self.conn.close()

def main():
    db_path = r'C:\B조\DB\ibm_data.db'
    
    if not os.path.exists(db_path):
        print(f"❌ DB 파일이 없습니다: {db_path}")
        return
    
    validator = WelfareDataValidator(db_path)
    
    try:
        validator.connect_db()
        validator.validate_data_quality()
        report = validator.generate_report()
        
        print(f"\n🎉 데이터 검증 완료!")
        print(f"총 정책 수: {report['기본_통계']['총_정책_수']}개")
        print(f"권장사항: {len(report['권장사항'])}개")
        
    except Exception as e:
        print(f"❌ 데이터 검증 실패: {e}")
        
    finally:
        validator.close_db()

if __name__ == "__main__":
    main() 