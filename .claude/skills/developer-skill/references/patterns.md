# Patrones de Diseño — Referencia Técnica

## Creational

### Singleton

```python
class DatabaseConnection:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
```

### Factory Method

```python
from abc import ABC, abstractmethod

class Notification(ABC):
    @abstractmethod
    def send(self, message: str): pass

class EmailNotification(Notification):
    def send(self, message: str):
        print(f"Email: {message}")

class PushNotification(Notification):
    def send(self, message: str):
        print(f"Push: {message}")

class NotificationFactory:
    @staticmethod
    def create(channel: str) -> Notification:
        factories = {
            "email": EmailNotification,
            "push": PushNotification,
        }
        return factories[channel]()
```

### Builder

```python
class QueryBuilder:
    def __init__(self):
        self._select = []
        self._from = None
        self._where = []
        self._order_by = []

    def select(self, *cols):
        self._select = cols
        return self

    def from_table(self, table):
        self._from = table
        return self

    def where(self, condition):
        self._where.append(condition)
        return self

    def order_by(self, col):
        self._order_by.append(col)
        return self

    def build(self):
        return f"SELECT {', '.join(self._select)} FROM {self._from} WHERE {' AND '.join(self._where)}"

# Uso: QueryBuilder().select("id", "name").from_table("users").where("active = 1").build()
```

## Structural

### Adapter

```python
class ExternalAPI:
    def get_data(self):
        return {"user_id": 1, "name": "John"}

class APIAdapter:
    def __init__(self, external: ExternalAPI):
        self._external = external

    def get_user(self):
        raw = self._external.get_data()
        return {"id": raw["user_id"], "full_name": raw["name"]}
```

### Decorator

```python
import functools

def retry(max_attempts=3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
            return wrapper
        return decorator
    return decorator
```

### Facade

```python
class OrderFacade:
    def __init__(self):
        self._payment = PaymentService()
        self._inventory = InventoryService()
        self._shipping = ShippingService()

    def place_order(self, order_id: str):
        self._payment.charge(order_id)
        self._inventory.reserve(order_id)
        self._shipping.deliver(order_id)
        return {"status": "completed"}
```

## Behavioral

### Observer

```python
class EventManager:
    def __init__(self):
        self._observers: dict[str, list[callable]] = {}

    def subscribe(self, event: str, callback: callable):
        self._observers.setdefault(event, []).append(callback)

    def publish(self, event: str, data: dict):
        for callback in self._observers.get(event, []):
            callback(data)
```

### Strategy

```python
class PaymentProcessor:
    def __init__(self, strategy):
        self._strategy = strategy

    def set_strategy(self, strategy):
        self._strategy = strategy

    def pay(self, amount: float):
        self._strategy.process(amount)

class CreditCardStrategy:
    def process(self, amount):
        print(f"Processing credit card: ${amount}")

class PayPalStrategy:
    def process(self, amount):
        print(f"Processing PayPal: ${amount}")
```

### Controller (MVC)

```python
class UserController:
    def __init__(self, user_service: UserService):
        self._service = user_service

    async def get(self, request: Request) -> Response:
        user_id = request.path_params["id"]
        user = await self._service.get_user(user_id)
        return Response.json(UserResponse.model_validate(user))

    async def create(self, request: Request) -> Response:
        data = request.body
        user = await self._service.create_user(data)
        return Response.json(UserResponse.model_validate(user)), 201
```

### Repository

```python
class UserRepository:
    def __init__(self, db: Database):
        self._db = db

    async def find_by_id(self, user_id: int) -> User | None:
        return await self._db.fetchone("SELECT * FROM users WHERE id = $1", user_id)

    async def save(self, user: User) -> User:
        if user.id:
            await self._db.execute(
                "UPDATE users SET name = $1 WHERE id = $2", user.name, user.id
            )
        else:
            user.id = await self._db.execute(
                "INSERT INTO users (name) VALUES ($1) RETURNING id", user.name
            )
        return user
```

## Enterprise

### Circuit Breaker

```python
# Python — usando tenacity + estado propio
from enum import Enum
from datetime import datetime, timedelta
import threading

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30):
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._last_failure_time: datetime | None = None
        self._lock = threading.Lock()

    def call(self, func, *args, **kwargs):
        with self._lock:
            if self._state == CircuitState.OPEN:
                if datetime.now() - self._last_failure_time > timedelta(seconds=self._recovery_timeout):
                    self._state = CircuitState.HALF_OPEN
                else:
                    raise CircuitOpenError("Circuit breaker OPEN — BD no disponible temporalmente")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()
            if self._failure_count >= self._failure_threshold:
                self._state = CircuitState.OPEN
```

## Retry con Exponential Backoff

```python
import asyncio
import random

async def retry_with_backoff(func, max_retries=3, base_delay=0.1, max_delay=5.0):
    """Retry con jitter para evitar thundering herd."""
    for attempt in range(max_retries):
        try:
            return await func()
        except (ConnectionError, TimeoutError) as e:
            if attempt == max_retries - 1:
                raise
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 0.1), max_delay)
            await asyncio.sleep(delay)
```

## Bulkhead Pattern (aislamiento de recursos)

Separar pools de conexión por tipo de operación:
- Pool A (10 conns): Lecturas por llave — operaciones críticas
- Pool B (5 conns): Operaciones batch — menos urgentes
- Pool C (3 conns): Lecturas analíticas — background

Esto evita que operaciones batch saturen el pool y bloqueen las lecturas críticas.

## Cache-Aside Pattern

```python
async def get_record(key: str) -> Record | None:
    # 1. Intentar caché L1 (in-memory)
    if cached := memory_cache.get(key):
        return cached
    
    # 2. Intentar caché L2 (Redis)
    if cached := await redis_cache.get(f"record:{key}"):
        memory_cache.set(key, cached, ttl=60)
        return cached
    
    # 3. Consultar BD
    record = await db_repo.find_by_key(key)
    if record:
        await redis_cache.set(f"record:{key}", record, ttl=300)
        memory_cache.set(key, record, ttl=60)
    
    return record
```

## CQRS Ligero (para APIs de alto volumen)

Separar rutas de lectura y escritura si las lecturas dominan (>90%):
- **Query Handler**: Optimizado para lecturas, puede usar réplica de BD, caché agresivo
- **Command Handler**: Escribe siempre en primario, invalida caché

## DTO / Value Object Mapping

Nunca exponer modelos de BD directamente. Usar DTOs:

```python
# Modelo de BD (interno)
class RecordEntity:
    id: int
    record_key: str
    payload: dict
    created_at: datetime
    internal_flag: bool  # NO exponer

# DTO de respuesta (externo)
class RecordResponse(BaseModel):
    key: str
    payload: dict
    created_at: datetime
    # Sin id interno, sin internal_flag
```
