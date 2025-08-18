FROM python:3.9-slim

WORKDIR /app

RUN pip install fastapi uvicorn sqlalchemy psycopg2-binary

COPY simple_app.py .

ENV PORT=8000
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "simple_app.py"]