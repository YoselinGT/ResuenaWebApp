"""Abstracción de almacenamiento de objetos en la nube.

Regla no negociable (CLAUDE.md): endpoints y services nunca usan boto3/aioboto3
directamente. Toda operación de archivos pasa por `StorageService`. La BD guarda
**claves** (ej. `perfiles-avatar/<uuid>.jpg`), nunca URLs; las URLs se generan
como presigned con TTL al momento de servir al cliente.

Diseño preparado para multi-proveedor: `StorageProvider` es un Protocol; hoy
existe `S3Provider` (aioboto3). Agregar GCS/Azure es implementar el mismo
Protocol y enrutarlo en la factory según `STORAGE_PROVIDER`.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol, runtime_checkable

import aioboto3
from botocore.config import Config

from src.config.settings import Settings, get_settings


@runtime_checkable
class StorageProvider(Protocol):
    """Contrato de un proveedor de almacenamiento de objetos."""

    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        """Sube `data` bajo `key`. Devuelve la clave almacenada."""
        ...

    async def delete(self, key: str) -> None:
        """Elimina el objeto en `key` (idempotente)."""
        ...

    async def presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        """Genera una URL presigned de lectura con TTL `expires_seconds`."""
        ...


class S3Provider:
    """Proveedor S3 sobre aioboto3 (async).

    Compatible con AWS S3 real y con LocalStack en dev vía `endpoint_url`. Para
    las URLs presigned en dev se usa `public_endpoint_url` (host alcanzable desde
    el navegador, p. ej. http://localhost:4566) porque SigV4 firma el host: si se
    firmara con el host interno (`localstack:4566`) el navegador no podría usarla.
    En producción `public_endpoint_url` es None y se usa el endpoint real.
    """

    def __init__(
        self,
        *,
        bucket: str,
        region: str,
        access_key: str,
        secret_key: str,
        endpoint_url: str | None = None,
        public_endpoint_url: str | None = None,
    ) -> None:
        self._bucket = bucket
        self._region = region
        self._access_key = access_key
        self._secret_key = secret_key
        self._endpoint_url = endpoint_url
        self._public_endpoint_url = public_endpoint_url
        self._session = aioboto3.Session()

    def _client(self, *, public: bool = False):
        endpoint = self._endpoint_url
        if public and self._public_endpoint_url:
            endpoint = self._public_endpoint_url
        # SigV4 explícito (algunas regiones AWS no aceptan SigV2). Con endpoint
        # custom (LocalStack) se fuerza path-style: el virtual-host style
        # (bucket.host) no resuelve contra LocalStack.
        s3_opts: dict = {}
        if self._endpoint_url:
            s3_opts["addressing_style"] = "path"
        config = Config(signature_version="s3v4", s3=s3_opts)
        return self._session.client(
            "s3",
            region_name=self._region,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            endpoint_url=endpoint,
            config=config,
        )

    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        async with self._client() as s3:
            await s3.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
        return key

    async def delete(self, key: str) -> None:
        async with self._client() as s3:
            await s3.delete_object(Bucket=self._bucket, Key=key)

    async def presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        async with self._client(public=True) as s3:
            return await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires_seconds,
            )


class StorageService:
    """Fachada de almacenamiento usada por services y endpoints.

    Delega en el `StorageProvider` configurado. Es la única vía permitida para
    operar archivos en la nube.
    """

    def __init__(self, provider: StorageProvider) -> None:
        self._provider = provider

    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        return await self._provider.upload(key, data, content_type)

    async def delete(self, key: str) -> None:
        await self._provider.delete(key)

    async def presigned_url(self, key: str, expires_seconds: int = 3600) -> str:
        return await self._provider.presigned_url(key, expires_seconds)


def _build_provider(settings: Settings) -> StorageProvider:
    """Construye el provider según `STORAGE_PROVIDER`."""
    if settings.storage_provider == "s3":
        return S3Provider(
            bucket=settings.aws_s3_bucket,
            region=settings.aws_region,
            access_key=settings.aws_access_key_id,
            secret_key=settings.aws_secret_access_key,
            endpoint_url=settings.aws_endpoint_url,
            public_endpoint_url=settings.aws_public_endpoint_url,
        )
    raise NotImplementedError(
        f"STORAGE_PROVIDER '{settings.storage_provider}' aún no implementado"
    )


@lru_cache
def get_storage_service() -> StorageService:
    """Instancia única de `StorageService` por proceso."""
    return StorageService(_build_provider(get_settings()))
