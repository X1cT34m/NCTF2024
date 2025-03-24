FROM python:3.11-slim-bookworm

RUN pip install fastapi uvicorn sqlmap

COPY ./src/ /app/

WORKDIR /app/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]