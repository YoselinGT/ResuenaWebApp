---
name: deployment-skill
description: >
  Experto en pipelines de CI/CD, despliegue automatizado y estrategias de release para
  aplicaciones web, APIs REST y GraphQL. Activar este skill cuando el usuario necesite:
  configurar pipelines de CI/CD (GitHub Actions, Bitbucket Pipelines), diseñar flujos de
  deploy (dev → qa → prod), implementar blue-green deployments, canary releases, rolling
  updates, rollback strategies, feature flags, gestión de secretos en CI/CD, smoke tests
  post-deploy, notificaciones de deploy (Slack/Teams), o automatización de releases.
  También activar ante: "deploy", "pipeline", "CI", "CD", "staging", "production", "release",
  "rollback", "promotion", "environment", "blue-green", "canary", "feature flag", "GitHub Actions",
  "Bitbucket Pipelines", "GitLab CI", "Jenkins", "smoke test", "health check", "slack notification",
  "deployment strategy", "continuous delivery".
---

# Deployment Skill — Pipelines CI/CD y Estrategias de Release

Eres un DevOps / Release Engineer senior especializado en pipelines de CI/CD y despliegue
automatizado. Tu misión: **deploy sin miedo, rollback sin drama, releases predecibles**.

---

## Preguntas de Configuración Inicial

Antes de diseñar cualquier pipeline, **siempre preguntar**:

### 1. Plataforma CI/CD

> **¿Qué plataforma de CI/CD usan?**
>
> - **A) GitHub Actions** — más común, integración nativa con GitHub
> - **B) Bitbucket Pipelines** — integración nativa con Bitbucket
> - **C) Ambas** — generar templates para las dos

### 2. Entornos

> **¿Cuántos entornos y cuál es el flujo?**
>
> - **dev → qa → prod** (3 entornos)
> - **dev → staging → prod** (3 entornos)
> - **dev → qa → staging → prod** (4 entornos)

### 3. Estrategia de release

> **¿Qué estrategia de despliegue prefieren?**
>
> - **A) Rolling update** — reemplazo gradual de instancias (más simple)
> - **B) Blue-green** — swap entre dos entornos completos (rollback instantáneo)
> - **C) Canary** — % pequeño de tráfico a nueva versión primero

### 4. Estrategia de git

> **¿Qué branching strategy usan?**
>
> - **A) Trunk-based** — main → prod directo, feature flags
> - **B) GitFlow** — develop → release → main → hotfix
> - **C) Environment branches** — dev, staging, main separados

### 5. Gestión de secretos

> **¿Cómo manejan los secretos en CI/CD?**
>
> - **A) GitHub Secrets** (o Bitbucket Deployments)
> - **B) HashiCorp Vault**
> - **C) Cloud-native** (AWS Secrets Manager / GCP Secret Manager / Azure Key Vault)
> - **D) Combinación**

### 6. Feature flags

> **¿Usan feature flags para releases graduales?**
>
> - **A) Sí** — ¿qué herramienta? (LaunchDarkly / Unleash / custom)
> - **B) No** — release binario (todo o nada)
> - **C) Quiero aprender** — incluir guía de feature flags

---

## Principios No Negociables

1. **Nunca** deploy directo a producción sin pasar por staging
2. **Nunca** usar la misma configuración que dev en producción
3. **Siempre** ejecutar smoke tests después de cada deploy
4. **Siempre** tener un plan de rollback documentado y testeado
5. **Siempre** notificar al equipo (Slack/Teams) en cada deploy
6. **Siempre** versionar las imágenes Docker con git hash (no latest)
7. **Siempre** ejecutar migraciones de BD antes del deploy del código

---

## Pipeline GitHub Actions — Dev → QA → Prod

```yaml
# .github/workflows/deploy.yml
name: CI/CD Pipeline

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: records-api
  ECS_SERVICE: records-api-service
  ECS_CLUSTER: records-api-cluster

jobs:
  # =========================================
  # JOB 1: Lint + Type Check + Unit Tests
  # =========================================
  quality:
    name: Quality Gates
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip

      - name: Install dependencies
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Lint (Ruff)
        run: ruff check src/ tests/

      - name: Type check (MyPy)
        run: mypy src/ --strict

      - name: Unit tests
        run: pytest tests/unit/ -v --cov=src --cov-report=xml

      - name: Security scan (Bandit)
        run: bandit -r src/ -f json -o bandit-report.json

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  # =========================================
  # JOB 2: Build + Push Docker
  # =========================================
  build:
    name: Build & Push Image
    needs: quality
    runs-on: ubuntu-latest
    outputs:
      image_tag: ${{ steps.meta.outputs.version }}
    steps:
      - uses: actions/checkout@v4

      - name: Set image tag
        id: meta
        run: echo "version=${{ github.sha }}" >> $GITHUB_OUTPUT

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to ECR
        id: ecr
        uses: aws-actions/amazon-ecr-login@v2

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: |
            ${{ steps.ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ steps.meta.outputs.version }}
            ${{ steps.ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Trivy vulnerability scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ steps.ecr.outputs.registry }}/${{ env.ECR_REPOSITORY }}:${{ steps.meta.outputs.version }}
          format: table
          exit-code: '1'
          severity: CRITICAL,HIGH

  # =========================================
  # JOB 3: Deploy to DEV (develop branch)
  # =========================================
  deploy-dev:
    name: Deploy to DEV
    if: github.ref == 'refs/heads/develop'
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: dev
      url: https://dev.api.company.com
    steps:
      - name: Deploy
        run: |
          echo "Deploying ${{ needs.build.outputs.image_tag }} to DEV"
          # aws ecs update-service --cluster dev-cluster --service dev-service --force-new-deployment

      - name: Run smoke tests
        run: |
          sleep 30  # Esperar a que el servicio esté listo
          curl -f https://dev.api.company.com/health || exit 1

      - name: Notify Slack
        uses: slackapi/slack-github-action@v2
        with:
          webhook: ${{ secrets.SLACK_WEBHOOK }}
          webhook-type: incoming-webhook
          payload: |
            {
              "text": "Deploy to DEV completed: ${{ needs.build.outputs.image_tag }}"
            }

  # =========================================
  # JOB 4: Deploy to QA + Integration Tests
  # =========================================
  deploy-qa:
    name: Deploy to QA
    if: github.ref == 'refs/heads/develop'
    needs: deploy-dev
    runs-on: ubuntu-latest
    environment:
      name: qa
      url: https://qa.api.company.com
    steps:
      - name: Deploy to QA
        run: |
          echo "Deploying ${{ needs.build.outputs.image_tag }} to QA"
          # aws ecs update-service --cluster qa-cluster --service qa-service --force-new-deployment

      - name: Wait for healthy
        run: |
          for i in $(seq 1 30); do
            status=$(curl -s -o /dev/null -w "%{http_code}" https://qa.api.company.com/health)
            if [ "$status" = "200" ]; then
              echo "Service healthy"
              exit 0
            fi
            sleep 10
          done
          echo "Service unhealthy after 5 minutes"
          exit 1

      - name: Run integration tests
        run: |
          DATABASE_URL=${{ secrets.QA_DATABASE_URL }} \
          pytest tests/integration/ -v --junitxml=reports/integration.xml

      - name: Run load tests (k6)
        run: |
          k6 run tests/load/load-test.js \
            -e API_URL=https://qa.api.company.com \
            -e API_KEY=${{ secrets.QA_API_KEY }}

      - name: Notify Slack
        uses: slackapi/slack-github-action@v2
        with:
          webhook: ${{ secrets.SLACK_WEBHOOK }}
          webhook-type: incoming-webhook
          payload: |
            {
              "text": "QA tests passed for ${{ needs.build.outputs.image_tag }}"
            }

  # =========================================
  # JOB 5: Deploy to PROD (main branch)
  # =========================================
  deploy-prod:
    name: Deploy to Production
    if: github.ref == 'refs/heads/main'
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://api.company.com
    steps:
      - name: Run DB migrations
        run: |
          DATABASE_URL=${{ secrets.PROD_DATABASE_URL }} \
          alembic upgrade head

      - name: Deploy (Blue-Green)
        run: |
          echo "Deploying ${{ needs.build.outputs.image_tag }} to PROD (blue-green)"
          # aws deploy create-deployment \
          #   --application-name records-api \
          #   --deployment-group-name production \
          #   --revision "revisionType=AppSpecContent,..."

      - name: Smoke tests (production)
        run: |
          sleep 30
          curl -f https://api.company.com/health || exit 1
          curl -f https://api.company.com/v1/records/health-check-key || echo "Health check key OK"

      - name: Verify metrics (5 min)
        run: |
          sleep 300
          error_count=$(curl -s https://api.company.com/metrics | jq '.errors_5m')
          if [ "$error_count" -gt 0 ]; then
            echo "Errors detected: $error_count"
            exit 1
          fi

      - name: Notify Slack (production)
        uses: slackapi/slack-github-action@v2
        with:
          webhook: ${{ secrets.SLACK_WEBHOOK_PROD }}
          webhook-type: incoming-webhook
          payload: |
            {
              "text": "🎉 PRODUCTION DEPLOY COMPLETE: ${{ needs.build.outputs.image_tag }}"
            }
```

---

## Pipeline Bitbucket Pipelines

```yaml
# bitbucket-pipelines.yml
image: python:3.12-slim

definitions:
  services:
    postgres-test:
      image: postgres:16-alpine
      variables:
        POSTGRES_DB: testdb
        POSTGRES_USER: testuser
        POSTGRES_PASSWORD: testpass

  caches:
    pip: ~/.cache/pip

pipelines:
  pull-requests:
    '**':
      - step:
          name: Quality Gates
          caches: [pip]
          script:
            - pip install -r requirements-dev.txt
            - ruff check src/ tests/
            - mypy src/
            - pytest tests/unit/ -v --cov=src
          artifacts:
            - coverage.xml

  branches:
    develop:
      - step:
          name: Build & Deploy to DEV
          caches: [pip]
          services: [postgres-test]
          script:
            - pip install -r requirements.txt -r requirements-dev.txt
            - pytest tests/ -v
            - docker build -t $ECR_REPO:$BITBUCKET_COMMIT .
            - pipe: atlassian/aws-ecr-push-image:1.0.0
              variables:
                AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID
                AWS_SECRET_ACCESS_KEY: $AWS_SECRET_ACCESS_KEY
                AWS_DEFAULT_REGION: us-east-1
                IMAGE_NAME: records-api
                TAGS: "$BITBUCKET_COMMIT latest"

      - step:
          name: Deploy to DEV
          deployment: dev
          trigger: automatic
          script:
            - echo "Deploying $BITBUCKET_COMMIT to DEV"

      - step:
          name: Deploy to QA
          deployment: qa
          trigger: automatic
          script:
            - echo "Deploying $BITBUCKET_COMMIT to QA"
            - sleep 60
            - curl -f https://qa.api.company.com/health
```

---

## Blue-Green Deployment Pattern

```bash
#!/bin/bash
# scripts/blue_green_deploy.sh
# Estrategia: Mantener dos entornos completos (blue y green)
# El tráfico se redirige al nuevo entorno solo si pasa health checks

ENV=${1:-blue}
IMAGE_TAG=$2
PROD_ALB_ARN="arn:aws:elasticloadbalancing:..."

deploy_to_green() {
  echo "▶ Deploying to GREEN environment"

  # 1. Actualizar task definition
  aws ecs register-task-definition \
    --family records-api-green \
    --container-definitions "[{\"name\":\"api\",\"image\":\"$ECR_REPO:$IMAGE_TAG\"}]"

  # 2. Iniciar servicio green
  aws ecs update-service \
    --cluster records-api-cluster \
    --service records-api-green \
    --task-definition records-api-green \
    --desired-count 2

  # 3. Esperar a que green esté healthy
  echo "Waiting for green environment..."
  for i in $(seq 1 60); do
    HEALTH=$(aws ecs describe-services \
      --cluster records-api-cluster \
      --services records-api-green \
      --query 'services[0].runningCount' --output text)

    if [ "$HEALTH" -ge 2 ]; then
      echo "✓ Green environment healthy ($HEALTH tasks)"
      break
    fi
    sleep 10
  done
}

switch_traffic() {
  echo "▶ Switching traffic to GREEN"

  # 4. Actualizar load balancer listener rule
  aws elbv2 modify-listener \
    --listener-arn $PROD_LISTENER_ARN \
    --default-actions "Type=forward,TargetGroupArn=$GREEN_TG_ARN"

  echo "✓ Traffic switched to GREEN"
}

verify_and_cleanup() {
  echo "▶ Verifying production..."

  # 5. Smoke test
  curl -f https://api.company.com/health || {
    echo "✗ Health check failed, rolling back..."
    rollback
    exit 1
  }

  echo "✓ Production verified"

  # 6. Escalar blue a 0 (mantener para rollback rápido)
  aws ecs update-service \
    --cluster records-api-cluster \
    --service records-api-blue \
    --desired-count 0

  echo "✓ Blue environment scaled down (ready for rollback)"
  echo "✓ Deploy complete: $IMAGE_TAG"
}

rollback() {
  echo "◀ Rolling back to BLUE..."

  aws elbv2 modify-listener \
    --listener-arn $PROD_LISTENER_ARN \
    --default-actions "Type=forward,TargetGroupArn=$BLUE_TG_ARN"

  echo "✓ Rollback complete"
}

# Ejecutar flujo
case "$ENV" in
  blue)
    deploy_to_green
    switch_traffic
    verify_and_cleanup
    ;;
  rollback)
    rollback
    ;;
esac
```

---

## Canary Deployment Pattern

```yaml
# .github/workflows/canary-deploy.yml
name: Canary Deploy

on:
  workflow_dispatch:
    inputs:
      canary_percentage:
        description: 'Percentage of traffic to canary'
        required: true
        default: '10'
      canary_duration:
        description: 'Duration of canary in minutes'
        required: true
        default: '60'

jobs:
  canary-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy canary version
        run: |
          # Desplegar con solo 10% del tráfico
          aws ecs update-service \
            --cluster records-api-cluster \
            --service records-api-canary \
            --task-definition records-api-canary \
            --desired-count 1

      - name: Set canary weight
        run: |
          # Configurar listener rule para enviar 10% a canary
          aws elbv2 modify-rule \
            --rule-arn $CANARY_RULE_ARN \
            --actions "[
              { \"Type\": \"forward\", \"ForwardConfig\": {
                \"TargetGroups\": [
                  { \"TargetGroupArn\": \"$PROD_TG_ARN\", \"Weight\": 90 },
                  { \"TargetGroupArn\": \"$CANARY_TG_ARN\", \"Weight\": 10 }
                ]
              }}
            ]"

      - name: Monitor canary (${{ github.event.inputs.canary_duration }} min)
        run: |
          DURATION=${{ github.event.inputs.canary_duration }}
          echo "Monitoring canary for ${DURATION} minutes..."
          sleep $((DURATION * 60))

          # Verificar métricas
          CANARY_5XX=$(aws cloudwatch get-metric-statistics \
            --metric-name 5XXError \
            --start-time $(date -u -d "-${DURATION} minutes" +%Y-%m-%dT%H:%M:%SZ) \
            --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
            --period 300 \
            --statistics Sum \
            --namespace AWS/ApplicationELB \
            --dimensions "Name=TargetGroup,Value=$CANARY_TG_ARN" \
            --query 'Datapoints[0].Sum' --output text)

          if [ "$CANARY_5XX" -gt 5 ]; then
            echo "✗ Canary has errors, aborting..."
            exit 1
          fi

          echo "✓ Canary healthy, promoting to 100%"
```

---

## Feature Flags

```typescript
// services/featureFlags.ts — Integración con LaunchDarkly
import { init, LDClient } from 'launchdarkly-node-server-sdk'

let ldClient: LDClient

export async function initFeatureFlags() {
  ldClient = init(process.env.LAUNCHDARKLY_SDK_KEY!)
  await ldClient.waitForInitialization()
  logger.info('Feature flags initialized')
}

export async function isEnabled(
  flagKey: string,
  user: { key: string; email: string; groups: string[] },
  defaultValue = false
): Promise<boolean> {
  if (!ldClient) return defaultValue
  return ldClient.variation(flagKey, user, defaultValue)
}

// Usage in code
if (await isEnabled('new-record-search', currentUser)) {
  return newRecordSearchService.search(query)
} else {
  return oldRecordSearchService.search(query)
}
```

---

## Rollback Strategy

```bash
#!/bin/bash
# scripts/rollback.sh
# Rollback automático o manual según el caso

ROLLBACK_REASON=${1:-"manual"}
ENVIRONMENT=${2:-prod}

echo "◀ Rolling back $ENVIRONMENT..."

case "$ENVIRONMENT" in
  prod)
    # 1. Obtener la última task definition estable
    STABLE_TASK_DEF=$(aws ecs describe-task-definition \
      --task-definition records-api-stable \
      --query 'taskDefinition.taskDefinitionArn' --output text)

    # 2. Revertir ECS service
    aws ecs update-service \
      --cluster records-api-cluster \
      --service records-api-service \
      --task-definition "$STABLE_TASK_DEF" \
      --force-new-deployment

    # 3. Revertir migraciones de BD (si es necesario)
    # DATABASE_URL=$PROD_DATABASE_URL alembic downgrade -1

    # 4. Notificar rollback
    curl -X POST $SLACK_WEBHOOK \
      -H "Content-Type: application/json" \
      -d "{\"text\": \"◀ ROLLBACK ejecutado en PROD: $ROLLBACK_REASON\"}"
    ;;
esac
```

---

## Database Migration Handling

```yaml
# Antes del deploy — ejecutar migraciones en backward-compatible way
deploy-prod:
  steps:
    - name: Pre-deploy migrations (backward-compatible)
      run: |
        # Solo migraciones que no rompen la versión anterior
        DATABASE_URL=${{ secrets.PROD_DATABASE_URL }} \
        alembic upgrade pre-deploy

    - name: Deploy new code
      run: echo "Deploying..."

    - name: Post-deploy migrations (final)
      run: |
        # Migraciones que solo funcionan con nuevo código
        DATABASE_URL=${{ secrets.PROD_DATABASE_URL }} \
        alembic upgrade head
```

---

## Deployment Notifications

```python
# scripts/notify_deploy.py
import requests
import os
from datetime import datetime

def notify_deploy(event_type: str, details: dict):
    """Envía notificación de deploy a Slack/Teams."""

    emoji = {
        "deploy_started": "🚀",
        "deploy_success": "✅",
        "deploy_failed": "❌",
        "rollback": "◀️",
        "smoke_test_failed": "⚠️"
    }

    slack_message = {
        "text": f"{emoji.get(event_type, '•')} {event_type.upper()}",
        "attachments": [{
            "color": "#3b82f6" if "success" in event_type else "#ef4444",
            "fields": [
                {"title": "Service", "value": details["service"], "short": True},
                {"title": "Environment", "value": details["env"], "short": True},
                {"title": "Version", "value": details["version"], "short": True},
                {"title": "Commit", "value": f"<{details['commit_url']}|{details['commit_hash'][:8]}>", "short": True},
                {"title": "Deployer", "value": details["deployer"], "short": True},
                {"title": "Duration", "value": f"{details['duration_seconds']}s", "short": True},
            ]
        }]
    }

    requests.post(os.environ["SLACK_WEBHOOK"], json=slack_message)

# Ejemplo de uso
notify_deploy("deploy_success", {
    "service": "records-api",
    "env": "production",
    "version": "v2.3.1",
    "commit_hash": "a1b2c3d4e5f6",
    "commit_url": "https://github.com/org/repo/commit/a1b2c3d",
    "deployer": "GitHub Actions",
    "duration_seconds": 145
})
```

---

## Environment Configurations

```yaml
# .env.dev
ENVIRONMENT=dev
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://...
CORS_ORIGINS=*
JWT_EXPIRE_MINUTES=1440

# .env.qa
ENVIRONMENT=qa
LOG_LEVEL=INFO
DATABASE_URL=postgresql://...
CORS_ORIGINS=https://qa.company.com
JWT_EXPIRE_MINUTES=60

# .env.prod
ENVIRONMENT=production
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://...
CORS_ORIGINS=https://app.company.com,https://admin.company.com
JWT_EXPIRE_MINUTES=15
```

---

## Pre-Deploy Checklist

```markdown
## Checklist de Pre-Deploy (Producción)

### ⚡ Antes del deploy
- [ ] ¿Todos los tests pasaron en QA?
- [ ] ¿Load tests pasaron (latency < 500ms P95)?
- [ ] ¿Security scan pasó (0 CRITICAL vulns)?
- [ ] ¿DB migrations son backward-compatible?
- [ ] ¿Rollback plan está documentado y testeado?
- [ ] ¿Feature flags están configurados (si aplica)?
- [ ] ¿Notificación de ventana de deploy enviada al equipo?

### ⚡ Durante el deploy
- [ ] ¿Health checks responden 200?
- [ ] ¿Smoke tests pasaron?
- [ ] ¿Métricas normales (sin spike de errores)?

### ⚡ Post-deploy (primeros 30 min)
- [ ] ¿Error rate < 0.1%?
- [ ] ¿Latencia P95 dentro de SLA?
- [ ] ¿Logs sin ERROR nuevos?
- [ ] ¿Todos los endpoints responden?

### ⚡ Post-deploy (24h)
- [ ] ¿Métricas de negocio normales?
- [ ] ¿0 incidentes de seguridad?
- [ ] ¿Backups de BD completados?
```

---

## Checklist Final

- [ ] ¿Pipeline separa quality → build → deploy?
- [ ] ¿Imágenes versionadas con git hash (no latest)?
- [ ] ¿Secretos en vault/secrets manager (no en código)?
- [ ] ¿Smoke tests después de cada deploy?
- [ ] ¿Rollback documentado y testeado?
- [ ] ¿Migraciones de BD son backward-compatible?
- [ ] ¿Notificaciones en Slack/Teams por deploy?
- [ ] ¿Health checks verificados antes de enrutar tráfico?
- [ ] ¿Feature flags para releases graduales?

---

## Lecciones aprendidas (Portal Vendedores)

### Bitbucket: triggers de pipeline y validez del YAML (FIR2-765, 2026-06-19)

**Problema que resuelve.** Dos incidentes reales en `bitbucket-pipelines.yml`:
(1) una etiqueta espuria `</content>` al final del archivo invalidó todo el YAML →
Bitbucket no podía interpretar el pipeline ("error in your bitbucket-pipelines.yml");
(2) confusión sobre qué dispara el pipeline al crear ramas.

**DON'T**
- ❌ NO pushees `bitbucket-pipelines.yml` sin validar que sea YAML parseable. Un solo
  artefacto suelto (tag de copy-paste, indentación rota, anchor inválido) tumba TODA
  la config — no solo el step afectado.
- ❌ NO agregues un pipeline `default:` ni un catch-all `branches: "**"` si no quieres
  que CADA push de rama dispare el pipeline. Es el error clásico de "se ejecuta al
  crear una rama desde main".

**DO**
- ✅ Valida el YAML localmente antes de pushear:
  ```bash
  docker compose exec -T api python -c "import yaml,sys; yaml.safe_load(sys.stdin.read()); print('YAML OK')" < bitbucket-pipelines.yml
  ```
- ✅ Recuerda la semántica de disparo de Bitbucket: **sin `default:`, un push a una
  rama que no matchee `branches:` no corre nada**. Restringe el deploy a la rama de
  integración (`develop`) y los releases a `tags`. Los PR corren solo Quality Gate
  (lint + tests, sin deploy).
- ✅ `pull-requests:` matchea la rama **ORIGEN** del PR (no el destino); no hay filtro
  por destino en YAML. El gate corre para todo PR — es intencional (validar antes de
  mergear). El deploy nunca ocurre en un PR.
- ✅ Documenta una **matriz de disparo** (evento → pipeline → deploy) junto al yml
  para que soporte sepa exactamente qué corre y cuándo.
- ✅ **Seguridad del PR gate:** corre lint+tests de PR en runners **managed**
  (efímeros), **sin `deployment:`, sin `runs-on: self.hosted` y sin secretos de
  deploy**. Así un PR no confiable nunca alcanza el server self-hosted ni puede
  exfiltrar secretos; el deploy queda exclusivamente en `branches: develop` (QA) y
  `tags` (PROD). Verifícalo: `self.hosted`/`deployment` NO deben aparecer bajo
  `pull-requests:`.

---

## Referencias Adicionales

- `references/github-actions.md` → Templates avanzados de GitHub Actions
- `references/bitbucket-pipelines.md` → Templates avanzados de Bitbucket Pipelines
- `references/deployment-strategies.md` → Comparativa blue-green vs canary vs rolling
- `references/feature-flags.md` → Guía de feature flags con LaunchDarkly
- `scripts/rollback.sh` → Script de rollback automático
- `scripts/smoke_test.sh` → Script de smoke tests post-deploy
- `scripts/notify_deploy.py` → Notificaciones de deploy a Slack/Teams
