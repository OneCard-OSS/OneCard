FROM python:3.12

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY ./pyproject.toml .
COPY ./uv.lock .

RUN uv sync --no-dev --verbose

COPY . .

EXPOSE 9413

CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9413" ]
