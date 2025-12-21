import json
import logging
import smtplib
import time
from email.message import EmailMessage
from functools import wraps
from os import environ
from typing import Any, Optional

import psycopg2
import redis
import seqlog
from confluent_kafka import Producer
from fastapi import FastAPI, HTTPException
from loki_logger_handler.loki_logger_handler import LokiLoggerHandler
from prometheus_client import Counter, generate_latest
from pydantic import BaseModel, EmailStr
from starlette.responses import Response

# Configure basic logging first
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("infra-demo")

# Try to configure Seq logging with error handling
try:
    seqlog.configure_from_dict(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                "seq": {
                    "class": "seqlog.structured_logging.SeqLogHandler",
                    "server_url": environ.get("SEQ_URL", "http://seq:5341"),
                    "batch_size": 1,
                    "auto_flush_timeout": 1,
                }
            },
            "root": {
                "level": "NOTSET",
                "handlers": ["seq"],
            },
        }
    )
    logger.info("Seq logging configured successfully")
except Exception as e:
    logger.warning(f"Failed to configure Seq logging: {e}. Continuing without Seq.")

# Try to configure Loki logging with error handling
try:
    loki_handler = LokiLoggerHandler(
        url=environ.get("LOKI_URL", "http://loki:3100/loki/api/v1/push"),
        labels={"application": "infra-demo", "environment": "Development"},
        label_keys={},
        timeout=3,
    )
    logger.addHandler(loki_handler)
    logger.info("Loki logging configured successfully")
except Exception as e:
    logger.warning(f"Failed to configure Loki logging: {e}. Continuing without Loki.")

app = FastAPI(title="Infra Demo")

REQUESTS = Counter("http_requests_total", "Total HTTP requests")

# Global connection objects - initialized lazily
_pg_connection: Optional[psycopg2.extensions.connection] = None
_redis_connection: Optional[redis.Redis] = None
_kafka_producer: Optional[Producer] = None


def retry_with_backoff(retries=3, backoff_in_seconds=1):
    """Decorator to retry a function with exponential backoff"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if x == retries:
                        logger.error(f"Failed after {retries} retries: {e}")
                        raise
                    wait = backoff_in_seconds * (2**x)
                    logger.warning(
                        f"Attempt {x + 1} failed: {e}. Retrying in {wait}s..."
                    )
                    time.sleep(wait)
                    x += 1

        return wrapper

    return decorator


@retry_with_backoff(retries=3, backoff_in_seconds=1)
def get_postgres_connection() -> psycopg2.extensions.connection:
    """Lazy initialization of PostgreSQL connection with retry logic"""
    global _pg_connection

    if _pg_connection is None or _pg_connection.closed:
        logger.info("Initializing PostgreSQL connection...")
        _pg_connection = psycopg2.connect(
            dbname=environ.get("POSTGRES_DB"),
            user=environ.get("POSTGRES_USER"),
            password=environ.get("POSTGRES_PASSWORD"),
            host=environ.get("POSTGRES_HOST"),
            port=environ.get("POSTGRES_PORT"),
        )
        _pg_connection.autocommit = True
        logger.info("PostgreSQL connection established")

    return _pg_connection


@retry_with_backoff(retries=3, backoff_in_seconds=1)
def get_redis_connection() -> redis.Redis:
    """Lazy initialization of Redis connection with retry logic"""
    global _redis_connection

    if _redis_connection is None:
        logger.info("Initializing Redis connection...")
        _redis_connection = redis.Redis(
            host=environ.get("REDIS_HOST", "redis"),
            port=int(environ.get("REDIS_PORT", 6379)),
        )
        # Test the connection
        _redis_connection.ping()
        logger.info("Redis connection established")

    return _redis_connection


@retry_with_backoff(retries=3, backoff_in_seconds=1)
def get_kafka_producer() -> Producer:
    """Lazy initialization of Kafka producer with retry logic"""
    global _kafka_producer

    if _kafka_producer is None:
        logger.info("Initializing Kafka producer...")
        kafka_config = {
            "bootstrap.servers": f"kafka:{int(environ.get('KAFKA_INTERNAL_PORT', 9092))}",
            "socket.timeout.ms": 10000,
            "api.version.request.timeout.ms": 10000,
            "broker.address.family": "v4",
        }
        _kafka_producer = Producer(kafka_config)
        logger.info("Kafka producer initialized")

    return _kafka_producer


def send_event(topic, message):
    """Send event to Kafka with error handling"""
    try:
        producer = get_kafka_producer()
        producer.produce(topic, message)
        producer.flush(timeout=5)
        logger.info(f"Event sent to Kafka topic: {topic}")
    except Exception as e:
        logger.error(f"Failed to send event to Kafka: {e}")
        raise HTTPException(status_code=500, detail="Failed to send event to Kafka")


class SendMailRequest(BaseModel):
    to_email: EmailStr
    from_email: EmailStr
    subject: str
    body: str


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup with retry logic"""
    logger.info("Application starting up...")

    # Try to establish connections with retries
    try:
        get_postgres_connection()
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")

    try:
        get_redis_connection()
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")

    try:
        get_kafka_producer()
    except Exception as e:
        logger.error(f"Failed to initialize Kafka producer: {e}")

    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    logger.info("Application shutting down...")

    global _pg_connection, _redis_connection, _kafka_producer

    if _pg_connection and not _pg_connection.closed:
        _pg_connection.close()
        logger.info("PostgreSQL connection closed")

    if _redis_connection:
        _redis_connection.close()
        logger.info("Redis connection closed")

    if _kafka_producer:
        _kafka_producer.flush()
        logger.info("Kafka producer flushed")

    logger.info("Application shutdown complete")


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Infra Demo API",
        "endpoints": {
            "ping": "/ping",
            "metrics": "/metrics",
            "sendmail": "/sendmail (POST)",
            "event": "/event (POST)",
        },
    }


@app.get("/ping")
def ping():
    """Ping endpoint to check service health"""
    REQUESTS.inc()

    try:
        r = get_redis_connection()
        hits = r.incr("hits")
    except Exception as e:
        logger.error(f"Redis error: {e}")
        raise HTTPException(status_code=503, detail="Redis unavailable")

    try:
        pg = get_postgres_connection()
        with pg.cursor() as cur:
            cur.execute("SELECT NOW()")
            now = cur.fetchone()
    except Exception as e:
        logger.error(f"PostgreSQL error: {e}")
        raise HTTPException(status_code=503, detail="PostgreSQL unavailable")

    try:
        logger.info(
            "Ping called",
            extra={"hits": hits},
        )
    except Exception as e:
        # Log but don't fail if logging fails
        print(f"Logging error: {e}")

    return {
        "status": "ok",
        "hits": hits,
        "time": str(now),
    }


@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type="text/plain")


@app.post("/sendmail")
def send_mail(payload: SendMailRequest):
    """Send email via MailHog"""
    msg = EmailMessage()
    msg["To"] = payload.to_email
    msg["From"] = payload.from_email
    msg["Subject"] = payload.subject
    msg.set_content(payload.body)

    smtp_host = environ.get("MAILHOG_HOST", "mailhog")
    smtp_port = int(environ.get("MAILHOG_PORT", 1025))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
            smtp.send_message(msg)
    except Exception as e:
        try:
            logger.exception(
                "Failed to send email",
                extra={"from": payload.from_email, "to": payload.to_email},
            )
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Email sending failed: {str(e)}")

    try:
        logger.info(
            "Email sent",
            extra={
                "from": payload.from_email,
                "to": payload.to_email,
                "subject": payload.subject,
            },
        )
    except Exception as e:
        # Log but don't fail if logging fails
        print(f"Logging error: {e}")

    return {"status": "sent"}


@app.post("/event")
def produce_event(event: dict[str, Any]):
    """Produce event to Kafka"""
    try:
        send_event("infra-events", json.dumps(event))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending event: {e}")
        raise HTTPException(status_code=500, detail="Failed to produce event")

    try:
        logger.info("Event sent to Kafka", extra={"event": event})
    except Exception as e:
        # Log but don't fail if logging fails
        print(f"Logging error: {e}")

    return {"status": "ok"}


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    health_status = {"status": "healthy", "services": {}}

    # Check Redis
    try:
        r = get_redis_connection()
        r.ping()
        health_status["services"]["redis"] = "ok"
    except Exception as e:
        health_status["services"]["redis"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Check PostgreSQL
    try:
        pg = get_postgres_connection()
        with pg.cursor() as cur:
            cur.execute("SELECT 1")
        health_status["services"]["postgres"] = "ok"
    except Exception as e:
        health_status["services"]["postgres"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # Check Kafka (just check if producer exists)
    try:
        get_kafka_producer()
        health_status["services"]["kafka"] = "ok"
    except Exception as e:
        health_status["services"]["kafka"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    status_code = 200 if health_status["status"] == "healthy" else 503
    return Response(
        content=json.dumps(health_status),
        status_code=status_code,
        media_type="application/json",
    )
