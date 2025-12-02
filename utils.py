"""유틸리티 함수들"""
import pandas as pd
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: plotly could not be imported: {e}")
    print("Please install plotly: pip install plotly>=5.18.0")
    PLOTLY_AVAILABLE = False
    px = None
    go = None
from collections import Counter
import json
import os

def load_data():
    """데이터 로드"""
    university_df = pd.read_csv('data/university_info.csv')
    major_df = pd.read_csv('data/major_info.csv')
    admission_df = pd.read_csv('data/admission_rate.csv')
    return university_df, major_df, admission_df

def analyze_question(question):
    """질문 분석 및 카테고리 분류"""
    keywords = {
        '내신': ['내신', '성적', '갈 수', '들어갈', '입학 가능', '입학', '가능한', '지원', '합격', '입시', '등급으로', '등급으로는', '내신으로', '성적으로'],
        '대학': ['대학', '학교', '캠퍼스'],
        '학과': ['학과', '전공', '과'],
        '진학': ['진학', '입시', '합격'],
        '취업': ['취업', '연봉', '취직', '직업'],
        '추천': ['추천', '어디', '좋은']
    }
    
    # 내신 관련 키워드가 우선순위가 높음
    for category, words in keywords.items():
        if any(word in question for word in words):
            return category
    return None

def extract_grade(question):
    """질문에서 등급 정보 추출"""
    import re
    # 등급 패턴 찾기 (예: 1.5등급, 2등급, 3.2등급 등)
    patterns = [
        r'(\d+\.?\d*)\s*등급',
        r'등급\s*(\d+\.?\d*)',
        r'내신\s*(\d+\.?\d*)',
        r'성적\s*(\d+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, question)
        if match:
            try:
                return float(match.group(1))
            except:
                pass
    return None

def get_response(question, university_df, major_df, admission_df):
    """질문에 대한 응답 생성"""
    category = analyze_question(question)
    
    if category == '내신':
        # 등급 추출
        user_grade = extract_grade(question)
        
        if user_grade is None:
            response = "내신 등급을 알려주시면 갈 수 있는 대학을 추천해드릴 수 있습니다.\n예: '내신 2.5등급으로 갈 수 있는 대학 알려줘'"
            return response, False, None
        
        # 특정 대학에 들어갈 수 있는지 확인
        for _, row in university_df.iterrows():
            if row['대학명'] in question:
                required_grade = row['평균등급']
                if user_grade <= required_grade + 0.3:  # 0.3등급 여유
                    response = f"""
**{row['대학명']}** 입학 가능성 분석:

📊 **내신 등급**: {user_grade}등급
🎯 **필요 등급**: {required_grade}등급
✅ **결과**: 입학 가능성이 있습니다! (필요 등급보다 {'높습니다' if user_grade < required_grade else '비슷합니다'})

📍 **위치**: {row['위치']}
💼 **취업률**: {row['취업률']}%
🎓 **주요학과**: {row['주요학과']}
"""
                else:
                    response = f"""
**{row['대학명']}** 입학 가능성 분석:

📊 **내신 등급**: {user_grade}등급
🎯 **필요 등급**: {required_grade}등급
❌ **결과**: 입학이 어려울 수 있습니다. (필요 등급보다 {user_grade - required_grade:.1f}등급 낮습니다)

다른 대학을 추천해드릴까요?
"""
                return response, True, 'grade_analysis'
        
        # 내신으로 갈 수 있는 대학 추천
        # 인서울 대학만 필터링
        seoul_universities = university_df[university_df['위치'] == '서울'].copy()
        # 내신보다 높은 등급이 필요한 대학 제외 (0.3등급 여유)
        available_universities = seoul_universities[
            seoul_universities['평균등급'] >= user_grade - 0.3
        ].sort_values('평균등급')
        
        if len(available_universities) > 0:
            response = f"""
**내신 {user_grade}등급으로 갈 수 있는 인서울 대학교** 추천:

"""
            for idx, (_, row) in enumerate(available_universities.head(10).iterrows(), 1):
                # 안전성 표시
                if user_grade <= row['평균등급']:
                    safety = "✅ 안전"
                elif user_grade <= row['평균등급'] + 0.2:
                    safety = "⚠️ 적정"
                else:
                    safety = "🔶 도전"
                
                response += f"{idx}. **{row['대학명']}** {safety}\n"
                response += f"   - 필요 등급: {row['평균등급']}등급\n"
                response += f"   - 취업률: {row['취업률']}%\n"
                response += f"   - 주요학과: {row['주요학과']}\n\n"
            
            response += f"📊 총 **{len(available_universities)}개** 대학에 지원 가능합니다.\n\n"
            response += "💡 **안내**: 등급은 참고용이며, 실제 입시 결과는 변동될 수 있습니다."
            return response, True, 'grade_recommendation'
        else:
            response = f"내신 {user_grade}등급으로는 인서울 대학 입학이 어려울 수 있습니다. 다른 지역 대학이나 전문대를 고려해보시기 바랍니다."
            return response, False, None
    
    elif category == '대학':
        # 특정 대학 검색
        for _, row in university_df.iterrows():
            if row['대학명'] in question:
                response = f"""
**{row['대학명']}** 정보를 알려드리겠습니다.

📍 **위치**: {row['위치']}
📅 **설립연도**: {row['설립연도']}년
👥 **학생수**: {row['학생수']:,}명
🎓 **주요학과**: {row['주요학과']}
📊 **평균등급**: {row['평균등급']}등급
💼 **취업률**: {row['취업률']}%
"""
                return response, True, 'university'
        
        # 대학 키워드가 있지만 특정 대학을 찾지 못한 경우
        if any(word in question for word in ['인서울', '서울', '대학', '학교']):
            response = "인서울 주요 대학교 정보를 보유하고 있습니다. 어떤 대학교에 대해 궁금하신가요?"
            return response, True, 'university_list'
        
        # 일반 대학 정보
        response = "대한민국 주요 대학교 정보를 보유하고 있습니다."
        return response, True, 'university_list'
    
    elif category == '학과':
        # 특정 학과 검색
        for _, row in major_df.iterrows():
            if row['학과명'] in question or row['분야'] in question:
                response = f"""
**{row['학과명']}** 정보를 알려드리겠습니다.

📚 **분야**: {row['분야']}
💰 **평균연봉**: {row['평균연봉']:,}만원
💼 **취업률**: {row['취업률']}%
🎯 **필요역량**: {row['필요역량']}
✨ **추천적성**: {row['추천적성']}
"""
                return response, True, 'major'
        
        # 학과 키워드가 있지만 특정 학과를 찾지 못한 경우
        if any(word in question for word in ['학과', '전공', '과']):
            response = "다양한 학과의 정보를 보유하고 있습니다. 어떤 학과에 대해 궁금하신가요?"
            return response, True, 'major_list'
        
        # 일반 학과 정보
        response = "다양한 학과의 정보를 보유하고 있습니다."
        return response, True, 'major_list'
    
    elif category == '진학':
        response = f"""
**대학 진학률** 정보를 알려드리겠습니다.

최근 5년간 대학 진학률 추이를 확인하실 수 있습니다.
- 2023년 전체 진학률: {admission_df.iloc[-1]['대학진학률']}%
- 4년제 진학률: {admission_df.iloc[-1]['4년제진학률']}%
- 전문대 진학률: {admission_df.iloc[-1]['전문대진학률']}%
"""
        return response, True, 'admission'
    
    elif category == '취업':
        response = """
**취업률** 정보를 알려드리겠습니다.

학과별 취업률 및 평균 연봉 정보를 확인하실 수 있습니다.
"""
        return response, True, 'employment'
    
    else:
        response = "죄송합니다 이 질문을 찾지 못하겠습니다 죄송합니다"
        return response, False, None

def create_visualization(vis_type, university_df, major_df, admission_df):
    """시각화 생성"""
    if not PLOTLY_AVAILABLE:
        # plotly가 없으면 DataFrame 반환
        if vis_type in ['university', 'major', 'admission', 'employment']:
            return None
        return None
    
    if vis_type == 'university':
        # 대학별 취업률 비교
        fig = px.bar(university_df.sort_values('취업률', ascending=False),
                     x='대학명', y='취업률',
                     title='대학별 취업률 비교',
                     labels={'취업률': '취업률 (%)', '대학명': '대학교'},
                     color='취업률',
                     color_continuous_scale='Blues')
        fig.update_layout(xaxis_tickangle=-45)
        return fig
    
    elif vis_type == 'university_list':
        # 대학 정보 테이블
        return university_df
    
    elif vis_type == 'major':
        # 학과별 연봉 vs 취업률
        fig = px.scatter(major_df, x='평균연봉', y='취업률',
                        text='학과명', size='평균연봉',
                        title='학과별 평균연봉 vs 취업률',
                        labels={'평균연봉': '평균연봉 (만원)', '취업률': '취업률 (%)'},
                        color='분야')
        fig.update_traces(textposition='top center')
        return fig
    
    elif vis_type == 'major_list':
        # 학과 정보 테이블
        return major_df
    
    elif vis_type == 'admission':
        # 진학률 추이
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=admission_df['연도'], y=admission_df['대학진학률'],
                                mode='lines+markers', name='전체 진학률',
                                line=dict(color='blue', width=3)))
        fig.add_trace(go.Scatter(x=admission_df['연도'], y=admission_df['4년제진학률'],
                                mode='lines+markers', name='4년제',
                                line=dict(color='green', width=2)))
        fig.add_trace(go.Scatter(x=admission_df['연도'], y=admission_df['전문대진학률'],
                                mode='lines+markers', name='전문대',
                                line=dict(color='orange', width=2)))
        fig.update_layout(title='연도별 대학 진학률 추이',
                         xaxis_title='연도',
                         yaxis_title='진학률 (%)')
        return fig
    
    elif vis_type == 'employment':
        # 학과별 취업률
        fig = px.bar(major_df.sort_values('취업률', ascending=True),
                     x='취업률', y='학과명',
                     orientation='h',
                     title='학과별 취업률',
                     labels={'취업률': '취업률 (%)', '학과명': '학과'},
                     color='취업률',
                     color_continuous_scale='Greens')
        return fig
    
    elif vis_type == 'grade_analysis':
        # 특정 대학의 등급 정보 (단일 대학이므로 테이블로 표시)
        return None  # 이미 텍스트로 표시됨
    
    elif vis_type == 'grade_recommendation':
        # 내신으로 갈 수 있는 대학 목록 (이미 텍스트로 표시됨)
        # 추가 시각화가 필요하면 여기에 구현
        return None
    
    return None

def save_chat_history(chat_item):
    """대화 기록 저장"""
    history_file = 'data/chat_history.json'
    
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []
    
    history.append(chat_item)
    
    # 최근 50개만 유지
    history = history[-50:]
    
    os.makedirs('data', exist_ok=True)
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_chat_history():
    """대화 기록 로드"""
    history_file = 'data/chat_history.json'
    
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def get_popular_topics():
    """인기 검색 주제 반환 (주제 기반)"""
    history = load_chat_history()
    
    if not history:
        return []
    
    # 주제 키워드 매핑
    topic_keywords = {
        '내신 기반 추천': ['내신', '등급', '성적', '갈 수', '들어갈', '입학', '합격 가능'],
        '대학 정보': ['대학', '학교', '캠퍼스', '서울대', '연세대', '고려대'],
        '학과 정보': ['학과', '전공', '과', '컴퓨터', '의학', '경영', '공학'],
        '진학률': ['진학', '입시', '합격', '진학률'],
        '취업률': ['취업', '연봉', '취직', '직업', '취업률'],
        '추천': ['추천', '어디', '좋은', '어떤']
    }
    
    # 각 주제별 빈도 계산
    topic_counts = Counter()
    
    for item in history:
        if 'question' in item:
            question = item['question']
            for topic, keywords in topic_keywords.items():
                if any(keyword in question for keyword in keywords):
                    topic_counts[topic] += 1
    
    # 빈도순으로 정렬하여 반환
    popular = topic_counts.most_common(5)
    
    return popular

def summarize_chat(question, response):
    """대화 내용 요약 (주제 기반)"""
    # 주제 추출
    if any(word in question for word in ['대학', '학교', '서울대', '연세대', '고려대']):
        # 대학명 추출 시도
        for word in ['서울대', '연세대', '고려대', '카이스트', '포스텍', '성균관', '한양', '서강', '중앙', '경희']:
            if word in question:
                return f"{word}학교 정보"
        return "대학 정보 문의"
    
    elif any(word in question for word in ['학과', '전공', '컴퓨터', '의학', '경영', '공학']):
        # 학과명 추출 시도
        for word in ['컴퓨터공학', '의예과', '경영학', '전기공학', '기계공학', '경제학', '법학', '심리학', '간호학', '건축학', '디자인', '화학공학', '생명과학', '교육학']:
            if word in question:
                return f"{word} 정보"
        return "학과 정보 문의"
    
    elif any(word in question for word in ['내신', '등급', '성적', '갈 수', '들어갈', '입학', '합격 가능']):
        return "내신 기반 대학 추천"
    
    elif any(word in question for word in ['진학', '입시', '합격']):
        return "진학률 문의"
    
    elif any(word in question for word in ['취업', '연봉', '취직']):
        return "취업 정보 문의"
    
    elif any(word in question for word in ['추천', '어디', '좋은']):
        return "추천 문의"
    
    else:
        # 기본 요약
        if len(question) > 25:
            return question[:25] + "..."
        return question

# 적성검사 질문 및 분석
APTITUDE_QUESTIONS = [
    {
        "id": 1,
        "question": "문제를 해결할 때 어떤 방식을 선호하나요?",
        "options": {
            "A": "논리적이고 체계적으로 분석한다",
            "B": "창의적이고 독창적인 방법을 찾는다",
            "C": "다른 사람들과 협력하여 해결한다",
            "D": "실용적이고 효율적인 방법을 선택한다"
        },
        "type": {"A": "탐구형", "B": "예술형", "C": "사회형", "D": "현실형"}
    },
    {
        "id": 2,
        "question": "여가 시간에 무엇을 하는 것을 좋아하나요?",
        "options": {
            "A": "책을 읽거나 새로운 것을 배운다",
            "B": "그림을 그리거나 음악을 듣는다",
            "C": "친구들을 만나 이야기를 나눈다",
            "D": "운동이나 실용적인 활동을 한다"
        },
        "type": {"A": "탐구형", "B": "예술형", "C": "사회형", "D": "현실형"}
    },
    {
        "id": 3,
        "question": "학교에서 어떤 과목을 좋아하나요?",
        "options": {
            "A": "수학, 과학",
            "B": "미술, 음악",
            "C": "국어, 사회",
            "D": "체육, 기술"
        },
        "type": {"A": "탐구형", "B": "예술형", "C": "사회형", "D": "현실형"}
    },
    {
        "id": 4,
        "question": "미래의 직업을 선택할 때 가장 중요한 것은?",
        "options": {
            "A": "전문성과 지적 성취감",
            "B": "창의성과 자유로움",
            "C": "사람들을 돕고 사회에 기여",
            "D": "안정성과 실질적인 보상"
        },
        "type": {"A": "탐구형", "B": "예술형", "C": "사회형", "D": "현실형"}
    },
    {
        "id": 5,
        "question": "팀 프로젝트에서 어떤 역할을 맡고 싶나요?",
        "options": {
            "A": "자료 조사 및 분석",
            "B": "디자인 및 창작",
            "C": "팀원 조율 및 발표",
            "D": "실행 및 제작"
        },
        "type": {"A": "탐구형", "B": "예술형", "C": "사회형", "D": "현실형"}
    },
    {
        "id": 6,
        "question": "새로운 기술이나 지식을 배울 때 어떤 방식을 선호하나요?",
        "options": {
            "A": "이론을 먼저 학습하고 실험으로 검증한다",
            "B": "직접 시도해보며 창의적으로 응용한다",
            "C": "다른 사람들과 함께 배우고 공유한다",
            "D": "실용적인 목적에 맞게 단계적으로 학습한다"
        },
        "type": {"A": "탐구형", "B": "예술형", "C": "사회형", "D": "현실형"}
    },
    {
        "id": 7,
        "question": "스트레스를 받을 때 어떻게 해소하나요?",
        "options": {
            "A": "혼자 조용히 생각하고 분석한다",
            "B": "예술 활동이나 창작 활동을 한다",
            "C": "친구나 가족과 대화하며 공감을 받는다",
            "D": "운동이나 실용적인 활동으로 몸을 움직인다"
        },
        "type": {"A": "탐구형", "B": "예술형", "C": "사회형", "D": "현실형"}
    },
    {
        "id": 8,
        "question": "성공한 사람의 모습을 상상할 때 어떤 모습인가요?",
        "options": {
            "A": "전문 분야에서 최고의 전문가",
            "B": "독창적이고 창의적인 작품을 만드는 사람",
            "C": "많은 사람들에게 도움을 주는 사람",
            "D": "안정적이고 실질적인 성과를 내는 사람"
        },
        "type": {"A": "탐구형", "B": "예술형", "C": "사회형", "D": "현실형"}
    },
    {
        "id": 9,
        "question": "어떤 환경에서 일하는 것을 선호하나요?",
        "options": {
            "A": "조용하고 집중할 수 있는 연구실이나 사무실",
            "B": "자유롭고 창의적인 작업 공간",
            "C": "사람들과 소통하며 협력하는 공간",
            "D": "구체적인 작업을 할 수 있는 현장"
        },
        "type": {"A": "탐구형", "B": "예술형", "C": "사회형", "D": "현실형"}
    },
    {
        "id": 10,
        "question": "미래에 가장 중요하게 생각하는 가치는?",
        "options": {
            "A": "지식과 진실 추구",
            "B": "창의성과 독창성",
            "C": "타인에 대한 배려와 봉사",
            "D": "안정성과 실용성"
        },
        "type": {"A": "탐구형", "B": "예술형", "C": "사회형", "D": "현실형"}
    }
]

def analyze_aptitude(answers):
    """적성검사 결과 분석"""
    type_counts = Counter()
    
    for answer in answers:
        q_id = answer['question_id']
        choice = answer['choice']
        
        question = next(q for q in APTITUDE_QUESTIONS if q['id'] == q_id)
        personality_type = question['type'][choice]
        type_counts[personality_type] += 1
    
    # 가장 많이 나온 유형
    primary_type = type_counts.most_common(1)[0][0]
    
    # 유형별 설명
    type_descriptions = {
        "탐구형": {
            "description": "논리적이고 분석적인 사고를 선호하며, 새로운 지식을 탐구하는 것을 즐깁니다.",
            "majors": ["컴퓨터공학과", "전기공학과", "화학공학과", "생명과학과"],
            "careers": ["연구원", "프로그래머", "데이터 분석가", "과학자", "엔지니어", "의사", "약사", "수학자", "물리학자", "화학자"]
        },
        "예술형": {
            "description": "창의적이고 독창적인 표현을 중시하며, 미적 감각이 뛰어납니다.",
            "majors": ["산업디자인과", "건축학과"],
            "careers": ["디자이너", "건축가", "예술가", "작가", "음악가", "영화감독", "사진작가", "애니메이터", "일러스트레이터", "패션디자이너"]
        },
        "사회형": {
            "description": "사람들과의 소통을 즐기며, 타인을 돕는 것에서 보람을 느낍니다.",
            "majors": ["심리학과", "간호학과", "교육학과"],
            "careers": ["교사", "간호사", "상담사", "사회복지사", "심리상담사", "의사", "언어치료사", "직업상담사", "인사담당자", "마케터"]
        },
        "현실형": {
            "description": "실용적이고 구체적인 활동을 선호하며, 손으로 만들거나 조작하는 것을 좋아합니다.",
            "majors": ["기계공학과", "건축학과", "간호학과"],
            "careers": ["기계공학자", "건축가", "전기기사", "자동차정비사", "조선공", "건설현장관리자", "항공정비사", "산업안전관리자", "토목기사", "환경기사"]
        }
    }
    
    result = {
        "primary_type": primary_type,
        "counts": dict(type_counts),
        "description": type_descriptions[primary_type]["description"],
        "recommended_majors": type_descriptions[primary_type]["majors"],
        "recommended_careers": type_descriptions[primary_type]["careers"]
    }
    
    return result

