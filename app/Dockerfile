# Local development only. On AWS the app is installed by user data, not Docker.
#   docker build -t mini-hotstar app
#   docker run --rm -p 8000:8000 mini-hotstar
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

RUN useradd --system --no-create-home hotstar
USER hotstar

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
