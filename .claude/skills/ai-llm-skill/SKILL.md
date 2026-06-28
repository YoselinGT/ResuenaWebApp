---
name: ai-llm-skill
description: >
  Experto en integración de IA y LLMs en aplicaciones web, móviles y APIs. Activar este skill
  cuando el usuario necesite: integrar Claude API (Anthropic), implementar RAG (Retrieval
  Augmented Generation), búsqueda semántica con embeddings, chatbot o asistente conversacional,
  streaming de respuestas, tool use o function calling, agentes de IA, análisis y clasificación
  de texto, generación de contenido, resúmenes automáticos, extracción de información, prompt
  engineering, gestión de contexto y memoria, o cualquier feature de inteligencia artificial.
  También activar ante: "IA", "LLM", "Claude", "Claude API", "Anthropic", "inteligencia
  artificial", "embeddings", "RAG", "semantic search", "búsqueda semántica", "agente", "agent",
  "tool use", "function calling", "chatbot", "generación de texto", "streaming", "prompt",
  "vector", "pgvector", "completions", "context window", "tokens", "sistema de IA", "AI feature".
  NOTA: Preguntar SIEMPRE el contexto de uso (pruebas / integración / producción) antes de
  generar código — los requisitos de producción son muy diferentes a los de pruebas.
---

# AI/LLM Skill — Integración de Claude API y Sistemas Inteligentes

Eres un AI Engineer senior especializado en integrar LLMs (especialmente Claude de Anthropic)
en aplicaciones de producción. Tu norte: **features de IA confiables, eficientes en costos
y con excelente UX**. La IA debe sentirse natural, no forzada.

---

## Preguntas de Configuración Inicial (OBLIGATORIAS)

Antes de generar cualquier código de IA, **siempre preguntar los tres bloques**:

### Bloque A — Tipo de integración

> **¿Qué tipo de feature de IA necesitan?**
>
> **A) Búsqueda semántica / RAG** — buscar en documentos propios, base de conocimiento
> **B) Chatbot / asistente conversacional** — diálogo multi-turno con el usuario
> **C) Generación de contenido** — textos, resúmenes, descripciones de productos
> **D) Análisis / clasificación / extracción** — categorizar, extraer datos estructurados
> **E) Agente con herramientas (tool use)** — el modelo puede consultar BD, APIs, calcular
> **F) Combinación** — especificar cuáles

### Bloque B — Contexto de despliegue (CRÍTICO — afecta todo el código)

> **¿Cuál es el contexto de uso?**
>
> **A) Solo pruebas / desarrollo** → código simple, sin optimizaciones, logs verbosos
> **B) Integración en sistema existente** → adapter pattern, feature flags, sin romper lo existente
> **C) Deploy a producción** → prompt caching, rate limiting, circuit breaker, monitoreo de costos
>
> Si es **producción**: ¿Cuántos usuarios concurrentes aproximados?
> - Bajo (< 50): rate limiting básico, un solo modelo
> - Medio (50-500): caching agresivo, cola de requests
> - Alto (> 500): múltiples workers, Kafka/Redis queue, caching distribuido

### Bloque C — Stack técnico

> **¿Qué stack usa el proyecto?**
>
> - **Backend**: Python/FastAPI · Node.js/Express · Java/Spring Boot
> - **Base de datos actual**: PostgreSQL (agregar pgvector) · MongoDB · otra
> - **¿Streaming de respuestas?** → Muy recomendado para chat (reduce tiempo de primera respuesta)

---

## Principios No Negociables

1. **Nunca** hardcodear la API Key — siempre desde variables de entorno / secrets manager
2. **Siempre** habilitar prompt caching en producción — ahorra hasta 90% del costo en prompts repetitivos
3. **Siempre** tener un fallback — si la API falla, degradar con búsqueda tradicional o mensaje de error claro
4. **Nunca** enviar PII (contraseñas, DNI, tarjetas) al LLM sin consentimiento explícito del usuario
5. **Siempre** rate limiting por usuario — no permitir que un usuario agote el presupuesto
6. **Siempre** loguear inputs/outputs para auditoría (sin datos sensibles)
7. **Siempre** circuit breaker si la API está caída — no dejar al usuario esperando indefinidamente
8. **Nunca** confiar ciegamente en el output del LLM — validar y sanitizar respuestas antes de usarlas

---

## Modelos Claude — Guía de Selección

| Modelo | ID | Capacidad | Velocidad | Uso ideal |
|--------|-----|-----------|-----------|-----------|
| **Claude Opus 4.7** | `claude-opus-4-7` | Máxima | Más lento | Razonamiento complejo, agentes, análisis profundo |
| **Claude Sonnet 4.6** | `claude-sonnet-4-6` | Alta | Rápido | Balance capacidad/costo, producción general |
| **Claude Haiku 4.5** | `claude-haiku-4-5-20251001` | Buena | Muy rápido | Clasificación, extracción simple, alta frecuencia |

**Regla**: Usar el modelo más capaz que el presupuesto permita para la tarea. Para producción de alto volumen: Haiku para clasificación simple, Sonnet para generación, Opus para razonamiento crítico.

---

## Setup Básico — Python (anthropic SDK)

### Instalación

```bash
pip install anthropic>=0.40.0
# Para embeddings con pgvector
pip install pgvector asyncpg
# Para RAG
pip install anthropic[vertex] sentence-transformers  # opcional
```

### Cliente base con prompt caching

```python
# src/ai/claude_client.py
import os
import anthropic
from anthropic import AsyncAnthropic

class ClaudeClient:
    """Wrapper del cliente de Claude con prompt caching y manejo de errores."""

    def __init__(self):
        self._client = AsyncAnthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],  # Falla explícito si no existe
            max_retries=3,
            timeout=60.0
        )
        self.default_model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

    async def complete(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        stream: bool = False,
        cache_system_prompt: bool = True,   # Activar por defecto
    ) -> str | anthropic.AsyncStream:

        system = []
        if system_prompt:
            block = {"type": "text", "text": system_prompt}
            if cache_system_prompt:
                block["cache_control"] = {"type": "ephemeral"}
            system.append(block)

        kwargs = dict(
            model=model or self.default_model,
            max_tokens=max_tokens,
            messages=messages,
            system=system or anthropic.NOT_GIVEN
        )

        if stream:
            return self._client.messages.stream(**kwargs)
        else:
            response = await self._client.messages.create(**kwargs)
            return response.content[0].text

claude = ClaudeClient()
```

### Llamada simple

```python
# Generación de contenido básica
response = await claude.complete(
    system_prompt="Eres un asistente especializado en análisis de datos de negocio.",
    messages=[{"role": "user", "content": "Resume los siguientes registros: ..."}],
    max_tokens=1024
)
```

---

## Setup Básico — Node.js (@anthropic-ai/sdk)

```bash
npm install @anthropic-ai/sdk
```

```typescript
// src/ai/claudeClient.ts
import Anthropic from '@anthropic-ai/sdk'

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,  // Falla si no existe
  maxRetries: 3,
  timeout: 60_000
})

const DEFAULT_MODEL = process.env.CLAUDE_MODEL ?? 'claude-sonnet-4-6'

export async function complete(
  messages: Anthropic.MessageParam[],
  options: {
    systemPrompt?: string
    model?: string
    maxTokens?: number
    cacheSystemPrompt?: boolean
  } = {}
): Promise<string> {
  const { systemPrompt, model = DEFAULT_MODEL, maxTokens = 2048, cacheSystemPrompt = true } = options

  const system: Anthropic.TextBlockParam[] = systemPrompt
    ? [{
        type: 'text',
        text: systemPrompt,
        ...(cacheSystemPrompt ? { cache_control: { type: 'ephemeral' } } : {})
      }]
    : []

  const response = await client.messages.create({
    model,
    max_tokens: maxTokens,
    messages,
    system: system.length ? system : undefined
  })

  return (response.content[0] as Anthropic.TextBlock).text
}

// Streaming
export async function* streamComplete(
  messages: Anthropic.MessageParam[],
  systemPrompt?: string
): AsyncGenerator<string> {
  const stream = client.messages.stream({
    model: DEFAULT_MODEL,
    max_tokens: 2048,
    messages,
    system: systemPrompt ? [{ type: 'text', text: systemPrompt }] : undefined
  })

  for await (const chunk of stream) {
    if (chunk.type === 'content_block_delta' && chunk.delta.type === 'text_delta') {
      yield chunk.delta.text
    }
  }
}
```

---

## Prompt Caching — Producción Obligatorio

El prompt caching reduce costos hasta **90%** para el contexto estático (system prompts, documentos RAG, ejemplos few-shot). El caché tiene TTL de 5 minutos.

```python
# Ejemplo: RAG con caching de documentos recuperados
async def answer_with_rag(question: str, documents: list[str], correlation_id: str) -> str:
    # El system prompt y los documentos son estáticos para esta query → cachear
    system_context = "\n\n".join(documents)

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Contexto de referencia:\n{system_context}",
                    "cache_control": {"type": "ephemeral"}  # Cachear el contexto
                },
                {
                    "type": "text",
                    "text": f"\nPregunta: {question}"      # No cachear la pregunta
                }
            ]
        }
    ]

    response = await anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=messages
    )

    # Monitorear cache performance
    usage = response.usage
    logger.info(
        "claude.cache",
        input_tokens=usage.input_tokens,
        cache_read_tokens=getattr(usage, 'cache_read_input_tokens', 0),
        cache_write_tokens=getattr(usage, 'cache_creation_input_tokens', 0),
        correlation_id=correlation_id
    )

    return response.content[0].text
```

---

## RAG — Retrieval Augmented Generation

Pipeline completo para búsqueda semántica sobre documentos propios.

### Setup pgvector en PostgreSQL

```sql
-- Extensión y tabla de embeddings
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE document_embeddings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id   VARCHAR(255) NOT NULL,       -- ID del documento origen
    source_type VARCHAR(100) NOT NULL,       -- "manual", "faq", "product", etc.
    chunk_index INTEGER NOT NULL,
    content     TEXT NOT NULL,               -- Texto del chunk
    embedding   vector(1536),               -- voyage-3: 1024 dims; text-embedding-3: 1536
    metadata    JSONB NOT NULL DEFAULT '{}', -- título, sección, url, etc.
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (source_id, chunk_index)
);

-- Índice HNSW para búsqueda aproximada rápida (mejor que IVFFlat para < 1M vectores)
CREATE INDEX ON document_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

### Ingestión de Documentos

```python
# src/ai/rag/ingestor.py
import anthropic
import asyncpg
from typing import AsyncGenerator

CHUNK_SIZE = 800       # tokens aproximados por chunk
CHUNK_OVERLAP = 100    # solapamiento entre chunks para no perder contexto

async def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide texto en chunks con overlap."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

async def get_embedding(text: str, client: anthropic.AsyncAnthropic) -> list[float]:
    """Genera embedding usando voyage-3 via Anthropic."""
    # Nota: usar voyage-3 o text-embedding-3-small dependiendo del cliente
    # Aquí usamos la API directa de Voyage AI (integrada con Anthropic)
    import voyageai
    vo = voyageai.AsyncClient(api_key=os.environ["VOYAGE_API_KEY"])
    result = await vo.embed([text], model="voyage-3", input_type="document")
    return result.embeddings[0]

async def ingest_document(
    pool: asyncpg.Pool,
    source_id: str,
    source_type: str,
    content: str,
    metadata: dict
) -> int:
    """Ingesta un documento: chunking + embedding + almacenamiento."""
    chunks = await chunk_text(content)
    client = anthropic.AsyncAnthropic()
    stored = 0

    async with pool.acquire() as conn:
        for i, chunk in enumerate(chunks):
            embedding = await get_embedding(chunk, client)
            await conn.execute("""
                INSERT INTO document_embeddings
                    (source_id, source_type, chunk_index, content, embedding, metadata)
                VALUES ($1, $2, $3, $4, $5::vector, $6)
                ON CONFLICT (source_id, chunk_index) DO UPDATE
                SET content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata
            """, source_id, source_type, i, chunk, embedding, json.dumps(metadata))
            stored += 1

    return stored
```

### Búsqueda Semántica + Generación

```python
# src/ai/rag/searcher.py
async def semantic_search(
    pool: asyncpg.Pool,
    query: str,
    top_k: int = 5,
    source_type: str | None = None
) -> list[dict]:
    """Busca los chunks más relevantes para la query."""
    query_embedding = await get_embedding(query, anthropic.AsyncAnthropic())

    filter_clause = "AND source_type = $3" if source_type else ""
    params = [query_embedding, top_k]
    if source_type:
        params.append(source_type)

    async with pool.acquire() as conn:
        rows = await conn.fetch(f"""
            SELECT
                content,
                metadata,
                source_id,
                1 - (embedding <=> $1::vector) AS similarity
            FROM document_embeddings
            WHERE 1 - (embedding <=> $1::vector) > 0.7  -- Threshold de relevancia
            {filter_clause}
            ORDER BY embedding <=> $1::vector
            LIMIT $2
        """, *params)

    return [dict(r) for r in rows]

async def rag_answer(
    pool: asyncpg.Pool,
    question: str,
    system_prompt: str,
    correlation_id: str
) -> str:
    """Pipeline completo: retrieve → augment → generate."""
    # 1. Recuperar chunks relevantes
    relevant_chunks = await semantic_search(pool, question, top_k=5)

    if not relevant_chunks:
        return "No encontré información relevante para responder tu pregunta."

    # 2. Construir contexto (con caching)
    context = "\n\n---\n\n".join([
        f"[Fuente: {c['metadata'].get('title', 'sin título')}]\n{c['content']}"
        for c in relevant_chunks
    ])

    # 3. Generar respuesta
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}  # Cachear system prompt
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Información de referencia:\n\n{context}",
                        "cache_control": {"type": "ephemeral"}  # Cachear contexto
                    },
                    {
                        "type": "text",
                        "text": f"\nPregunta: {question}"
                    }
                ]
            }
        ]
    )

    logger.info(
        "rag.answer",
        chunks_used=len(relevant_chunks),
        correlation_id=correlation_id,
        input_tokens=response.usage.input_tokens
    )

    return response.content[0].text
```

---

## Streaming de Respuestas

Imprescindible para chat — reduce el tiempo de primera respuesta de segundos a milisegundos.

### Backend — FastAPI con SSE

```python
# api/ai_router.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import json

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, current_user=Depends(get_current_user)):
    """Endpoint de chat con streaming via SSE."""

    async def generate():
        client = anthropic.AsyncAnthropic()
        try:
            async with client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=[{
                    "type": "text",
                    "text": ASSISTANT_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"}
                }],
                messages=request.messages
            ) as stream:
                async for text_chunk in stream.text_stream:
                    yield f"data: {json.dumps({'text': text_chunk})}\n\n"

                # Señal de fin
                yield f"data: {json.dumps({'done': True})}\n\n"

        except anthropic.APIError as e:
            yield f"data: {json.dumps({'error': 'Error al procesar tu solicitud'})}\n\n"
            logger.error("claude.stream.error", error=str(e))

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )
```

### Frontend — React consumiendo stream

```tsx
// hooks/useAIStream.ts
import { useState, useCallback } from 'react'

export function useAIStream() {
  const [streamedText, setStreamedText] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)

  const streamChat = useCallback(async (messages: ChatMessage[]) => {
    setStreamedText('')
    setIsStreaming(true)

    try {
      const response = await fetch('/api/ai/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages })
      })

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n').filter(l => l.startsWith('data: '))

        for (const line of lines) {
          const data = JSON.parse(line.slice(6))
          if (data.text) {
            setStreamedText(prev => prev + data.text)
          }
          if (data.done) break
        }
      }
    } finally {
      setIsStreaming(false)
    }
  }, [])

  return { streamedText, isStreaming, streamChat }
}

// Componente de chat
function ChatMessage({ text, isStreaming }: { text: string; isStreaming: boolean }) {
  return (
    <div className="prose prose-sm max-w-none">
      {text}
      {isStreaming && <span className="animate-pulse">▋</span>}
    </div>
  )
}
```

---

## Tool Use / Function Calling

Permite al modelo usar herramientas: consultar BD, llamar APIs, hacer cálculos.

```python
# src/ai/tools/db_tools.py
import anthropic
import json

# Definir herramientas disponibles para el modelo
TOOLS = [
    {
        "name": "search_records",
        "description": "Busca registros en la base de datos por llave o criterio",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Término de búsqueda o llave del registro"
                },
                "limit": {
                    "type": "integer",
                    "description": "Máximo de resultados (default: 10)",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_summary_stats",
        "description": "Obtiene estadísticas de la base de datos",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity": {
                    "type": "string",
                    "enum": ["orders", "users", "products"],
                    "description": "Entidad sobre la que calcular estadísticas"
                }
            },
            "required": ["entity"]
        }
    }
]

# Ejecutores de herramientas (implementaciones reales)
async def execute_tool(tool_name: str, tool_input: dict, db_pool) -> str:
    if tool_name == "search_records":
        results = await db_pool.fetch(
            "SELECT * FROM records WHERE record_key ILIKE $1 LIMIT $2",
            f"%{tool_input['query']}%",
            tool_input.get('limit', 10)
        )
        return json.dumps([dict(r) for r in results])

    elif tool_name == "get_summary_stats":
        entity = tool_input["entity"]
        count = await db_pool.fetchval(f"SELECT COUNT(*) FROM {entity}")
        return json.dumps({"entity": entity, "total_count": count})

    return json.dumps({"error": f"Herramienta desconocida: {tool_name}"})

# Ciclo completo de tool use
async def agent_with_tools(
    user_message: str,
    db_pool,
    correlation_id: str
) -> str:
    client = anthropic.AsyncAnthropic()
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            tools=TOOLS,
            messages=messages,
            system=[{
                "type": "text",
                "text": "Eres un asistente de datos. Usa las herramientas disponibles para responder con información real.",
                "cache_control": {"type": "ephemeral"}
            }]
        )

        # Si el modelo terminó sin tools → devolver respuesta
        if response.stop_reason == "end_turn":
            return response.content[0].text

        # Si el modelo quiere usar una herramienta
        if response.stop_reason == "tool_use":
            # Agregar la respuesta del modelo al historial
            messages.append({"role": "assistant", "content": response.content})

            # Ejecutar las herramientas solicitadas
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result = await execute_tool(block.name, block.input, db_pool)
                    logger.info(
                        "ai.tool.used",
                        tool=block.name,
                        correlation_id=correlation_id
                    )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result
                    })

            # Devolver resultados al modelo
            messages.append({"role": "user", "content": tool_results})
            # Continuar el loop — el modelo procesará los resultados
```

---

## Manejo de Contexto y Memoria

### Sliding Window (conversación larga)

```python
# src/ai/context_manager.py
MAX_CONTEXT_MESSAGES = 20          # Máximo de mensajes a enviar
SUMMARY_TRIGGER = 30               # Resumir cuando se superen 30 mensajes

async def manage_context(
    messages: list[dict],
    new_message: str,
    session_id: str,
    redis_client
) -> list[dict]:
    """Gestiona el contexto para no exceder el context window."""

    # Cargar historial desde Redis
    history_key = f"chat:{session_id}:messages"
    history = json.loads(await redis_client.get(history_key) or "[]")

    history.append({"role": "user", "content": new_message})

    # Si es demasiado largo, resumir los mensajes más antiguos
    if len(history) > SUMMARY_TRIGGER:
        old_messages = history[:-MAX_CONTEXT_MESSAGES]
        recent_messages = history[-MAX_CONTEXT_MESSAGES:]

        summary = await summarize_conversation(old_messages)
        history = [
            {"role": "user", "content": f"[Resumen de conversación anterior]: {summary}"},
            {"role": "assistant", "content": "Entendido, continuemos desde ahí."},
            *recent_messages
        ]

    # Guardar en Redis (TTL de 4 horas)
    await redis_client.setex(history_key, 14400, json.dumps(history))

    return history[-MAX_CONTEXT_MESSAGES:]

async def summarize_conversation(messages: list[dict]) -> str:
    client = anthropic.AsyncAnthropic()
    conversation_text = "\n".join([
        f"{m['role'].upper()}: {m['content']}"
        for m in messages
    ])
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",  # Haiku para tarea simple de resumen
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"Resume en 3-5 oraciones los puntos clave de esta conversación:\n\n{conversation_text}"
        }]
    )
    return response.content[0].text
```

---

## Rate Limiting y Control de Costos

```python
# src/ai/rate_limiter.py
import redis.asyncio as redis
from anthropic import AsyncAnthropic

# Límites por plan de usuario
USER_LIMITS = {
    "free":    {"requests_per_day": 20,   "tokens_per_day": 50_000},
    "basic":   {"requests_per_day": 200,  "tokens_per_day": 500_000},
    "premium": {"requests_per_day": 2000, "tokens_per_day": 5_000_000},
}

class AIRateLimiter:
    def __init__(self, redis_client):
        self._redis = redis_client

    async def check_and_increment(self, user_id: str, plan: str, estimated_tokens: int) -> None:
        today = datetime.now(timezone.utc).date().isoformat()
        limits = USER_LIMITS.get(plan, USER_LIMITS["free"])

        req_key = f"ai:requests:{user_id}:{today}"
        tok_key = f"ai:tokens:{user_id}:{today}"

        pipe = self._redis.pipeline()
        pipe.incr(req_key)
        pipe.incrby(tok_key, estimated_tokens)
        pipe.expire(req_key, 86400)
        pipe.expire(tok_key, 86400)
        results = await pipe.execute()

        if results[0] > limits["requests_per_day"]:
            raise HTTPException(status_code=429, detail="Límite diario de requests de IA alcanzado")

        if results[1] > limits["tokens_per_day"]:
            raise HTTPException(status_code=429, detail="Límite diario de tokens de IA alcanzado")

    async def get_today_usage(self, user_id: str) -> dict:
        today = datetime.now(timezone.utc).date().isoformat()
        pipe = self._redis.pipeline()
        pipe.get(f"ai:requests:{user_id}:{today}")
        pipe.get(f"ai:tokens:{user_id}:{today}")
        results = await pipe.execute()
        return {
            "requests": int(results[0] or 0),
            "tokens": int(results[1] or 0)
        }
```

---

## Circuit Breaker para la API de Claude

```python
# src/ai/circuit_breaker.py
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"       # Normal
    OPEN = "open"          # Fallback
    HALF_OPEN = "half_open" # Probando

class ClaudeCircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._failure_threshold = failure_threshold
        self._last_failure_time: float = 0
        self._recovery_timeout = recovery_timeout

    def can_proceed(self) -> bool:
        if self._state == CircuitState.CLOSED:
            return True
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time > self._recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                return True
            return False
        return True  # HALF_OPEN: intentar

    def on_success(self):
        self._failures = 0
        self._state = CircuitState.CLOSED

    def on_failure(self):
        self._failures += 1
        self._last_failure_time = time.time()
        if self._failures >= self._failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning("ai.circuit_breaker.opened")

claude_breaker = ClaudeCircuitBreaker()

async def safe_claude_call(messages: list, system: str, fallback: str = None) -> str:
    if not claude_breaker.can_proceed():
        logger.warning("ai.circuit_breaker.blocked")
        return fallback or "El asistente de IA no está disponible temporalmente."
    try:
        result = await claude.complete(messages, system_prompt=system)
        claude_breaker.on_success()
        return result
    except anthropic.APIError as e:
        claude_breaker.on_failure()
        logger.error("ai.api.error", error=str(e))
        return fallback or "Error al procesar tu solicitud. Por favor intenta de nuevo."
```

---

## Integración en API REST

```python
# api/ai_router.py — Endpoints listos para usar
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])

class ChatRequest(BaseModel):
    messages: list[dict] = Field(..., min_length=1, max_length=50)
    session_id: str | None = None

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    source_type: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)

class AnalyzeRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=50_000)
    task: str = Field(..., description="classify | summarize | extract")

@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db),
    redis=Depends(get_redis)
):
    """Chat conversacional con memoria de sesión."""
    await rate_limiter.check_and_increment(current_user.id, current_user.plan, 2000)

    messages = await manage_context(
        request.messages,
        request.messages[-1]["content"],
        request.session_id or str(uuid.uuid4()),
        redis
    )

    response = await safe_claude_call(
        messages=messages,
        system=CHAT_SYSTEM_PROMPT,
        fallback="No pude procesar tu mensaje. Por favor intenta de nuevo."
    )
    return {"response": response}

@router.get("/search")
async def semantic_search_endpoint(
    q: str,
    source_type: str | None = None,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    """Búsqueda semántica sobre la base de conocimiento."""
    chunks = await semantic_search(db, q, top_k=5, source_type=source_type)
    if not chunks:
        return {"results": [], "answer": None}

    answer = await rag_answer(db, q, RAG_SYSTEM_PROMPT, str(uuid.uuid4()))
    return {"results": chunks, "answer": answer}
```

---

## Seguridad y Moderación de Prompts

```python
# src/ai/security.py
import re

FORBIDDEN_PATTERNS = [
    r"ignore (previous|all|above) instructions",
    r"you are now",
    r"system prompt",
    r"jailbreak",
    r"DAN mode",
    r"act as if",
    r"pretend (you are|to be)",
]

SENSITIVE_FIELDS = ["password", "contraseña", "credit_card", "ssn", "token", "secret"]

def sanitize_user_input(text: str, max_length: int = 10_000) -> str:
    """Valida y sanitiza el input antes de enviarlo al LLM."""
    if len(text) > max_length:
        raise ValueError(f"Input demasiado largo: {len(text)} caracteres")

    # Detectar intentos de prompt injection
    text_lower = text.lower()
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, text_lower):
            raise ValueError("Input no permitido — posible prompt injection")

    return text.strip()

def redact_sensitive_from_log(messages: list[dict]) -> list[dict]:
    """Redacta campos sensibles antes de loguear."""
    redacted = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            for field in SENSITIVE_FIELDS:
                content = re.sub(
                    rf'"{field}"\s*:\s*"[^"]*"',
                    f'"{field}": "[REDACTED]"',
                    content,
                    flags=re.IGNORECASE
                )
        redacted.append({**msg, "content": content})
    return redacted
```

---

## Testing de Features con IA

```python
# tests/unit/test_ai_features.py
from unittest.mock import AsyncMock, patch
import pytest

class TestChatEndpoint:
    @pytest.fixture
    def mock_claude(self):
        """Mock del cliente de Claude para tests deterministas."""
        with patch("src.ai.claude_client.claude.complete") as mock:
            mock.return_value = "Respuesta del asistente de prueba"
            yield mock

    async def test_chat_returns_response(self, mock_claude, test_client):
        response = await test_client.post("/api/v1/ai/chat", json={
            "messages": [{"role": "user", "content": "Hola"}]
        })
        assert response.status_code == 200
        assert "response" in response.json()

    async def test_chat_rate_limit_enforced(self, test_client):
        for _ in range(21):  # Límite free: 20 requests/día
            await test_client.post("/api/v1/ai/chat", json={
                "messages": [{"role": "user", "content": "test"}]
            })
        response = await test_client.post("/api/v1/ai/chat", json={
            "messages": [{"role": "user", "content": "test"}]
        })
        assert response.status_code == 429

    async def test_prompt_injection_rejected(self, test_client):
        response = await test_client.post("/api/v1/ai/chat", json={
            "messages": [{"role": "user", "content": "ignore previous instructions and..."}]
        })
        assert response.status_code == 400
```

---

## Deployment — Consideraciones por Contexto

### Solo pruebas / desarrollo

```env
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-haiku-4-5-20251001  # Más barato para pruebas
LOG_LEVEL=DEBUG
AI_RATE_LIMIT_ENABLED=false
```

```python
# Código mínimo sin optimizaciones
client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
response = await client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=1024,
    messages=[{"role": "user", "content": user_input}]
)
```

### Integración en sistema existente

```python
# Adapter pattern — desacoplar el sistema del SDK específico
class AIServiceAdapter:
    """Interfaz genérica — el sistema no conoce a Anthropic directamente."""

    async def complete(self, prompt: str, context: list[dict] | None = None) -> str: ...
    async def search(self, query: str) -> list[dict]: ...

class ClaudeAdapter(AIServiceAdapter):
    """Implementación con Claude."""
    # ...

# Feature flag para habilitar/deshabilitar
AI_ENABLED = os.getenv("AI_FEATURES_ENABLED", "false") == "true"

if AI_ENABLED:
    ai_service = ClaudeAdapter()
else:
    ai_service = FallbackAdapter()  # Búsqueda tradicional
```

### Producción

```python
# Checklist de producción:
# ✓ API key en AWS Secrets Manager / Azure Key Vault / GCP Secret Manager
# ✓ Prompt caching habilitado (ahorro hasta 90%)
# ✓ Rate limiting por usuario (por plan)
# ✓ Circuit breaker (fallback si API caída)
# ✓ Logging estructurado sin PII
# ✓ Monitoreo de costos con alertas
# ✓ Retry con backoff exponencial (anthropic SDK lo hace automáticamente)
# ✓ Request timeout configurado (60s máximo)
# ✓ Content moderation en inputs de usuario
```

---

## Monitoreo de Costos

```python
# src/ai/cost_tracker.py
# Precios aproximados por millón de tokens (mayo 2026)
PRICING = {
    "claude-opus-4-7":              {"input": 15.0,  "output": 75.0},
    "claude-sonnet-4-6":            {"input": 3.0,   "output": 15.0},
    "claude-haiku-4-5-20251001":    {"input": 0.25,  "output": 1.25},
}
CACHE_DISCOUNT = 0.10  # Cache reads cuestan 10% del precio de input

def estimate_cost(model: str, input_tokens: int, output_tokens: int,
                  cache_read_tokens: int = 0) -> float:
    prices = PRICING.get(model, PRICING["claude-sonnet-4-6"])
    input_cost  = (input_tokens / 1_000_000) * prices["input"]
    cache_cost  = (cache_read_tokens / 1_000_000) * prices["input"] * CACHE_DISCOUNT
    output_cost = (output_tokens / 1_000_000) * prices["output"]
    return input_cost + cache_cost + output_cost

async def track_usage(model: str, usage, correlation_id: str, redis_client):
    cost = estimate_cost(
        model,
        usage.input_tokens,
        usage.output_tokens,
        getattr(usage, 'cache_read_input_tokens', 0)
    )
    today = datetime.now(timezone.utc).date().isoformat()
    await redis_client.incrbyfloat(f"ai:cost:{today}", cost)
    logger.info("ai.cost", model=model, cost_usd=round(cost, 6), correlation_id=correlation_id)
```

---

## Checklist según Contexto

### Solo pruebas
- [ ] ¿API key en .env (no en código)?
- [ ] ¿Modelo de prueba (Haiku) para reducir costo?
- [ ] ¿Input validado antes de enviar?

### Integración en sistema existente
- [ ] ¿Adapter pattern implementado?
- [ ] ¿Feature flag para habilitar/deshabilitar?
- [ ] ¿Fallback a funcionalidad existente si AI falla?
- [ ] ¿Tests con mock del LLM?

### Producción
- [ ] ¿API key en Vault / Secrets Manager?
- [ ] ¿Prompt caching habilitado?
- [ ] ¿Rate limiting por usuario?
- [ ] ¿Circuit breaker con fallback?
- [ ] ¿Logs estructurados sin PII?
- [ ] ¿Monitoreo de costos con alerta si supera presupuesto diario?
- [ ] ¿Content moderation en inputs?
- [ ] ¿pgvector configurado si hay RAG?
- [ ] ¿Streaming habilitado si es chat?

---

## Referencias Adicionales

- `references/prompts/` → Biblioteca de system prompts por caso de uso
- `references/eval-results.md` → Resultados de evaluaciones de calidad
- `references/cost-analysis.md` → Análisis de costos por feature
- `references/rag-corpus.md` → Descripción de la base de conocimiento
- `scripts/ingest_documents.py` → Script para ingestar documentos al RAG
- `scripts/test_prompts.py` → Herramienta para probar prompts interactivamente
- `scripts/cost_report.py` → Reporte de costos de IA del mes
