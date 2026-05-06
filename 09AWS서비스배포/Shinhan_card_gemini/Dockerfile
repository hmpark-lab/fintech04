FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# lxml 빌드/동작 관련 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# 최소 의존성만 설치
RUN pip install --upgrade pip

COPY gemini_req.txt /app/gemini_req.txt

# 현재 req 파일이 너무 무거워서 배포용 최소 패키지만 별도 설치
RUN pip install \
    gradio==5.23.3 \
    pandas==2.2.3 \
    requests==2.32.5 \
    beautifulsoup4==4.14.3 \
    python-dotenv==1.2.2 \
    google-genai==1.68.0 \
    lxml

COPY app.py /app/app.py
COPY .gemini_env /app/.gemini_env

EXPOSE 7860

CMD ["python", "app.py"]