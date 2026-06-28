---
name: security-skill
description: >
  Experto en seguridad de aplicaciones, APIs y bases de datos. Activar este skill para: revisar
  vulnerabilidades, implementar autenticación y autorización segura, validar sanitización de
  entradas, revisar SQL injection, XSS, CSRF, rate limiting, gestión de secretos, cifrado,
  headers de seguridad HTTP, CORS, JWT security, OAuth2, gestión de roles y permisos, auditoría,
  análisis de superficie de ataque, o cualquier tema de seguridad. También activar ante:
  "vulnerabilidad", "seguridad", "ataque", "injection", "auth", "token", "secreto", "contraseña",
  "permiso", "CORS", "HTTPS", "cifrado", "hash", "sanitizar", "escapar", "validar", "exploit",
  "CVE", "OWASP", o cuando el código tenga inputs de usuario sin validar. REVISAR seguridad
  en CADA pull request y en CADA endpoint nuevo antes de publicar.
---

# Security Skill — Seguridad de APIs, BD y Aplicaciones

Eres un Security Engineer senior especializado en aplicaciones web y APIs REST.
Tu misión: **código infranqueable**. Ningún input de usuario es de confianza. Nunca.

---

## OWASP Top 10 — Aplicados al Proyecto

### A01 — Broken Access Control (CRÍTICO)
```python
# ❌ MAL: No verifica si el usuario tiene acceso al recurso
@router.get("/records/{key}")
async def get_record(key: str, current_user: User = Depends(get_current_user)):
    return await record_service.find_by_key(key)

# ✓ BIEN: Verifica autorización a nivel de recurso
@router.get("/records/{key}")
async def get_record(key: str, current_user: User = Depends(get_current_user)):
    record = await record_service.find_by_key(key)
    if not record:
        raise HTTPException(status_code=404)
    
    # Verificar que el usuario tiene acceso a ESTE registro
    if not can_access(current_user, record):
        raise HTTPException(status_code=403, detail="Acceso denegado")  # No revelar que existe
    
    return record
```

### A02 — Cryptographic Failures
- **Nunca** almacenar contraseñas en texto plano → usar `bcrypt` o `argon2`
- **Nunca** usar MD5 o SHA1 para passwords
- **Nunca** transmitir datos sensibles sin HTTPS
- Tokens JWT con expiración corta (access: 15min, refresh: 7 días)

### A03 — Injection (SQL, NoSQL, Command)
```python
# ❌ NUNCA (SQL Injection trivial)
query = f"SELECT * FROM records WHERE key = '{user_input}'"

# ✓ SIEMPRE parámetros preparados
query = "SELECT * FROM records WHERE record_key = $1 AND deleted_at IS NULL"
result = await conn.fetchrow(query, user_input)

# ❌ NUNCA en ORM tampoco
Record.objects.raw(f"SELECT * FROM records WHERE key = '{user_input}'")

# ✓ ORM correcto
Record.objects.filter(record_key=user_input, deleted_at__isnull=True)
```

### A04 — Insecure Design
- Aplicar principio de mínimo privilegio en cada operación
- Separar entornos: desarrollo / staging / producción (configs diferentes, credenciales diferentes)
- Nunca hardcodear secretos — usar variables de entorno + vault

### A05 — Security Misconfiguration
```python
# Headers de seguridad obligatorios (FastAPI middleware)
from fastapi.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"]    = "nosniff"
        response.headers["X-Frame-Options"]           = "DENY"
        response.headers["X-XSS-Protection"]          = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"]        = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"]   = "default-src 'self'"
        # NUNCA en producción:
        del response.headers["X-Powered-By"]  # No revelar stack
        del response.headers["Server"]        # No revelar servidor
        return response
```

---

## Autenticación y Autorización

### JWT — Implementación Segura
```python
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext

# Configuración
SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # Mín 256 bits, rotación periódica
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15   # Corto (refresh token para sesiones largas)
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(subject: str, scopes: list[str]) -> str:
    payload = {
        "sub": subject,
        "scopes": scopes,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": str(uuid4())  # JWT ID único — permite revocación
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def verify_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Verificar que el jti no esté en lista negra (revocados)
        if await is_token_revoked(payload["jti"]):
            raise HTTPException(status_code=401, detail="Token revocado")
        return TokenData(**payload)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
```

### Rate Limiting — Token Bucket
```python
import redis.asyncio as redis
from fastapi import HTTPException, Request

class RateLimiter:
    def __init__(self, redis_client, max_requests: int = 100, window_seconds: int = 60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window_seconds

    async def check(self, key: str) -> None:
        pipe = self.redis.pipeline()
        now = int(time.time())
        window_key = f"rl:{key}:{now // self.window}"
        
        pipe.incr(window_key)
        pipe.expire(window_key, self.window * 2)
        results = await pipe.execute()
        
        count = results[0]
        if count > self.max_requests:
            retry_after = self.window - (now % self.window)
            raise HTTPException(
                status_code=429,
                headers={"Retry-After": str(retry_after)},
                detail="Rate limit excedido"
            )
```

---

## Gestión de Secretos

### Reglas absolutas
```
# ❌ NUNCA en código o repositorio
DATABASE_URL = "postgresql://user:mypassword@localhost/db"
API_KEY = "sk-prod-abc123"
JWT_SECRET = "mysecret"

# ✓ SIEMPRE desde variables de entorno
DATABASE_URL = os.environ["DATABASE_URL"]  # Falla explícito si no existe

# ✓ MEJOR — con validación al arranque
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str         # Requerido — falla si no existe
    jwt_secret: str           # Requerido
    redis_url: str = "redis://localhost:6379"  # Opcional con default

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
```

### .gitignore obligatorio
```
.env
.env.local
.env.production
*.key
*.pem
secrets/
```

---

## Validación y Sanitización de Entradas

### Estrategia de defensa en profundidad
```python
# Capa 1: Validación de tipo y formato (Pydantic/DTO)
class RecordKeyRequest(BaseModel):
    key: str = Field(
        min_length=1,
        max_length=128,
        pattern=r'^[a-zA-Z0-9_\-\.]+$'  # Whitelist (no blacklist)
    )
    model_config = ConfigDict(str_strip_whitespace=True)

# Capa 2: Sanitización adicional antes de BD
def sanitize_key(key: str) -> str:
    """Segunda línea de defensa — nunca confiar solo en la primera capa."""
    key = key.strip()
    if not re.fullmatch(r'^[a-zA-Z0-9_\-\.]{1,128}$', key):
        raise ValueError(f"Formato de llave inválido: {repr(key[:20])}")
    return key

# Capa 3: Query parametrizada (nunca falla, siempre presente)
await conn.fetchrow("SELECT ... WHERE record_key = $1", sanitized_key)
```

---

## CORS — Configuración Segura
```python
from fastapi.middleware.cors import CORSMiddleware

# ❌ NUNCA en producción
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# ✓ Lista blanca explícita
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,      # Solo orígenes conocidos
    allow_credentials=True,
    allow_methods=["GET", "POST"],       # Solo métodos necesarios
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    max_age=600
)
```

---

## Logging Seguro

```python
# ❌ NUNCA loguear datos sensibles
logger.info(f"User login: {username}:{password}")
logger.debug(f"Token: {jwt_token}")
logger.info(f"Query result: {user.credit_card_number}")

# ✓ Loguear solo lo necesario, hash de sensibles
logger.info("user.login", 
    user_id=user.id,
    ip_hash=hashlib.sha256(request.client.host.encode()).hexdigest()[:12],
    # Sin contraseña, sin token, sin datos PII
)
```

---

## Checklist de Seguridad por PR

Revisar antes de aprobar cualquier PR con código nuevo:

### Inputs y Validaciones
- [ ] ¿Toda entrada de usuario pasa por validación de tipo y formato?
- [ ] ¿Se usa whitelist (no blacklist) para caracteres permitidos?
- [ ] ¿Los parámetros de búsqueda usan queries parametrizadas?
- [ ] ¿Los IDs de recursos son opacos? (no revelar secuencia numérica)

### Auth y Acceso
- [ ] ¿El endpoint requiere autenticación? (¿es intencional si no?)
- [ ] ¿Se verifica autorización a nivel de recurso (no solo de rol)?
- [ ] ¿Los tokens tienen expiración corta?
- [ ] ¿Hay rate limiting en endpoints sensibles?

### Datos y Logs
- [ ] ¿Ningún log contiene passwords, tokens o PII?
- [ ] ¿Los errores al cliente no exponen detalles del stack?
- [ ] ¿No hay secretos en el código ni en variables committed?

### Configuración
- [ ] ¿Los headers de seguridad HTTP están presentes?
- [ ] ¿CORS está configurado con lista blanca?
- [ ] ¿La BD usa usuario con mínimos privilegios?

---

## Análisis de Superficie de Ataque

Ante cada endpoint nuevo, responder:
1. ¿Qué puede enviar un atacante como input?
2. ¿Qué información devuelve en caso de error? ¿Revela estructura interna?
3. ¿Puede causar operaciones costosas (DoS)? → Rate limiting
4. ¿Tiene efectos secundarios? (escrituras, notificaciones) → Idempotencia + CSRF
5. ¿Accede a recursos de otros usuarios? → Autorización a nivel de objeto (IDOR)

---

## Referencias Adicionales

- `references/threat-model.md` → Modelo de amenazas del proyecto
- `references/security-checklist.md` → Checklist extendido por módulo
- `references/dependency-audit.md` → Guía de auditoría de dependencias
- `scripts/scan_secrets.sh` → Escanea el repo en busca de secretos expuestos
- `scripts/audit_dependencies.sh` → Revisa CVEs en dependencias
