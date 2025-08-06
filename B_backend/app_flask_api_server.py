from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import json
import os

app = Flask(__name__)
CORS(app)  # React에서 API 호출할 수 있도록 CORS 설정

# ------------------ 🔹 DB 절대 경로 설정 ------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "welfare_policies.db")  # 같은 폴더 안에 DB가 있어야 함
# --------------------------------------------------------

def get_db_connection():
    """데이터베이스 연결"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 결과 반환
    return conn

@app.route('/api/health', methods=['GET'])
def health_check():
    """서버 상태 확인"""
    return jsonify({"status": "healthy", "message": "API 서버가 정상 작동 중입니다!"})

@app.route('/api/policies', methods=['GET'])
def get_all_policies():
    """모든 정책 조회"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, url, region, age_range, application_period, conditions, benefits
            FROM welfare_policies
            ORDER BY region, title
        ''')
        
        policies = []
        for row in cursor.fetchall():
            policy = dict(row)
            if policy['age_range']:
                policy['age_range'] = json.loads(policy['age_range'])
            else:
                policy['age_range'] = []
            policies.append(policy)
        
        conn.close()
        return jsonify({
            "success": True,
            "count": len(policies),
            "policies": policies
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/policies/region/<region>', methods=['GET'])
def get_policies_by_region(region):
    """지역별 정책 조회"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, url, region, age_range, application_period, conditions, benefits
            FROM welfare_policies
            WHERE region = ?
            ORDER BY title
        ''', (region,))
        
        policies = []
        for row in cursor.fetchall():
            policy = dict(row)
            if policy['age_range']:
                policy['age_range'] = json.loads(policy['age_range'])
            else:
                policy['age_range'] = []
            policies.append(policy)
        
        conn.close()
        return jsonify({
            "success": True,
            "region": region,
            "count": len(policies),
            "policies": policies
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/policies/search', methods=['GET'])
def search_policies():
    """키워드로 정책 검색"""
    keyword = request.args.get('keyword', '')
    region = request.args.get('region', '')
    age = request.args.get('age', '')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT id, title, url, region, age_range, application_period, conditions, benefits
            FROM welfare_policies
            WHERE 1=1
        '''
        params = []
        
        if keyword:
            query += ''' AND (title LIKE ? OR benefits LIKE ? OR conditions LIKE ?)'''
            params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
        
        if region:
            query += ''' AND region = ?'''
            params.append(region)
        
        if age:
            query += ''' AND age_range LIKE ?'''
            params.append(f'%{age}%')
        
        query += ''' ORDER BY region, title'''
        
        cursor.execute(query, params)
        
        policies = []
        for row in cursor.fetchall():
            policy = dict(row)
            if policy['age_range']:
                policy['age_range'] = json.loads(policy['age_range'])
            else:
                policy['age_range'] = []
            policies.append(policy)
        
        conn.close()
        return jsonify({
            "success": True,
            "keyword": keyword,
            "region": region,
            "age": age,
            "count": len(policies),
            "policies": policies
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/regions', methods=['GET'])
def get_regions():
    """사용 가능한 지역 목록 조회"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT DISTINCT region FROM welfare_policies ORDER BY region')
        regions = [row['region'] for row in cursor.fetchall()]
        
        conn.close()
        return jsonify({
            "success": True,
            "regions": regions
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """데이터베이스 통계"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM welfare_policies')
        total = cursor.fetchone()['total']
        
        cursor.execute('SELECT region, COUNT(*) as count FROM welfare_policies GROUP BY region')
        region_stats = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return jsonify({
            "success": True,
            "total_policies": total,
            "region_stats": region_stats
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 복지정책 API 서버 시작...")
    print("📊 사용 가능한 엔드포인트:")
    print("   GET /api/health - 서버 상태 확인")
    print("   GET /api/policies - 모든 정책 조회")
    print("   GET /api/policies/region/<region> - 지역별 정책 조회")
    print("   GET /api/policies/search?keyword=<keyword>&region=<region>&age=<age> - 정책 검색")
    print("   GET /api/regions - 지역 목록 조회")
    print("   GET /api/stats - 통계 정보")
    print("\n🌐 서버 주소: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
