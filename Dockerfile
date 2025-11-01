FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model (optional at build time - can be done at runtime if you prefer)
RUN python -m spacy download en_core_web_sm

COPY . .

ENV PORT=5002

EXPOSE 5002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5002", "--proxy-headers"]
