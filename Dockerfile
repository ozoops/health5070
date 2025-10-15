FROM python:3.10-slim

# 시스템 의존성을 한 레이어에서 처리
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    ffmpeg \
    fonts-nanum \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 폰트 캐시 업데이트
RUN fc-cache -fv

WORKDIR /app

# requirements 복사 및 설치 (캐시 레이어)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# matplotlib 폰트 캐시 삭제
RUN rm -rf /root/.cache/matplotlib

# 앱 코드 복사
COPY . .



EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]