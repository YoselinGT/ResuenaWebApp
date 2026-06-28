---
name: observability-logging-skill
description: >
  Experto en observabilidad, logging estructurado, trazabilidad distribuida y monitoreo para
  APIs, microservicios y aplicaciones web. Activar este skill cuando el usuario necesite:
  implementar logging estructurado (JSON), configurar correlation IDs y trace IDs, diseñar
  bitácoras de auditoría, configurar log aggregation (ELK, Loki, CloudWatch), implementar
  distributed tracing (Jaeger, Zipkin, OpenTelemetry), crear dashboards de monitoreo (Grafana,
  Kibana), definir SLOs/SLIs, configurar alertas, implementar APM, o cualquier tarea de
  observabilidad. También activar ante: "log", "logging", "bitácora", "trazabilidad",
  "observabilidad", "monitor", "metrics", "apm", "tracing", "ELK", "Loki", "Elasticsearch",
  "Kibana", "Grafana", "Jaeger", "Zipkin", "OpenTelemetry", "correlation", "trace",
  "span", "SLO", "SLI", "alert", "alerta", "logs", "logging level", "structured logging",
  "fluentd", "fluent bit", "promtail", "error tracking", "audit log".
---

# Observability Skill — Logging, Trazabilidad y Monitoreo

Eres un Observability Engineer senior especializado en logging estructurado, tracing distribuido
y monitoreo de aplicaciones. Tu misión: **cada request es trazable de punta a punta; ningún error
pasa desapercibido; los logs son útiles, no ruido**.

---

## Preguntas de Configuración Inicial

Antes de diseñar el sistema de observabilidad, **siempre preguntar**:

### 1. Agregador de Logs

> **¿Qué sistema de log aggregation prefieren?**
>
> - **A) ELK Stack (Elasticsearch + Logstash + Kibana)** — más popular, rico en features
> - **B) Grafana + Loki + Promtail** — más ligero, cloud-native, integra métricas y logs
> - **C) Datadog** — enterprise, todo en uno, más caro
> - **D) Cloud-native** — CloudWatch (AWS) / Cloud Logging (GCP) / Azure Monitor (Azure)
> - **E) Docker local / Servidor dedicado** — Fluentd + Elasticsearch para on-premise
> - **F) No definido** → skill recomienda según stack y presupuesto

### 2. Formato de logs

> **¿Formato de logs?**
>
> - **A) JSON estructurado** — machine-friendly, fácil de parsear y buscar
> - **B) Texto human-readable** — para desarrollo local
> - **C) Ambos** — JSON en prod, texto en dev

### 3. Distributed Tracing

> **¿Necesitan distributed tracing?**
>
> - **A) Jaeger** — open source, compatible con OpenTelemetry
> - **B) Zipkin** — open source, más simple
> - **C) Cloud-native** — AWS X-Ray / GCP Cloud Trace / Azure Application Insights
> - **D) No** — aplicación monolítica simple

### 4. Alerting

> **¿Canales de alerta?**
>
> - **A) Slack** — notificaciones en canal
> - **B) PagerDuty / Opsgenie** — on-call rotations
> - **C) Email** — alertas no urgentes
> - **D) Webhook** — integración custom

### 5. SLO/SLA Monitoring

> **¿Necesitan monitoreo de SLOs?**
>
> - **A) Sí** — definir SLIs, SLOs, error budgets
> - **B) No** — solo métricas básicas y alertas

---

## Principios No Negociables

1. **Nunca** loguear datos sensibles (passwords, tokens, PII, credit cards)
2. **Siempre** incluir `correlation_id` en cada log entry
3. **Siempre** usar niveles de log (DEBUG, INFO, WARN, ERROR, FATAL)
4. **Siempre** loguear en JSON estructurado en producción
5. **Nunca** usar `print()` o `console.log()` en producción
6. **Siempre** rotar logs (no archivos infinitos)
7. **Siempre** muestrear traces (no 100% en producción, impacta performance)

---

## Logging Estructurado

### Python — structlog

```python
# src/logging_config.py
import structlog
import logging
import json
import os
from datetime import datetime, timezone

def add_correlation_id(logger, method_name, event_dict):
    """Agrega correlation_id del contexto actual."""
    from contextvars import ContextVar
    correlation_id: ContextVar[str] = ContextVar('correlation_id', default='unknown')
    event_dict['correlation_id'] = correlation_id.get()
    return event_dict

def add_timestamp(logger, method_name, event_dict):
    """Agrega timestamp ISO 8601."""
    event_dict['timestamp'] = datetime.now(timezone.utc).isoformat()
    return event_dict

def add_service_name(logger, method_name, event_dict):
    """Agrega nombre del servicio."""
    event_dict['service'] = os.getenv('SERVICE_NAME', 'records-api')
    return event_dict

def redact_sensitive(logger, method_name, event_dict):
    """Redacta campos sensibles antes de loguear."""
    sensitive_keys = {'password', 'token', 'secret', 'api_key', 'credit_card', 'ssn', 'pii'}
    for key in list(event_dict.keys()):
        if key.lower() in sensitive_keys:
            event_dict[key] = '[REDACTED]'
    return event_dict

# Configuración de structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        add_timestamp,
        add_correlation_id,
        add_service_name,
        redact_sensitive,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        # En producción: salida JSON
        structlog.processors.JSONRenderer(serializer=json.dumps)
        # En desarrollo: salida coloreada
        # structlog.dev.ConsoleRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
```

### Uso de logging estructurado

```python
# En middleware — capturar correlation_id
from contextvars import ContextVar
from uuid import uuid4

correlation_id_ctx: ContextVar[str] = ContextVar('correlation_id', default='unknown')

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Inyecta correlation_id en cada request."""
    cid = request.headers.get("X-Correlation-ID", str(uuid4()))
    correlation_id_ctx.set(cid)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response

# En services/repositories — loguear operaciones
async def find_by_key(self, key: str) -> Record | None:
    start = time.perf_counter()
    logger.info("record.lookup.start", key_hash=hashlib.sha256(key.encode()).hexdigest()[:12])

    try:
        result = await self._repo.find_by_key(key)

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "record.lookup.success",
            key_hash=hashlib.sha256(key.encode()).hexdigest()[:12],
            duration_ms=round(elapsed_ms, 2),
            found=result is not None,
            cache_hit=False
        )
        return result

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.error(
            "record.lookup.failed",
            key_hash=hashlib.sha256(key.encode()).hexdigest()[:12],
            duration_ms=round(elapsed_ms, 2),
            error_type=type(e).__name__,
            error_message=str(e)[:200]  # No loguear trace completo
        )
        raise

# Ejemplo de salida JSON:
# {
#   "timestamp": "2026-05-07T15:30:00.123Z",
#   "level": "info",
#   "event": "record.lookup.success",
#   "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
#   "service": "records-api",
#   "key_hash": "a1b2c3d4e5f6",
#   "duration_ms": 12.5,
#   "found": true,
#   "cache_hit": false
# }
```

### Node.js — winston

```typescript
// src/logging.ts
import winston from 'winston'
import { AsyncLocalStorage } from 'async_hooks'
import crypto from 'crypto'

const correlationStore = new AsyncLocalStorage<{ correlationId: string }>()

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format((info) => {
      const store = correlationStore.getStore()
      info.correlation_id = store?.correlationId || 'unknown'
      info.service = 'records-api'

      // Redact sensitive fields
      const sensitive = ['password', 'token', 'secret', 'api_key']
      for (const key of sensitive) {
        if (info[key]) info[key] = '[REDACTED]'
      }
      return info
    })(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    }),
    // Archivo rotado (solo en producción)
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error',
      maxsize: 10485760, // 10MB
      maxFiles: 5
    }),
    new winston.transports.File({
      filename: 'logs/combined.log',
      maxsize: 10485760,
      maxFiles: 5
    })
  ]
})

export { logger, correlationStore }
```

### Java — SLF4J + Logback

```xml
<!-- logback-spring.xml -->
<configuration>
  <appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
    <encoder class="net.logstash.logback.encoder.LogstashEncoder">
      <customFields>{"service":"records-api"}</customFields>
      <includeMdcKeyName>correlation_id</includeMdcKeyName>
    </encoder>
  </appender>

  <appender name="FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <file>logs/records-api.log</file>
    <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
      <fileNamePattern>logs/records-api.%d{yyyy-MM-dd}.log</fileNamePattern>
      <maxHistory>30</maxHistory>
    </rollingPolicy>
    <encoder class="net.logstash.logback.encoder.LogstashEncoder"/>
  </appender>

  <root level="INFO">
    <appender-ref ref="JSON"/>
    <appender-ref ref="FILE"/>
  </root>
</configuration>
```

```java
// CorrelationIdFilter.java
@Component
@Order(1)
public class CorrelationIdFilter extends OncePerRequestFilter {
    private static final String CORRELATION_ID_HEADER = "X-Correlation-ID";

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain chain) throws IOException, ServletException {
        String cid = request.getHeader(CORRELATION_ID_HEADER);
        if (cid == null) cid = UUID.randomUUID().toString();

        MDC.put("correlation_id", cid);
        response.setHeader(CORRELATION_ID_HEADER, cid);

        try {
            chain.doFilter(request, response);
        } finally {
            MDC.remove("correlation_id");
        }
    }
}
```

---

## Bitácoras de Auditoría (Audit Logs)

```python
# services/audit_logger.py
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Literal

@dataclass
class AuditEvent:
    """Evento de auditoría inmutable — registro de quién hizo qué y cuándo."""
    event_type: str          # record.created, record.updated, record.deleted
    actor_id: str            # usuario o API key que realizó la acción
    actor_type: str          # user, api_key, system
    resource_type: str       # record, user, api_key
    resource_id: str         # key o ID del recurso afectado
    action: str              # create, update, delete, read
    changes: dict | None     # diff de cambios (antes/después)
    metadata: dict           # IP, user_agent, etc.
    timestamp: str = None

    def __post_init__(self):
        self.timestamp = datetime.now(timezone.utc).isoformat()

async def log_audit_event(event: AuditEvent):
    """Registra evento de auditoría en log separado."""
    audit_logger.info(
        "audit.event",
        **asdict(event),
        # No incluir datos sensibles en changes
        redact_fields=["password", "token"]
    )

# Uso en service layer
await log_audit_event(AuditEvent(
    event_type="record.updated",
    actor_id=current_user.id,
    actor_type="user",
    resource_type="record",
    resource_id=record.key,
    action="update",
    changes={
        "before": {"payload": old_record.payload},
        "after":  {"payload": record.payload}
    },
    metadata={
        "ip": request.client.host,
        "user_agent": request.headers.get("user-agent", "unknown")
    }
))
```

---

## Log Levels — Guía de Uso

| Level | Cuándo usar | Ejemplo |
|-------|------------|---------|
| **DEBUG** | Detalles para desarrollo local | `debug("query.params", sql=query, params=values)` |
| **INFO** | Operaciones normales de negocio | `info("record.lookup", key_hash=..., duration_ms=...)` |
| **WARN** | Algo no ideal pero no crítico | `warn("cache.miss", key=..., reason="expired")` |
| **ERROR** | Fallo que requiere atención | `error("db.connection_failed", retry=3, error=...)` |
| **FATAL** | Crash de la aplicación | `fatal("app.startup_failed", reason=..., traceback=...)` |

---

## Logshippers — Fluentd / Fluent Bit / Promtail

### Fluentd (Docker sidecar)

```yaml
# docker-compose.yml — Fluentd como sidecar
services:
  app:
    # ... configuración de app
    logging:
      driver: fluentd
      options:
        fluentd-address: localhost:24224
        tag: "records-api.{{.Name}}"

  fluentd:
    image: fluent/fluentd:v1.17-1
    volumes:
      - ./docker/fluentd/fluent.conf:/fluentd/etc/fluent.conf
    ports:
      - "24224:24224"
```

```xml
<!-- docker/fluentd/fluent.conf -->
<source>
  @type forward
  port 24224
</source>

<filter records-api.**>
  @type record_transformer
  <record>
    service records-api
    environment ${ENVIRONMENT}
  </record>
</filter>

<match records-api.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  logstash_format true
  logstash_prefix records-api
  include_tag_key true
</match>
```

### Promtail (para Loki)

```yaml
# docker/promtail/promtail-config.yml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: records-api-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: records-api
          environment: production
          __path__: /var/log/records-api/*.log
```

---

## ELK Stack (Elasticsearch + Logstash + Kibana)

```yaml
# docker-compose.elk.yml — ELK Stack para desarrollo local
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.14.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.14.0
    volumes:
      - ./docker/logstash/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5000:5000"
    depends_on:
      - elasticsearch

  kibana:
    image: docker.elastic.co/kibana/kibana:8.14.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  es_data:
```

```ruby
# docker/logstash/logstash.conf
input {
  tcp {
    port => 5000
    codec => json
  }
}

filter {
  # Parsear timestamp
  date {
    match => ["timestamp", "ISO8601"]
  }

  # Extraer campos del mensaje
  if [event] =~ /^record\./ {
    mutate { add_tag => ["record_event"] }
  }

  # GeoIP (si hay IP en los logs)
  geoip {
    source => "client_ip"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "records-api-%{+YYYY.MM.dd}"
  }
}
```

---

## Grafana + Loki + Promtail

```yaml
# docker-compose.loki.yml — Grafana + Loki stack
services:
  loki:
    image: grafana/loki:3.0
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml
    volumes:
      - loki_data:/loki

  promtail:
    image: grafana/promtail:3.0
    volumes:
      - /var/log:/var/log
      - ./docker/promtail/promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml

  grafana:
    image: grafana/grafana:11.0
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_INSTALL_PLUGINS=grafana-lokiexplore-app
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./docker/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./docker/grafana/datasources:/etc/grafana/provisioning/datasources
```

```yaml
# docker/grafana/datasources/loki.yml
apiVersion: 1
datasources:
  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    isDefault: true

  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
```

### LogQL Queries (Loki Query Language)

```logql
# Buscar errores en los últimos 5 minutos
{service="records-api"} |= "ERROR"
  | json
  | error_type != ""[5m]

# Latencia de lookups
{service="records-api"} | json
  | event = "record.lookup.success"
  | unwrap duration_ms
  | quantile_over_time(0.95, duration_ms, 5m)

# Conteo de errores por tipo
sum by (error_type) (
  count_over_time(
    {service="records-api"} | json
    | level = "error"[5m]
  )
)
```

---

## Distributed Tracing — OpenTelemetry + Jaeger

```yaml
# docker-compose.jaeger.yml
services:
  jaeger:
    image: jaegertracing/all-in-one:1.57
    ports:
      - "5775:5775/udp"
      - "6831:6831/udp"
      - "6832:6832/udp"
      - "5778:5778"
      - "16686:16686"   # Jaeger UI
      - "14268:14268"
      - "14250:14250"
      - "9411:9411"
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
      - SPAN_STORAGE_TYPE=badger
      - BADGER_EPHEMERAL=false
      - BADGER_DIRECTORY_VALUE=/badger/data
      - BADGER_DIRECTORY_KEY=/badger/key
    volumes:
      - jaeger_data:/badger

volumes:
  jaeger_data:
```

### Instrumentación con OpenTelemetry

```python
# requirements.txt
opentelemetry-api==1.26.0
opentelemetry-sdk==1.26.0
opentelemetry-instrumentation-fastapi==0.47b0
opentelemetry-exporter-otlp==1.26.0
opentelemetry-exporter-jaeger==1.21.0

# src/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def init_tracing(app: FastAPI):
    """Inicializa distributed tracing con Jaeger."""

    # Crear tracer provider
    trace.set_tracer_provider(TracerProvider())

    # Exportador Jaeger
    jaeger_exporter = JaegerExporter(
        agent_host_name=os.getenv("JAEGER_HOST", "localhost"),
        agent_port=int(os.getenv("JAEGER_PORT", "6831")),
    )

    # Batch processor (envía spans en batches)
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Auto-instrumentar FastAPI
    FastAPIInstrumentor.instrument_app(app)
```

### Trazas manuales

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def find_by_key(self, key: str) -> Record | None:
    with tracer.start_as_current_span("record.lookup") as span:
        span.set_attribute("record.key", key)

        # Buscar en caché
        with tracer.start_as_current_span("cache.lookup"):
            cached = await self._cache.get(key)
            span.set_attribute("cache.hit", cached is not None)

        if cached:
            span.set_attribute("record.source", "cache")
            return cached

        # Buscar en BD
        with tracer.start_as_current_span("db.query"):
            span.set_attribute("db.operation", "find_by_key")
            result = await self._repo.find_by_key(key)
            span.set_attribute("record.found", result is not None)

        span.set_attribute("record.source", "database")
        return result
```

---

## Métricas — Prometheus + Grafana

### Python — prometheus_client

```python
# src/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from fastapi import APIRouter, Response

# Métricas de negocio
record_lookups_total = Counter(
    "record_lookups_total",
    "Total de lookups de registros",
    ["status"]  # success, not_found, error
)

record_lookup_duration_ms = Histogram(
    "record_lookup_duration_milliseconds",
    "Duración de lookups en ms",
    ["source"],  # cache, database
    buckets=[1, 5, 10, 25, 50, 100, 250, 500, 1000]
)

active_connections = Gauge(
    "active_connections",
    "Conexiones activas a BD"
)

# Endpoint de métricas para Prometheus
router = APIRouter()

@router.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain"
    )

# Uso en código
record_lookups_total.labels(status="success").inc()
record_lookup_duration_ms.labels(source="cache").observe(elapsed_ms)
```

---

## SLOs, SLIs y Error Budgets

### Definición de SLIs

```python
# services/sli_tracker.py
from prometheus_client import Counter, Gauge

# SLI: Disponibilidad = requests exitosos / requests totales
requests_total = Counter("requests_total", "Total requests", ["status_code"])
error_budget_remaining = Gauge("error_budget_remaining_percent", "Error budget remaining")

# SLO: 99.9% de disponibilidad (error budget = 0.1%)
TARGET_SLO = 99.9
ERROR_BUDGET_PERCENT = 100.0 - TARGET_SLO  # 0.1%

def calculate_error_budget(window_minutes: int = 1440):  # 24h window
    total = requests_total._metrics.copy()
    errors_5xx = sum(
        v for k, v in total.items()
        if k.get("status_code", "").startswith("5")
    )
    total_all = sum(v for v in total.values())

    if total_all == 0:
        return 100.0

    error_rate = (errors_5xx / total_all) * 100
    budget_used = (error_rate / ERROR_BUDGET_PERCENT) * 100
    budget_remaining = 100.0 - budget_used

    error_budget_remaining.set(budget_remaining)
    return budget_remaining
```

### SLO Dashboard (JSON para Grafana)

```json
{
  "dashboard": {
    "title": "Records API SLO Dashboard",
    "panels": [
      {
        "title": "Error Budget Remaining (24h)",
        "type": "gauge",
        "targets": [{
          "expr": "error_budget_remaining_percent"
        }],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                { "value": 0, "color": "red" },
                { "value": 50, "color": "yellow" },
                { "value": 80, "color": "green" }
              ]
            }
          }
        }
      },
      {
        "title": "P95 Latency",
        "type": "graph",
        "targets": [{
          "expr": "histogram_quantile(0.95, record_lookup_duration_milliseconds_bucket)"
        }]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [{
          "expr": "rate(requests_total[5m])"
        }]
      }
    ]
  }
}
```

---

## Alerting

### Prometheus Alert Rules

```yaml
# docker/prometheus/alerts.yml
groups:
  - name: records-api
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(requests_total{status_code=~"5.."}[5m]))
          / sum(rate(requests_total[5m])) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate > 1% en Records API"
          description: "Error rate es {{ $value | humanizePercentage }} en los últimos 5 minutos"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            rate(record_lookup_duration_milliseconds_bucket[5m])
          ) > 500
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency > 500ms"
          description: "P95 latency es {{ $value }}ms"

      - alert: LowErrorBudget
        expr: error_budget_remaining_percent < 20
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error budget below 20%"
          description: "Solo queda {{ $value }}% del error budget. Detener deploys."

      - alert: ServiceDown
        expr: up{job="records-api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Records API está caído"
```

### Alertmanager Config

```yaml
# docker/alertmanager/config.yml
route:
  receiver: slack-critical
  routes:
    - match:
        severity: critical
      receiver: pagerduty
    - match:
        severity: warning
      receiver: slack-warnings

receivers:
  - name: slack-critical
    slack_configs:
      - api_url: ${SLACK_WEBHOOK_CRITICAL}
        channel: '#alerts-critical'
        title: '[{{ .Status | toUpper }}] {{ .CommonLabels.alertname }}'
        text: '{{ .CommonAnnotations.description }}'

  - name: slack-warnings
    slack_configs:
      - api_url: ${SLACK_WEBHOOK_WARNINGS}
        channel: '#alerts-warnings'

  - name: pagerduty
    pagerduty_configs:
      - routing_key: ${PAGERDUTY_KEY}
```

---

## Dashboard de Operaciones (Grafana)

Dashboard pre-built con los paneles esenciales:

1. **Request Rate** — requests por segundo (gráfico de línea)
2. **Error Rate** — % de errores 4xx/5xx (gráfico de línea)
3. **P95 Latency** — latencia por endpoint (gráfico de línea)
4. **Cache Hit Rate** — % de cache hits (gauge)
5. **Active Connections** — conexiones a BD (gauge)
6. **DB Query Duration** — duración de queries P95
7. **Error Budget Remaining** — presupuesto de error (gauge)
8. **Top 10 Slow Queries** — queries más lentas (tabla)
9. **Log Volume** — volumen de logs por nivel (histograma)
10. **Deployment History** — timeline de deploys

---

## Docker — Logging Pipeline

```yaml
# docker-compose.logging.yml
services:
  app:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "5"
        labels: "service,environment"

  fluentd:
    image: fluent/fluentd:v1.17-1
    volumes:
      - ./docker/fluentd/fluent.conf:/fluentd/etc/fluent.conf
      - fluentd_buffer:/fluentd/buffer
    ports:
      - "24224:24224"

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.14.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - es_data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.14.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

volumes:
  fluentd_buffer:
  es_data:
```

---

## Recomendación según Entorno

| Entorno | Recomendación |
|---------|--------------|
| **Docker local / Dev** | Fluentd + Elasticsearch + Kibana (ELK simple) o Grafana + Loki |
| **Servidor dedicado** | ELK completo con Filebeat + Logstash |
| **AWS** | CloudWatch Logs + CloudWatch Metrics + X-Ray (nativo) |
| **GCP** | Cloud Logging + Cloud Monitoring + Cloud Trace (nativo) |
| **Azure** | Application Insights + Log Analytics (nativo) |
| **Enterprise (presupuesto alto)** | Datadog APM + Logs (todo en uno) |
| **Budget-constrained** | Grafana + Loki + Prometheus (open source) |

---

## Checklist Antes de Entregar

- [ ] ¿Logs en JSON estructurado (no texto plano)?
- [ ] ¿Correlation ID en cada log entry?
- [ ] ¿No hay datos sensibles en logs (passwords, tokens, PII)?
- [ ] ¿Log levels correctos (INFO en prod, DEBUG en dev)?
- [ ] ¿Log rotation configurada (no archivos infinitos)?
- [ ] ¿Distributed tracing habilitado (Jaeger/OpenTelemetry)?
- [ ] ¿Métricas de negocio expuestas (Prometheus endpoint)?
- [ ] ¿SLOs definidos y error budgets monitoreados?
- [ ] ¿Alertas configuradas (error rate, latency, availability)?
- [ ] ¿Dashboard de operaciones en Grafana/Kibana?
- [ ] ¿Logshipper configurado (Fluentd/Promtail)?
- [ ] ¿Pipeline de logs en Docker (sidecar fluentd)?

---

## Referencias Adicionales

- `references/structured-logging.md` → Guía completa de logging estructurado
- `references/elk-setup.md` → Setup completo de Elasticsearch + Logstash + Kibana
- `references/loki-setup.md` → Setup completo de Grafana + Loki + Promtail
- `references/opentelemetry.md` → Guía de OpenTelemetry
- `references/slo-guide.md` → Cómo definir y medir SLOs
- `references/dashboards/` → Dashboards JSON pre-built para Grafana
- `scripts/generate_log_config.py` → Genera configuración de logging
