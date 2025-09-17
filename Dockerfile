FROM python:3.11-slim

WORKDIR /app

# Копируем код и зависимости
COPY main.py config.ini requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]