#!/bin/bash
# init-s3.sh — Crea los buckets S3 en LocalStack al arrancar.
# LocalStack ejecuta automáticamente los scripts en /etc/localstack/init/ready.d/
# cuando el servicio S3 está listo.

set -euo pipefail

REGION="${AWS_REGION:-us-east-1}"
BUCKET="${AWS_S3_BUCKET:-resuena-dev}"

echo "▶ Creando buckets S3 en LocalStack (region=${REGION})..."

# Bucket principal de la aplicación
awslocal s3 mb "s3://${BUCKET}" --region "${REGION}" 2>/dev/null || \
  echo "  bucket ${BUCKET} ya existe"

# Estructura lógica de prefijos (carpetas) usada por la app.
# En S3 las "carpetas" son solo prefijos de clave; creamos marcadores .keep
# para que sean visibles y documentar la convención de claves.
for prefix in campanas-audio campanas-imagen entregas-reels perfiles-avatar; do
  echo "" | awslocal s3 cp - "s3://${BUCKET}/${prefix}/.keep" --region "${REGION}"
done

# CORS para permitir uploads presigned desde el frontend en desarrollo.
awslocal s3api put-bucket-cors --bucket "${BUCKET}" --region "${REGION}" \
  --cors-configuration '{
    "CORSRules": [
      {
        "AllowedOrigins": ["http://localhost:3000"],
        "AllowedMethods": ["GET", "PUT", "POST", "HEAD"],
        "AllowedHeaders": ["*"],
        "ExposeHeaders": ["ETag"],
        "MaxAgeSeconds": 3000
      }
    ]
  }'

echo "✓ Buckets S3 listos:"
awslocal s3 ls
