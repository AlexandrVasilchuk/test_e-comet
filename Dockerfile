FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0"]