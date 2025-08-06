FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY ./pyproject.toml .
COPY /.uv.lock .

RUN uv sync --no-deps

COPY . .

EXPOSE 9413

CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9413" ]
