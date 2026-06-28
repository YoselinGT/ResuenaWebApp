"""Tests de integración de onboarding/perfil y catálogos."""

from __future__ import annotations

ONB = "/api/onboarding"
CAT = "/api/catalogos"


async def _genero_ids(client, n=2) -> list[int]:
    r = await client.get(f"{CAT}/generos")
    return [g["id"] for g in r.json()[:n]]


async def test_catalogo_generos_retorna_20(client):
    r = await client.get(f"{CAT}/generos")
    assert r.status_code == 200
    assert len(r.json()) == 20


async def test_artista_completa_pasos(client, register_and_confirm):
    await register_and_confirm(client, "artista")
    gids = await _genero_ids(client, 2)

    assert (await client.put(f"{ONB}/generos", json={"genero_ids": gids})).status_code == 200
    assert (await client.put(f"{ONB}/idiomas", json={"codigos": ["es", "en"]})).status_code == 200
    assert (await client.put(f"{ONB}/regiones", json={"codigos": ["MX", "US"]})).status_code == 200
    assert (
        await client.put(
            f"{ONB}/preferencias",
            json={
                "apertura_musical": 70,
                "acepta_todos_idiomas": True,
                "tipo_lanzamientos": "ambos",
            },
        )
    ).status_code == 200
    assert (
        await client.post(f"{ONB}/redes", json={"tipo": "spotify", "url": "https://open.spotify.com/x"})
    ).status_code == 201

    prog = (await client.get(f"{ONB}/progreso")).json()
    assert prog["generos"] and prog["idiomas"] and prog["regiones"]
    assert prog["redes"] and prog["preferencias"]
    assert prog["medios"] is False  # el artista no tiene medios


async def test_progreso_parcial_solo_generos(client, register_and_confirm):
    await register_and_confirm(client, "artista")
    gids = await _genero_ids(client, 1)
    await client.put(f"{ONB}/generos", json={"genero_ids": gids})
    prog = (await client.get(f"{ONB}/progreso")).json()
    assert prog["generos"] is True
    assert prog["idiomas"] is False
    assert prog["regiones"] is False


async def test_genero_inexistente_422(client, register_and_confirm):
    await register_and_confirm(client, "artista")
    r = await client.put(f"{ONB}/generos", json={"genero_ids": [999999]})
    assert r.status_code == 422


async def test_idioma_inexistente_422(client, register_and_confirm):
    await register_and_confirm(client, "artista")
    r = await client.put(f"{ONB}/idiomas", json={"codigos": ["zz"]})
    assert r.status_code == 422


async def test_artista_no_puede_medios_403(client, register_and_confirm):
    await register_and_confirm(client, "artista")
    r = await client.post(f"{ONB}/medios", json={"nombre": "x", "tipo": "blog"})
    assert r.status_code == 403


async def test_curador_crea_dos_medios(client, register_and_confirm):
    await register_and_confirm(client, "profesional")
    gids = await _genero_ids(client, 2)

    r1 = await client.post(
        f"{ONB}/medios",
        json={
            "nombre": "Playlist",
            "tipo": "playlist",
            "genero_ids": gids,
            "audiencia_estimada": 5000,
        },
    )
    assert r1.status_code == 201
    assert sorted(r1.json()["genero_ids"]) == sorted(gids)

    r2 = await client.post(
        f"{ONB}/medios", json={"nombre": "FB", "tipo": "facebook", "genero_ids": gids[:1]}
    )
    assert r2.status_code == 201

    medios = (await client.get(f"{ONB}/medios")).json()
    assert len(medios) == 2
    assert (await client.get(f"{ONB}/progreso")).json()["medios"] is True


async def test_curador_medio_tipo_invalido_422(client, register_and_confirm):
    await register_and_confirm(client, "profesional")
    r = await client.post(f"{ONB}/medios", json={"nombre": "x", "tipo": "inventado"})
    assert r.status_code == 422


async def test_curador_update_y_softdelete_medio(client, register_and_confirm):
    await register_and_confirm(client, "profesional")
    gids = await _genero_ids(client, 2)
    mid = (
        await client.post(
            f"{ONB}/medios", json={"nombre": "M1", "tipo": "playlist", "genero_ids": gids}
        )
    ).json()["id"]

    upd = await client.put(
        f"{ONB}/medios/{mid}",
        json={"nombre": "M1 v2", "tipo": "playlist", "genero_ids": gids[:1]},
    )
    assert upd.status_code == 200
    assert upd.json()["nombre"] == "M1 v2"
    assert upd.json()["genero_ids"] == gids[:1]

    assert (await client.delete(f"{ONB}/medios/{mid}")).status_code == 204
    assert len((await client.get(f"{ONB}/medios")).json()) == 0
