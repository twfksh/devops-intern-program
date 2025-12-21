# Server-Side Tools Infrastructure

Prerequisites: Linux and Docker installed. A sample `.env` is provided in the repository for testing.

## Docker Compose Profiles

### API Profile

**Services:** FastAPI app, PostgreSQL, Redis, Kafka, Prometheus, Grafana, Loki, Seq, MailHog

**Run:**
```bash
docker-compose --profile api up -d
```

**Access:**
- API: `http://localhost:8000`
- Grafana: `http://localhost:3001`
- Seq: `http://localhost:5340`
- MailHog: `http://localhost:8025`
- Kafka UI: `http://localhost:8070`

**Test:**
```bash
# Ping API
curl http://localhost:8000/ping

# Post Event
curl -X POST http://localhost:8000/event -H "Content-Type: application/vnd.kafka.json.v2+json" -d '{
  "records":[
    {"value":{"user":"user","action":"login","ts":"2025-13-17T12:00:00Z"}}
  ]
}'
```

Open grafana at `http://localhost:3001` to view metrics and logs and kafka at `http://localhost:8070` to view kafka topics.

**Stop:**
```bash
docker-compose --profile api down
```

---

### Elasticsearch Profile

**Services:** Elasticsearch, Kibana

**Run:**
```bash
docker-compose --profile es up -d
```

**Access:**
- Elasticsearch: `https://localhost:9200` (user: elastic, password from .env)
- Kibana: `http://localhost:5601`

**Note:** 
- Elasticsearch passwords must be at least 6 characters long. Update `ELASTIC_PASSWORD` and `KIBANA_PASSWORD` in `.env` if using default values.
- Wait for services to start before accessing. This can take a few minutes depending on your system's performance.

**Stop:**
```bash
docker-compose --profile es down
```

---

### PostgreSQL Backup Profile

**Services:** PostgreSQL backup service (requires PostgreSQL from API profile)

**Run:**
```bash
# Start API profile first (for PostgreSQL)
docker-compose --profile api --profile pgbackup up -d
```

**Backup Location:** `./backups/`

**Logs:** `./logs/`

**Stop:**
```bash
docker-compose --profile api --profile pgbackup down
```

---

### Misc Profile

**Services:** MongoDB, Mongo Express, Cassandra

**Run:**
```bash
docker-compose --profile misc up -d
```

**Access:**
- MongoDB: `localhost:27017`
- Mongo Express: `http://localhost:8088`
- Cassandra: `localhost:9042`

**Stop:**
```bash
docker-compose --profile misc down
```

---

## Run Multiple Profiles

```bash
docker-compose --profile api --profile misc up -d
```

## View Logs

```bash
docker-compose logs -f [service_name]
```

---

## Clean Up

Remove all containers, volumes, and data:
```bash
docker-compose --profile api --profile es --profile pgbackup --profile misc down -v
rm -rf data/ backups/ logs/
```

---

## Nginx Setup and Testing

### Prerequisites
- Nginx installed (`sudo apt install nginx`)
- Node.js installed (for Node.js demos)
- PHP-FPM installed (for PHP demo: `sudo apt install php-fpm`)

### Setup Steps

**1. Copy project files:**
```bash
sudo cp -r nginx-projects /srv/nginx-projects
```

**2. Backup existing nginx config:**
```bash
sudo mv /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak
```

**3. Copy new nginx config:**
```bash
sudo cp nginx.conf /etc/nginx/nginx.conf
```

**4. Test nginx configuration:**
```bash
sudo nginx -t
```

**5. Reload nginx:**
```bash
sudo systemctl reload nginx
```

### Testing Each Project

**Static Demo (Port 8080):**
```bash
curl http://localhost:8080
```

**URI/Args Test (Port 8081):**
```bash
curl http://localhost:8081/test?foo=bar
```

**Static with Caching (Port 8082):**
```bash
curl -I http://localhost:8082/mini.min.css
```

**Reverse Proxy Demo (Port 8083):**
```bash
curl http://localhost:8083
```

**Node.js Demo (Port 8084):**
```bash
# Start Node.js app first
cd nginx-projects/node-js-demo
node app.js &

# Test
curl http://localhost:8084
```

**PHP Demo (Port 8086):**
```bash
# Ensure PHP-FPM is running
sudo systemctl start php-fpm

# Test
curl http://localhost:8086
```

**Load Balancer Demo (Port 8888):**
```bash
# Start all 3 Node.js servers
cd nginx-projects/load-balancer-demo
node server-1.js &
node server-2.js &
node server-3.js &

# Test load balancing (run multiple times to see different servers respond)
curl http://localhost:8888
curl http://localhost:8888
curl http://localhost:8888
```

### Stop All Node.js Processes
```bash
pkill -f "node"
```

### Restore Original Nginx Config
```bash
sudo mv /etc/nginx/nginx.conf.bak /etc/nginx/nginx.conf
sudo systemctl reload nginx
```
