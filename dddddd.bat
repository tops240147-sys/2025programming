@echo off
echo ====================================
echo  대학 진로 상담 시스템 시작
echo ====================================
echo.

REM 필요한 패키지 설치
echo 필요한 패키지를 설치합니다...
pip install -r requirements.txt

echo.
echo 애플리케이션을 실행합니다...
streamlit run app.py

pause

