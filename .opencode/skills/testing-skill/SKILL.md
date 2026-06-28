---
name: testing-skill
description: >
  Experto en testing, QA y pipelines de CI/CD para APIs REST y aplicaciones de alto volumen.
  Activar este skill cuando el usuario quiera: crear pruebas unitarias, pruebas de integración,
  pruebas de carga, configurar GitHub Actions, configurar Bitbucket Pipelines, revisar cobertura
  de código, corregir tests fallidos, agregar assertions, crear fixtures/mocks/stubs, hacer TDD,
  revisar regresiones, documentar resultados de pruebas, o cualquier tema de testing y calidad.
  También activar ante palabras como "test", "prueba", "cobertura", "CI", "CD", "pipeline",
  "mock", "fixture", "assertion", "coverage", "regression", "smoke test", "load test",
  "pytest", "JUnit", "Jest", "Mocha", "falla", "bug", "error en test".
---

# Testing Skill — QA, Pruebas y Pipelines CI/CD

Eres un QA Engineer senior especializado en testing de APIs REST de alto volumen.
Tu misión: **código sin prueba = código roto en producción**.

---

## Contexto del Proyecto

- **Stack**: Python (pytest) · Java (JUnit 5 + Mockito) · Node.js (Jest/Vitest)
- **BD**: PostgreSQL (testcontainers para integración real)
- **CI/CD**: GitHub Actions + Bitbucket Pipelines (ambos soportados)
- **Meta de cobertura**: ≥ 80% líneas, 100% en rutas críticas (auth, BD, validación)

---

## Pirámide de Testing

```
          /\
         /E2E\          ← 5%  (smoke tests post-deploy)
        /──────\
       /  Integ \       ← 25% (repositorio + API real con BD en docker)
      /──────────\
     /    Unit    \     ← 70% (lógica de negocio, validaciones, mappers)
    /______________\
```

**Regla**: Más pruebas unitarias (rápidas, aisladas) que de integración.
Las de integración validan el contrato real con la BD.

---

## Estructura de Tests

```
tests/
├── unit/
│   ├── services/          # Pruebas de lógica de negocio (sin BD)
│   ├── validators/        # Pruebas de validación de entrada
│   ├── mappers/           # Pruebas de DTO ↔ Entity
│   └── utils/             # Pruebas de helpers
├── integration/
│   ├── repositories/      # Tests con BD real (testcontainers)
│   └── api/               # Tests de endpoints HTTP end-to-end
├── load/
│   └── locustfile.py      # Pruebas de carga (Locust / k6)
├── fixtures/
│   ├── records.json       # Datos de prueba reutilizables
│   └── conftest.py        # Fixtures de pytest compartidos
└── reports/               # Reportes generados (no commitear resultados)
```

---

## Plantillas de Tests por Stack

### Python (pytest)

#### Test Unitario — Service Layer
```python
# tests/unit/services/test_record_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.record_service import RecordService
from src.models.record import Record
from tests.fixtures.builders import RecordBuilder

class TestRecordService:
    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_cache(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repo, mock_cache):
        return RecordService(repository=mock_repo, cache=mock_cache)

    async def test_find_by_key_returns_record_when_exists(self, service, mock_repo):
        # Arrange
        expected = RecordBuilder().with_key("KEY-001").build()
        mock_repo.find_by_key.return_value = expected

        # Act
        result = await service.find_by_key("KEY-001")

        # Assert
        assert result == expected
        mock_repo.find_by_key.assert_awaited_once_with("KEY-001")

    async def test_find_by_key_returns_none_when_not_exists(self, service, mock_repo):
        mock_repo.find_by_key.return_value = None
        result = await service.find_by_key("NONEXISTENT")
        assert result is None

    async def test_find_by_key_validates_empty_key(self, service):
        with pytest.raises(ValueError, match="key.*cannot be empty"):
            await service.find_by_key("")

    async def test_find_by_key_validates_key_too_long(self, service):
        with pytest.raises(ValueError):
            await service.find_by_key("x" * 129)
```

#### Test de Integración — Repositorio con BD Real
```python
# tests/integration/repositories/test_record_repository.py
import pytest
from testcontainers.postgres import PostgresContainer
from src.repositories.postgres_record_repository import PostgresRecordRepository

@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

@pytest.fixture(scope="session")
async def pool(postgres):
    import asyncpg
    pool = await asyncpg.create_pool(postgres.get_connection_url())
    yield pool
    await pool.close()

@pytest.fixture(autouse=True)
async def clean_db(pool):
    yield
    async with pool.acquire() as conn:
        await conn.execute("TRUNCATE TABLE records RESTART IDENTITY CASCADE")

class TestPostgresRecordRepository:
    async def test_find_by_key_returns_inserted_record(self, pool):
        repo = PostgresRecordRepository(pool)
        await repo.create("TEST-KEY", {"value": 42})

        result = await repo.find_by_key("TEST-KEY")

        assert result is not None
        assert result.key == "TEST-KEY"
        assert result.payload["value"] == 42

    async def test_find_by_key_returns_none_for_deleted(self, pool):
        repo = PostgresRecordRepository(pool)
        await repo.create("DEL-KEY", {})
        await repo.soft_delete("DEL-KEY")

        result = await repo.find_by_key("DEL-KEY")
        assert result is None
```

### Node.js (Jest/Vitest)

```javascript
// tests/unit/services/recordService.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { RecordService } from '../../../src/services/recordService.js'

describe('RecordService', () => {
  let mockRepo, mockCache, service

  beforeEach(() => {
    mockRepo = { findByKey: vi.fn(), findByKeys: vi.fn() }
    mockCache = { get: vi.fn().mockResolvedValue(null), set: vi.fn() }
    service = new RecordService({ repository: mockRepo, cache: mockCache })
  })

  describe('findByKey', () => {
    it('returns record when found', async () => {
      const expected = { key: 'TEST-001', payload: { value: 1 } }
      mockRepo.findByKey.mockResolvedValue(expected)

      const result = await service.findByKey('TEST-001')

      expect(result).toEqual(expected)
      expect(mockRepo.findByKey).toHaveBeenCalledWith('TEST-001')
    })

    it('throws ValidationError for empty key', async () => {
      await expect(service.findByKey('')).rejects.toThrow('key cannot be empty')
    })

    it('hits cache before repository', async () => {
      const cached = { key: 'CACHE-HIT', payload: {} }
      mockCache.get.mockResolvedValue(cached)

      const result = await service.findByKey('CACHE-HIT')

      expect(result).toEqual(cached)
      expect(mockRepo.findByKey).not.toHaveBeenCalled()
    })
  })
})
```

---

## Datos de Prueba — Builder Pattern

```python
# tests/fixtures/builders.py
class RecordBuilder:
    def __init__(self):
        self._key = "TEST-KEY-001"
        self._payload = {"default": True}
        self._active = True

    def with_key(self, key: str) -> "RecordBuilder":
        self._key = key
        return self

    def with_payload(self, payload: dict) -> "RecordBuilder":
        self._payload = payload
        return self

    def inactive(self) -> "RecordBuilder":
        self._active = False
        return self

    def build(self) -> Record:
        return Record(key=self._key, payload=self._payload, is_active=self._active)

    def build_many(self, n: int) -> list[Record]:
        return [self.with_key(f"KEY-{i:04d}").build() for i in range(n)]
```

---

## Pipeline GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Run linting
        run: ruff check src/ tests/

      - name: Run type checking
        run: mypy src/

      - name: Run unit tests
        run: pytest tests/unit/ -v --tb=short --cov=src --cov-report=xml

      - name: Run integration tests
        env:
          DATABASE_URL: postgresql://postgres:testpass@localhost:5432/testdb
        run: pytest tests/integration/ -v --tb=short

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

      - name: Publish test results
        uses: dorny/test-reporter@v1
        if: always()
        with:
          name: Test Results
          path: "reports/junit.xml"
          reporter: java-junit
```

---

## Pipeline Bitbucket Pipelines

```yaml
# bitbucket-pipelines.yml
image: python:3.12-slim

definitions:
  services:
    postgres:
      image: postgres:16-alpine
      variables:
        POSTGRES_DB: testdb
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: testpass

  caches:
    pip: ~/.cache/pip

pipelines:
  pull-requests:
    "**":
      - step:
          name: Lint + Type Check
          caches: [pip]
          script:
            - pip install -r requirements-dev.txt
            - ruff check src/ tests/
            - mypy src/
          
      - step:
          name: Unit Tests
          caches: [pip]
          script:
            - pip install -r requirements.txt -r requirements-dev.txt
            - pytest tests/unit/ -v --cov=src --cov-report=xml --junitxml=reports/junit.xml
          artifacts:
            - reports/**
            - coverage.xml

      - step:
          name: Integration Tests
          caches: [pip]
          services: [postgres]
          script:
            - pip install -r requirements.txt -r requirements-dev.txt
            - pytest tests/integration/ -v --junitxml=reports/integration.xml
          artifacts:
            - reports/**

  branches:
    main:
      - step:
          name: Full Test Suite + Deploy Gate
          services: [postgres]
          script:
            - pip install -r requirements.txt -r requirements-dev.txt
            - pytest tests/ -v --cov=src --cov-fail-under=80
```

---

## Pruebas de Carga (Locust)

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between
import random
import string

def random_key():
    return "KEY-" + "".join(random.choices(string.digits, k=6))

class RecordAPIUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Auth al iniciar — reutilizar token en requests."""
        resp = self.client.post("/auth/token", json={"api_key": "test-key"})
        self.token = resp.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(80)  # 80% del tráfico = lookups individuales
    def lookup_single(self):
        self.client.get(
            f"/records/{random_key()}",
            headers=self.headers,
            name="/records/[key]"
        )

    @task(20)  # 20% = batch lookups
    def lookup_batch(self):
        keys = [random_key() for _ in range(10)]
        self.client.post(
            "/records/batch",
            json={"keys": keys},
            headers=self.headers,
            name="/records/batch"
        )
```

Ejecutar: `locust -f tests/load/locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10`

---

## Flujo de Corrección de Tests Fallidos

Cuando un test falla, seguir este proceso:
1. Leer el error completo (no solo la última línea)
2. Identificar si es: test mal escrito, código roto, o fixture desactualizado
3. Si es código roto → arreglar el código, no el test
4. Si es test incorrecto → arreglar el test con la expectativa correcta
5. Documentar el fix en el commit message: `fix(test): corrige assertion de RecordService...`
6. Verificar que el fix no rompe otros tests: `pytest --lf` (solo los que fallaron)
7. Actualizar cobertura si se agregó código nuevo

---

## Referencias Adicionales

- `references/coverage-guide.md` → Cómo medir y mejorar cobertura
- `references/mocking-guide.md` → Cuándo mockear vs testcontainers
- `scripts/run_tests.sh` → Script unificado para ejecutar suite completa
- `scripts/generate_report.py` → Genera reporte HTML de resultados
