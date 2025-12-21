FROM python:3.14.2-alpine3.23 AS build

RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    librdkafka-dev

WORKDIR /build

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


FROM python:3.14.2-alpine3.23 AS runtime

RUN apk add --no-cache \
    libpq \
    librdkafka

RUN addgroup -S app && adduser -S app -G app

WORKDIR /app

COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY main.py .

USER app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

