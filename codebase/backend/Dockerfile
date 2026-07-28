FROM python:3.13-slim AS runtime

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM runtime AS test

RUN pip install --no-cache-dir --group dev .
COPY tests ./tests

FROM runtime AS production

RUN useradd --system --create-home appuser
USER appuser
