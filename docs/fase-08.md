# Fase 08 — Campañas musicales — Creación + carga de archivos

> **Estado:** `[ ]` pendiente · **Días estimados:** 4 · **Modelo:** `claude-sonnet-4-6`
> **Skills:** `developer-skill`, `frontend-skill`
> **Pre-requisitos:** Fase 06 `[x]`, Fase 07 `[x]`

---

## Contexto

Esta fase implementa la creación de campañas musicales por parte de los artistas. Una campaña es el objeto central del negocio: contiene la canción, material promocional y la selección de profesionales a quienes se enviará.

Flujo de creación de campaña (multi-step):
1. **Paso 1 — Información básica:** título, descripción, género/categoría objetivo.
2. **Paso 2 — Material:** upload de audio (MP3/WAV ≤50MB), imagen de portada (JPG/PNG ≤5MB), material adicional ZIP opcional (≤100MB).
3. **Paso 3 — Selección de profesionales:** filtrar por tipo (blogger/playlister/influencer/reel), género, ver perfil básico. Seleccionar 1-N profesionales.
4. **Paso 4 — Confirmar y enviar:** resumen con créditos a usar. Si no hay suficientes créditos → bloquear con link a compra. Si sí → retener créditos y enviar.

El artista puede guardar como borrador en cualquier paso y retomar luego.

---

## Tareas

- [ ] **T1.** Endpoint `POST /campanas`: crea campaña en estado `borrador`. Artistas únicamente. Body: `{titulo, descripcion, genero_id}`.
- [ ] **T2.** Endpoint `PATCH /campanas/:id`: actualiza campos editables de la campaña en borrador. Valida que el artista es dueño.
- [ ] **T3.** Endpoint `POST /campanas/:id/upload/audio`: multipart, valida MIME audio/mpeg o audio/wav, ≤50MB, sube a S3 vía `StorageService` con clave `campanas-audio/{campana_id}/{filename}`, actualiza `url_audio` con la clave (no URL).
- [ ] **T4.** Endpoint `POST /campanas/:id/upload/imagen`: multipart, valida MIME image/jpeg o image/png, ≤5MB, redimensiona a 800×800 max con Pillow, sube a S3 con clave `campanas-imagenes/{campana_id}/cover.jpg`, actualiza `url_imagen`.
- [ ] **T5.** Endpoint `POST /campanas/:id/upload/material`: multipart, valida MIME application/zip, ≤100MB, sube a S3 con clave `campanas-material/{campana_id}/material.zip`, actualiza `url_material`.
- [ ] **T6.** Endpoint `GET /profesionales/disponibles`: artistas consultan profesionales disponibles para una campaña. Filtros: `tipo_profesional`, `genero_id`, `categoria_id`. Solo retorna aprobados y activos. Incluye nombre, tipo, categorías, conteo de campañas completadas.
- [ ] **T7.** Endpoint `POST /campanas/:id/profesionales`: recibe `{profesional_ids: []}`, valida que todos existen y están aprobados, los vincula a la campaña en `campana_profesionales` con estado `pendiente`.
- [ ] **T8.** Endpoint `POST /campanas/:id/enviar`: verifica que la campaña tiene audio + imagen + al menos 1 profesional. Calcula créditos necesarios (1 por profesional). Verifica saldo. Retiene créditos del wallet. Cambia estado campaña a `enviada`. Registra en bitácora. Dispara notificación por email a cada profesional seleccionado.
- [ ] **T9.** Endpoint `GET /campanas` (artista): lista campañas propias paginada, con filtro por estado.
- [ ] **T10.** Endpoint `GET /campanas/:id` (artista): detalle de campaña incluyendo estado de cada profesional vinculado.
- [ ] **T11.** Endpoint `DELETE /campanas/:id`: solo si estado es `borrador`. Elimina los objetos S3 asociados (`url_audio`, `url_imagen`, `url_material`) vía `StorageService`. Elimina el registro de BD.
- [ ] **T12.** Vista multi-step `(dashboard)/artista/campanas/nueva/page.tsx`: wizard con 4 pasos. Guarda progreso en localStorage. Muestra créditos disponibles en paso 4 con alerta si insuficientes.
- [ ] **T13.** Vista `(dashboard)/artista/campanas/page.tsx`: lista de campañas con estado badge + acciones (ver detalle, continuar borrador, cancelar).
- [ ] **T14.** Vista `(dashboard)/artista/campanas/[id]/page.tsx`: detalle con reproductor de audio inline, imagen, estado de cada profesional vinculado (pendiente/aceptada/rechazada/entregada).
- [ ] **T15.** Tests: upload de archivo inválido rechazado; campaña sin audio no se puede enviar; saldo insuficiente al enviar → 402; envío exitoso retiene créditos correctamente.

---

## Archivos a crear

| Ruta | |
|------|-|
| `src/api/campanas.py` | |
| `src/api/profesionales_busqueda.py` | |
| `src/services/campana_service.py` | |
| `src/services/campana_upload_service.py` | |
| `src/models/dto/campanas.py` | |
| `app/(dashboard)/artista/campanas/page.tsx` | |
| `app/(dashboard)/artista/campanas/nueva/page.tsx` | |
| `app/(dashboard)/artista/campanas/[id]/page.tsx` | |
| `components/campanas/CampanaWizard.tsx` | |
| `components/campanas/ProfesionalPicker.tsx` | |
| `components/campanas/CampanaStatusBadge.tsx` | |
| `components/campanas/AudioPlayer.tsx` | |
| `tests/integration/test_campanas.py` | |

---

## Tests / validaciones

- `POST /campanas/:id/upload/audio` con PDF → 415.
- `POST /campanas/:id/upload/audio` con MP3 >50MB → 413.
- `POST /campanas/:id/upload/audio` con MP3 válido → objeto en S3/LocalStack con clave `campanas-audio/{id}/...`, `url_audio` actualizada en BD.
- `POST /campanas/:id/enviar` con 3 profesionales y artista con 2 créditos → 402 `insufficient_credits`.
- `POST /campanas/:id/enviar` con saldo suficiente → estado `enviada`, wallet -3, transacciones registradas, emails disparados.
- `DELETE /campanas/:id` en estado `enviada` → 409.
- `DELETE /campanas/:id` en estado `borrador` → objetos S3 eliminados, registro BD eliminado.
- Profesional no aprobado no aparece en `GET /profesionales/disponibles`.
- Las URLs de audio/imagen retornadas al cliente son presigned URLs con TTL (no URLs permanentes de S3).

## Notas de implementación

- `StorageService` (definido en Fase 04) es el único punto de contacto con S3. Los endpoints de upload nunca usan `boto3` directamente.
- Las claves S3 siguen el patrón `{bucket-lógico}/{entidad_id}/{filename}`. El bucket físico de AWS se configura en `AWS_S3_BUCKET`; los prefijos distinguen el tipo de contenido.
- En dev, `AWS_ENDPOINT_URL=http://localstack:4566` y credenciales dummy (`test/test`) hacen que `S3Provider` apunte a LocalStack sin ningún cambio de código.
- En prod, basta con setear `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_S3_BUCKET` reales y dejar `AWS_ENDPOINT_URL` vacío.
- Para cambiar a GCS o Azure en el futuro: implementar `GCSProvider` o `AzureProvider` con el mismo Protocol de Fase 04, y cambiar `STORAGE_PROVIDER=gcs` en el env. Sin tocar los endpoints.
- Los uploads grandes (ZIP ≤100MB) deben usar `multipart_upload` de S3 para eficiencia. `S3Provider.upload()` debe detectar archivos >10MB y usar multipart automáticamente.
- Configurar CORS en el bucket S3 para permitir que el browser descargue los presigned URLs desde el dominio de la app.

---

- **T1-T11:** `developer-skill`.
- **T12-T14:** `frontend-skill`.
- **T15:** `testing-skill`.

---

## PROGRESO

- [ ] T1 — POST /campanas (crear borrador)
- [ ] T2 — PATCH /campanas/:id
- [ ] T3 — Upload audio
- [ ] T4 — Upload imagen
- [ ] T5 — Upload material ZIP
- [ ] T6 — GET /profesionales/disponibles
- [ ] T7 — POST /campanas/:id/profesionales
- [ ] T8 — POST /campanas/:id/enviar
- [ ] T9 — GET /campanas (lista artista)
- [ ] T10 — GET /campanas/:id (detalle)
- [ ] T11 — DELETE /campanas/:id
- [ ] T12 — Vista wizard nueva campaña
- [ ] T13 — Vista lista campañas
- [ ] T14 — Vista detalle campaña
- [ ] T15 — Tests

**Última sesión:** —
**Próximo paso al reanudar:** T1 — endpoint `POST /campanas` en `src/api/campanas.py` con guard `require_artista` y body `{titulo, descripcion, genero_id}`.
