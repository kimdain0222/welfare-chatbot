from flask import Flask, jsonify, request
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app, origins=['https://welfarechatbot02.netlify.app', 'http://localhost:3000'])  # React에서 API 호출할 수 있도록 CORS 설정

@app.route('/api/health', methods=['GET'])
def health_check():
    """서버 상태 확인"""
    return jsonify({"status": "healthy", "message": "API 서버가 정상 작동 중입니다!"})

@app.route('/api/policies/region/<region>', methods=['GET'])
def get_policies_by_region(region):
    """지역별 정책 조회 (테스트용)"""
    # 테스트용 정책 데이터
    test_policies = {
        "seoul": [
            {
                "id": 1,
                "title": "서울 청년 주거 지원",
                "benefits": "월 30만원 주거비 지원",
                "conditions": "20-30대 청년, 소득 기준 하위 80%",
                "application_period": "2024.01.01 ~ 2024.12.31",
                "url": "https://example.com/seoul-housing"
            },
            {
                "id": 2,
                "title": "서울 청년 취업 지원",
                "benefits": "취업 성공 시 100만원 지원",
                "conditions": "25-35세 청년, 실업 상태",
                "application_period": "2024.01.01 ~ 2024.12.31",
                "url": "https://example.com/seoul-employment"
            }
        ],
        "gyeonggi": [
            {
                "id": 3,
                "title": "경기 청년 창업 지원",
                "benefits": "창업 자금 최대 500만원 지원",
                "conditions": "20-40대 청년, 창업 계획서 제출",
                "application_period": "2024.01.01 ~ 2024.12.31",
                "url": "https://example.com/gyeonggi-startup"
            }
        ],
        "incheon": [
            {
                "id": 4,
                "title": "인천 청년 문화 지원",
                "benefits": "문화 활동비 월 10만원 지원",
                "conditions": "20-30대 청년, 인천 거주",
                "application_period": "2024.01.01 ~ 2024.12.31",
                "url": "https://example.com/incheon-culture"
            }
        ]
    }
    
    policies = test_policies.get(region, [])
    
    return jsonify({
        "success": True,
        "region": region,
        "count": len(policies),
        "policies": policies
    })

@app.route('/api/policies', methods=['GET'])
def get_all_policies():
    """모든 정책 조회 (테스트용)"""
    all_policies = []
    test_policies = {
        "seoul": [
            {
                "id": 1,
                "title": "서울 청년 주거 지원",
                "benefits": "월 30만원 주거비 지원",
                "conditions": "20-30대 청년, 소득 기준 하위 80%",
                "application_period": "2024.01.01 ~ 2024.12.31",
                "url": "https://example.com/seoul-housing"
            }
        ],
        "gyeonggi": [
            {
                "id": 2,
                "title": "경기 청년 창업 지원",
                "benefits": "창업 자금 최대 500만원 지원",
                "conditions": "20-40대 청년, 창업 계획서 제출",
                "application_period": "2024.01.01 ~ 2024.12.31",
                "url": "https://example.com/gyeonggi-startup"
            }
        ],
        "incheon": [
            {
                "id": 3,
                "title": "인천 청년 문화 지원",
                "benefits": "문화 활동비 월 10만원 지원",
                "conditions": "20-30대 청년, 인천 거주",
                "application_period": "2024.01.01 ~ 2024.12.31",
                "url": "https://example.com/incheon-culture"
            }
        ]
    }
    
    for region, policies in test_policies.items():
        for policy in policies:
            policy["region"] = region
            all_policies.append(policy)
    
    return jsonify({
        "success": True,
        "count": len(all_policies),
        "policies": all_policies
    })

if __name__ == '__main__':
    print("🚀 복지정책 API 서버 시작...")
    print("📊 사용 가능한 엔드포인트:")
    print("   GET /api/health - 서버 상태 확인")
    print("   GET /api/policies - 모든 정책 조회")
    print("   GET /api/policies/region/<region> - 지역별 정책 조회")
    print("\n🌐 서버 주소: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 