import json
import sqlite3
import os

# 1. JSON 파일 경로 (윈도우 경로는 raw string 추천)
json_path = r'C:\Users\pst00\Downloads\서울_크롤링(11개)_완성.json'

# 파일 존재 여부 체크
if not os.path.exists(json_path):
    raise FileNotFoundError(f"JSON 파일이 없습니다: {json_path}")

# 2. JSON 데이터 읽기
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"총 정책 개수: {len(data)}")
print(f"첫번째 정책 예시: {data[0]}")

# 3. SQLite DB 연결 및 테이블 생성
conn = sqlite3.connect(r'C:\sqlite\ok\ibm_data.db')
cur = conn.cursor()


# 4. 데이터 삽입
for i, item in enumerate(data):
    try:
        # region이 리스트면 문자열로 변환, 아니면 문자열 그대로
        region = ', '.join(item['region']) if isinstance(item.get('region'), list) else str(item.get('region', ''))

        # age_range가 리스트면 최소/최대 추출, 아니면 기본값 -1 설정
        age_range = item.get('age_range', [])
        if isinstance(age_range, list) and len(age_range) > 0:
            age_min = min(age_range)
            age_max = max(age_range)
        else:
            age_min = -1
            age_max = -1
        
        # 기타 필드는 없으면 빈 문자열로 처리
        cur.execute('''
            INSERT INTO policies(title, url, region, age_min, age_max, application_period, conditions, benefits)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item.get('title', ''),
            item.get('url', ''),
            region,
            age_min,
            age_max,
            item.get('application_period', ''),
            item.get('conditions', ''),
            item.get('benefits', '')
        ))
    except Exception as e:
        print(f"Error inserting item {i}: {e}")

# 5. 커밋하고 연결 종료
conn.commit()

# 6. 저장 확인용 조회 출력
cur.execute('SELECT COUNT(*) FROM policies')
count = cur.fetchone()[0]
print(f"DB에 저장된 정책 개수: {count}")

cur.execute('SELECT * FROM policies LIMIT 3')
rows = cur.fetchall()
for row in rows:
    print(row)

conn.close()
