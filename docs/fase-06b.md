# Fase 06b — Admin: Gestión de paquetes de créditos

> **Estado:** `[ ]` pendiente · **Días estimados:** 2 · **Modelo:** `claude-sonnet-4-6`
> **Skills:** `developer-skill`, `frontend-skill`
> **Pre-requisitos:** Fase 02 `[x]`, Fase 06 `[x]`

---

## Contexto

La fase 06 implementó el sistema de créditos con paquetes hardcodeados (5/10/20/50 créditos
a precio fijo en MXN). Esta fase lo reemplaza con un panel admin configurable y migra la
lógica de precios a USD con `price_data` dinámico en Stripe.

### Modelo de precios definitivo

**Todo en USD. Sin tipo de cambio. Sin referencia MXN.**

**Crédito individual (sin paquete):**
El artista puede comprar créditos sueltos al precio fijo `precio_credito_individual_usd`
(default `$2.00 USD`). Vive en `parametros_config`.

**Paquetes (descuento por volumen):**
El admin define `cantidad_creditos` y `precio_total_usd`. El sistema calcula:
```
precio_por_credito_usd     = precio_total_usd / cantidad_creditos
stripe_fee_estimado_usd    ≈ precio_total_usd × 0.036 + 0.17
artista_paga_estimado_usd  = precio_total_usd + stripe_fee_estimado_usd
curador_recibe_por_credito = precio_por_credito_usd × (100 - comision_pct) / 100
resuena_por_credito        = precio_por_credito_usd × comision_pct / 100
```
**Ningún campo derivado se almacena en BD** — todos se calculan en `paquetes_service.calcular_campos()`.

**Stripe — `price_data` dinámico:**
No hay Price objects ni Product IDs en Stripe. El backend calcula el monto y lo pasa directamente:
```python
session = stripe.checkout.Session.create(
    payment_method_types=["card"],
    line_items=[{
        "price_data": {
            "currency": "usd",
            "unit_amount": round(artista_paga_usd * 100),  # centavos
            "product_data": {"name": f"{paquete.nombre} — {paquete.cantidad_creditos} créditos"},
        },
        "quantity": 1,
    }],
    mode="payment",
    metadata={
        "paquete_id": str(paquete_id),
        "usuario_id": str(usuario_id),
        "cantidad_creditos": str(paquete.cantidad_creditos),
        "tipo_pago": "nacional",  # el real llega en el webhook
    },
    success_url=...,
    cancel_url=...,
)
```
El webhook lee `metadata.cantidad_creditos` para acreditar al wallet y registra el `amount_total`
real de Stripe en `creditos_transacciones.monto_usd` para trazabilidad exacta del fee real cobrado.

**Comisión de Resuena:**
- Parámetro global `comision_resuena_pct` (default 50%) aplica a todos los paquetes.
- Cada paquete puede sobrescribir con su propio `comision_pct` (NULL = usar global).
- El curador recibe `(100 - comision_pct)%` del valor del crédito al entregar contenido.

**Wallet — Modelo A (por artista, sin cambios):**
Cada artista tiene su propia wallet. Ya implementado en fase 02 y fase 06. No hay wallet
del sello. El sello gestiona qué campañas propone, pero los créditos siempre pertenecen
al artista. No hay cambios de código necesarios aquí.

### Comisiones de Stripe — tarifas oficiales México (stripe.com/mx/pricing)

Todos los fees se configuran en `parametros_config` para que el admin los ajuste sin tocar código.
El sistema aplica el fee correcto según el escenario de pago detectado o configurado.

#### Tarifa base — tarjeta nacional mexicana
```
fee = precio_neto × stripe_pct_nacional + stripe_fixed_usd
```
| Parámetro | Valor oficial | Descripción |
|-----------|--------------|-------------|
| `stripe_pct_nacional` | `0.036` | 3.6% sobre el monto |
| `stripe_fixed_usd` | `0.17` | $3.00 MXN ≈ $0.17 USD fee fijo |

#### Cargos adicionales que se suman a la tarifa base

| Parámetro | Valor oficial | Cuándo aplica |
|-----------|--------------|----------------|
| `stripe_pct_internacional` | `0.005` | +0.5% si la tarjeta es de otro país |
| `stripe_pct_conversion_moneda` | `0.02` | +2% si hay conversión de moneda (USD → MXN en cuenta MX) |
| `stripe_pct_disputa` | `0.0` | No es %, es monto fijo (ver abajo) |
| `stripe_fixed_disputa_usd` | `8.57` | $150 MXN ≈ $8.57 USD por disputa abierta |

#### Meses sin intereses (MSI) — cargo adicional sobre la tarifa base

<cite index="41-1">Solo disponible para cuentas Stripe México, tarjetas de crédito de consumo emitidas en México,
en MXN. Stripe cobra un fee adicional que varía según el número de cuotas.</cite>

**⚠ IMPORTANTE:** MSI requiere que el artista pague en MXN. Como Resuena cobra en USD,
MSI **no aplica** en la integración actual. Documentado aquí para el caso de que en el futuro
se agregue un flujo de pago en MXN.

| Parámetro | Valor oficial | Cuándo aplica |
|-----------|--------------|----------------|
| `stripe_pct_msi_3meses` | `0.05` | +5% a 3 meses |
| `stripe_pct_msi_6meses` | `0.07` | +7% (estimado) a 6 meses |
| `stripe_pct_msi_9meses` | `0.09` | +9% (estimado) a 9 meses |
| `stripe_pct_msi_12meses` | `0.11` | +11% (estimado) a 12 meses |

#### Métodos de pago alternativos (no tarjeta)

| Método | Tarifa oficial | Parámetro config |
|--------|---------------|-----------------|
| OXXO Pay | 4% + $3 MXN (~$0.17 USD) | `stripe_pct_oxxo` = `0.04` |
| Transferencia bancaria | 4% + $3 MXN (~$0.17 USD) | `stripe_pct_transferencia` = `0.04` |

#### Fórmula de cálculo del precio al artista

El servicio `paquetes_service.calcular_precio_artista()` recibe el escenario de pago
y devuelve cuánto debe pagar el artista para que Resuena reciba exactamente `precio_neto`:

```python
def calcular_precio_artista(
    precio_neto_usd: Decimal,
    escenario: str = "nacional",      # "nacional" | "internacional" | "oxxo"
    con_conversion: bool = False,
) -> Decimal:
    """
    Despeja precio_artista de la ecuación:
      precio_neto = precio_artista × (1 - pct_total) - fixed_usd
      precio_artista = (precio_neto + fixed_usd) / (1 - pct_total)
    """
    pct = config.stripe_pct_nacional   # 0.036 (base siempre)

    if escenario == "internacional":
        pct += config.stripe_pct_internacional    # +0.005
    elif escenario == "oxxo":
        pct = config.stripe_pct_oxxo              # 0.04 reemplaza base

    if con_conversion:
        pct += config.stripe_pct_conversion_moneda  # +0.02

    fixed = config.stripe_fixed_usd               # 0.17

    precio_artista = (precio_neto_usd + fixed) / (1 - pct)
    return round(precio_artista, 2)
```

**Ejemplo práctico — paquete Pro (precio_neto = $18.00 USD):**

| Escenario | pct_total | fee | Artista paga |
|-----------|-----------|-----|-------------|
| Tarjeta nacional MX | 3.6% + $0.17 | $0.83 | **$18.83 USD** |
| Tarjeta internacional | 4.1% + $0.17 | $0.94 | **$18.94 USD** |
| Internacional + conversión | 6.1% + $0.17 | $1.26 | **$19.26 USD** |
| OXXO | 4% + $0.17 | $0.92 | **$18.92 USD** |

#### Estrategia de Resuena para el escenario de cobro

Dado que Resuena cobra en USD y tiene cuenta en México, el escenario más probable es
**tarjeta internacional con conversión de moneda** (el banco mexicano de Resuena recibe USD
pero Stripe puede cobrar conversión según la configuración de la cuenta).

**Recomendación:** usar el escenario `internacional` como default conservador en el cálculo.
Si la cuenta Stripe está configurada para recibir y liquidar en USD directamente (sin conversión),
usar `nacional` sin conversión.

El admin puede configurar el escenario default con `stripe_escenario_default`
(valores: `"nacional"` | `"internacional"` | `"oxxo"`).

### Parámetros globales en `parametros_config` (nuevos)

| Clave | Default | Descripción |
|-------|---------|-------------|
| `precio_credito_individual_usd` | `2.00` | Precio de 1 crédito suelto en USD (neto para Resuena) |
| `comision_resuena_pct` | `50` | % del crédito que retiene Resuena al transferir al curador |
| `stripe_pct_nacional` | `0.036` | Fee % Stripe tarjeta nacional mexicana |
| `stripe_fixed_usd` | `0.17` | Fee fijo Stripe por transacción ($3 MXN ≈ $0.17 USD) |
| `stripe_pct_internacional` | `0.005` | Fee adicional % por tarjeta internacional |
| `stripe_pct_conversion_moneda` | `0.02` | Fee adicional % por conversión de moneda |
| `stripe_pct_oxxo` | `0.04` | Fee % para pagos OXXO (reemplaza al nacional) |
| `stripe_fixed_disputa_usd` | `8.57` | Fee fijo por disputa abierta ($150 MXN ≈ $8.57 USD) |
| `stripe_escenario_default` | `"nacional"` | Escenario de pago para calcular precio al artista |

**Nota:** Los fees de MSI (meses sin intereses) están documentados en la sección anterior
pero NO se seedean como parámetros activos porque MSI requiere pagos en MXN y Resuena
cobra en USD. Si en el futuro se habilita un flujo en MXN, agregar los parámetros MSI.

Los parámetros anteriores `precio_credito_mxn` y `porcentaje_comision` quedan en BD
como datos históricos. Los nuevos conviven con ellos.

### Layout de la página (diseño aprobado)

```
┌─────────────────────────────────────────────────┐
│ Paquetes de créditos           [3 paquetes]     │
│ Define paquetes y el precio individual.          │
├─────────────────────────────────────────────────┤
│ CONFIGURACIÓN GLOBAL DE CRÉDITOS               │
│ [Precio crédito individual $2.00 USD]           │
│ [Comisión Resuena 50%]                         │
├─────────────────────────────────────────────────┤
│ NUEVO PAQUETE                                   │
│ [Nombre] [Créditos] [Precio total USD] [Com%]  │
│ [Descripción]  → preview calculado en tiempo real│
│ ☐ Activo  ☐ Visible  ☐ Destacado  [Crear]     │
├─────────────────────────────────────────────────┤
│ PAQUETES EXISTENTES                             │
│ ┌─ card (destacada = borde accent) ──────────┐ │
│ │ [Nombre★] [Créditos] [Precio USD] [Com%]   │ │
│ │ $/c: $1.80 → curador $0.90 / Resuena $0.90│ │
│ │ Artista paga est: $18.82 USD               │ │
│ │     ● Activo  ☑ Visible   [Guardar]        │ │
│ └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### `activo` vs `visible`

| activo | visible | Resultado |
|--------|---------|-----------|
| true | true | Aparece en catálogo artista + acepta compras |
| true | false | No visible al artista, acepta compras (paquetes privados) |
| false | cualquiera | No acepta nuevas compras |

`GET /creditos/paquetes` (artista) filtra `activo=true AND visible=true`.
`GET /admin/paquetes` retorna todos sin filtro.

---

## Tareas

### Backend

- [ ] **T1.** Migración Alembic `0006_paquetes_usd.py`:
  ```sql
  ALTER TABLE paquetes_creditos
    ADD COLUMN precio_total_usd NUMERIC(10,2),
    ADD COLUMN comision_pct INTEGER DEFAULT NULL;
  
  INSERT INTO parametros_config (clave, valor_cifrado, es_secreto, descripcion)
  VALUES
    ('precio_credito_individual_usd', '2.00',   false, 'Precio neto de 1 crédito suelto en USD'),
    ('comision_resuena_pct',          '50',     false, 'Comisión % que retiene Resuena al curador'),
    ('stripe_pct_nacional',           '0.036',  false, 'Fee % Stripe tarjeta nacional MX'),
    ('stripe_fixed_usd',              '0.17',   false, 'Fee fijo Stripe por transacción (en USD)'),
    ('stripe_pct_internacional',      '0.005',  false, 'Fee adicional % tarjeta internacional'),
    ('stripe_pct_conversion_moneda',  '0.02',   false, 'Fee adicional % conversión de moneda'),
    ('stripe_pct_oxxo',               '0.04',   false, 'Fee % OXXO Pay (reemplaza nacional)'),
    ('stripe_fixed_disputa_usd',      '8.57',   false, 'Fee fijo USD por disputa ($150 MXN)'),
    ('stripe_escenario_default',      'nacional', false, 'Escenario default: nacional|internacional|oxxo')
  ON CONFLICT (clave) DO NOTHING;
  
  -- Backfill inicial: precio_total_usd = $2.00 × cantidad_creditos (base de partida)
  UPDATE paquetes_creditos
  SET precio_total_usd = ROUND((cantidad_creditos * 2.00)::numeric, 2)
  WHERE precio_total_usd IS NULL;
  ```
  **`downgrade`**: `DROP COLUMN precio_total_usd`, `DROP COLUMN comision_pct`,
  `DELETE FROM parametros_config WHERE clave IN (...)`.

- [ ] **T2.** Servicio `paquetes_service.py` (nuevo, reemplaza la lógica hardcodeada en `stripe_service`):
    - `calcular_precio_artista(precio_neto, escenario, con_conversion) -> Decimal` — aplica la
      fórmula `(precio_neto + stripe_fixed_usd) / (1 - pct_total)` según escenario. Lee todos
      los `stripe_pct_*` de `parametros_config`.
    - `calcular_campos(paquete, comision_global, stripe_config) -> dict` — calcula todos los campos derivados:
      `precio_por_credito_usd`, `artista_paga_usd` (según `stripe_escenario_default`),
      `stripe_fee_estimado_usd`, `curador_recibe_por_credito_usd`, `resuena_por_credito_usd`.
      **Ningún campo derivado se almacena en BD.**
    - `list_all(db) -> list[PaqueteAdminResponse]` — todos los paquetes + campos calculados + `transacciones_count`.
    - `list_activos(db) -> list[PaquetePublicoResponse]` — solo `activo=true AND visible=true`.
    - `create(db, data) -> Paquete`
    - `update(db, id, data) -> Paquete` — valida que si `transacciones_count > 0` no cambia `cantidad_creditos`.
    - `get_comision_efectiva(paquete, comision_global) -> int` — `paquete.comision_pct or comision_global`.

- [ ] **T3.** Endpoint `GET /admin/paquetes` — lista todos con campos calculados + `transacciones_count`. Solo Admin.

- [ ] **T4.** Endpoint `POST /admin/paquetes` — body:
  ```json
  {
    "nombre": "Pro",
    "cantidad_creditos": 10,
    "precio_total_usd": 18.00,
    "comision_pct": null,
    "descripcion": "Ideal para campañas medianas.",
    "activo": true,
    "visible": true,
    "destacado": false
  }
  ```
  Solo Admin.

- [ ] **T5.** Endpoint `PATCH /admin/paquetes/:id` — campos editables: `nombre`, `descripcion`,
  `precio_total_usd`, `comision_pct`, `activo`, `visible`, `destacado`. Si `transacciones_count > 0`
  rechaza cambio de `cantidad_creditos` → 409 `creditos_inmutables`. El toggle de `activo` desde
  el badge hace PATCH inmediato (sin esperar "Guardar"). Solo Admin.

- [ ] **T6.** Endpoint `GET /admin/config/creditos` — retorna todos los parámetros de config de créditos y Stripe: `{precio_credito_individual_usd, comision_resuena_pct, stripe_pct_nacional, stripe_fixed_usd, stripe_pct_internacional, stripe_pct_conversion_moneda, stripe_pct_oxxo, stripe_fixed_disputa_usd, stripe_escenario_default}`.

- [ ] **T7.** Endpoint `PATCH /admin/config/creditos` — actualiza cualquiera de los 9 parámetros de créditos/Stripe en `parametros_config`. Body acepta los campos a actualizar (todos opcionales). Solo Admin. Bitácora con diff de los valores cambiados.

- [ ] **T8.** Actualizar `GET /creditos/paquetes` — ahora retorna los paquetes con `precio_total_usd`
  y campos calculados (incluyendo `artista_paga_estimado_usd` y el `desglose` de transparencia).
  Usar `paquetes_service.list_activos()`.

- [ ] **T9.** Actualizar `stripe_service.create_checkout_session` — usar `price_data` dinámico:
    - Llamar a `paquetes_service.calcular_precio_artista(precio_neto, escenario_default)` para
      obtener `artista_paga_usd` y convertir a centavos (`unit_amount = round(artista_paga_usd * 100)`).
    - Para compras individuales: `precio_neto = precio_credito_individual_usd × cantidad`.
    - Pasar `metadata` con `paquete_id`, `cantidad_creditos`, `precio_neto_usd`, `stripe_escenario`.

- [ ] **T10.** Actualizar `stripe_service.handle_webhook` — leer `metadata.cantidad_creditos`
  del evento para acreditar. Ya no confiar en un monto hardcodeado.

### Frontend

- [ ] **T11.** Vista `(dashboard)/admin/paquetes/page.tsx` — Client component:
  ```tsx
  <PageHeader title="Paquetes de créditos" badge="{n} paquetes" />
  <ConfigGlobalCard config={config} onSaved={refetchConfig} />
  <NuevoPaqueteForm globalComision={config.comision_resuena_pct} onCreated={refetch} />
  <SectionLabel>Paquetes existentes</SectionLabel>
  <PaquetesList paquetes={paquetes} onSaved={refetch} />
  ```

- [ ] **T12.** Componente `ConfigGlobalCard.tsx`:
    - **Sección "Precios":**
        - "Precio crédito individual (USD)" — input decimal, default 2.00.
        - "Comisión Resuena %" — input number 1–99, default 50.
    - **Sección "Comisiones de Stripe" (colapsable, expandir para editar):**
        - "Fee % tarjeta nacional" — default 3.6%, readonly con tooltip "Actualizar solo si Stripe cambia sus tarifas".
        - "Fee fijo por transacción (USD)" — default $0.17.
        - "Fee adicional % tarjeta internacional" — default 0.5%.
        - "Fee adicional % conversión de moneda" — default 2.0%.
        - "Fee % OXXO" — default 4.0%.
        - "Fee fijo disputa (USD)" — default $8.57.
        - "Escenario default" — selector: Nacional / Internacional / Internacional+conversión / OXXO.
    - **Preview calculado en tiempo real:** "Con escenario [X]: crédito de $2.00 neto → artista paga $2.10 USD".
    - Botón "Guardar configuración" → `PATCH /admin/config/creditos`.
    - Nota: "Los fees de Stripe son tarifas publicadas. Actualizarlos aquí no afecta lo que Stripe realmente cobra — solo cambia el monto que se cobra al artista."

- [ ] **T13.** Componente `NuevoPaqueteForm.tsx` — fila de campos + preview calculado en tiempo real:
    - Campos: Nombre, Créditos, Precio total USD, Comisión % (hereda global como default), Descripción.
    - Preview principal: `"10 créditos a $1.80/c · Artista paga est. $18.83 USD · Resuena $9.00 · Curador $9.00"`
    - Inmediatamente debajo del preview, nota de disclaimer en `var(--text-muted)` tamaño 11px:
      `"* El monto que paga el artista es una estimación basada en tarjeta nacional. El cargo real lo determina
      Stripe según el tipo y origen de la tarjeta — puede ser mayor en tarjetas internacionales."`
    - La nota NO va en tooltip — debe ser visible sin interacción.
    - Checkboxes: Activo, Visible, Destacado.

- [ ] **T14.** Componente `PaqueteCard.tsx` — card editable individual:
    - Grid: Nombre, Créditos (readonly si tiene transacciones + tooltip), Precio total USD, Comisión %.
    - Calculado (readonly): `$/crédito`, `artista paga est.`
    - Badge de estado `activo` (● Activo / ○ Pausado) — clic hace PATCH inmediato solo de `activo`.
    - Checkbox `visible` — espera botón "Guardar".
    - Botón "Guardar" deshabilitado si `isDirty = false`.
    - Desglose siempre visible debajo de la card:
      `"N créditos a $X.XX/c · Artista paga est. ~$Z.ZZ USD* · Resuena $R.RR · Curador $C.CC"`
    - Al lado del asterisco, ícono de info (ⓘ) con tooltip en desktop / texto expandible en móvil:
      `"Estimación basada en tarjeta nacional mexicana (3.6% + $0.17 USD). El cobro real varía según
      el tipo de tarjeta: internacional +0.5%, con conversión de moneda +2%, OXXO 4% flat."`
    - Si `destacado=true`: borde `var(--border-accent)` + badge "★ Más popular" inline.

- [ ] **T15.** Hook `usePaqueteCard(paquete, globalComision)`:
  ```typescript
  // Campos calculados derivados — nunca almacenados:
  const comisionEfectiva  = values.comision_pct ?? globalComision
  const ppc               = values.precio_total_usd / values.cantidad_creditos
  const stripeFee         = values.precio_total_usd * 0.036 + 0.17
  const artistaPaga       = values.precio_total_usd + stripeFee
  const curadorPorCredito = ppc * (1 - comisionEfectiva / 100)
  const resuenaPorCredito = ppc * (comisionEfectiva / 100)
  ```
  `toggleActivo` hace PATCH inmediato (`PATCH /admin/paquetes/:id` con solo `{activo}`).

- [ ] **T16.** Actualizar vista `(dashboard)/artista/creditos/page.tsx`:
    - Precio en cada `PaqueteCard` del artista: `"$18.83 USD est."` con el sufijo "est." en gris.
    - Bajo el precio, badge o texto pequeño: `"El monto final lo determina Stripe al momento del pago"`.
    - Al hacer clic en "Comprar" y antes de redirigir a Stripe Checkout, mostrar un modal de confirmación
      con el desglose completo y el disclaimer explícito:
      ```
      ┌────────────────────────────────────────────────┐
      │ Confirmar compra                               │
      ├────────────────────────────────────────────────┤
      │ Paquete Pro — 10 créditos                      │
      │                                                │
      │ Precio estimado:    ~$18.83 USD                │
      │                                                │
      │ ℹ️ El monto exacto lo determina Stripe según   │
      │ el tipo de tu tarjeta:                         │
      │ · Tarjeta nacional MX:     ~$18.83 USD         │
      │ · Tarjeta internacional:   ~$18.94 USD         │
      │ · Con conversión de moneda: ~$19.26 USD        │
      │                                                │
      │ Resuena no controla ni retiene estas           │
      │ diferencias — son fees directos de Stripe.     │
      ├────────────────────────────────────────────────┤
      │ [Cancelar]              [Ir a pagar →]         │
      └────────────────────────────────────────────────┘
      ```
    - El modal usa el sistema de diseño Resuena (dark mode, borde `var(--border-subtle)`).
    - Sección de transparencia bajo los paquetes: "De cada crédito: $X.XX USD al curador · $Y.YY USD a Resuena".
    - Opción de compra individual: "¿Prefieres comprar créditos sueltos? $2.00 USD/crédito" con input de cantidad
      y su propio botón "Comprar X créditos" que también abre el modal de confirmación con el mismo disclaimer.

### Tests

- [ ] **T17.** Tests backend:
    - `POST /admin/paquetes` como artista → 403.
    - `POST /admin/paquetes` con `precio_total_usd=18.00, cantidad_creditos=10` → 201; `calcular_campos` retorna `precio_por_credito_usd=1.80`, `curador_recibe=0.90`.
    - `GET /admin/paquetes` → incluye campos calculados correctos.
    - `PATCH /admin/paquetes/:id` cambiando `cantidad_creditos` en paquete con transacciones → 409 `creditos_inmutables`.
    - `PATCH /admin/paquetes/:id` `visible=false` → desaparece de `GET /creditos/paquetes`.
    - `PATCH /admin/config/creditos` actualiza `stripe_pct_internacional` → nuevo valor en BD + bitácora con diff.
    - `calcular_precio_artista($18.00, "nacional")` → `$18.83 USD`.
    - `calcular_precio_artista($18.00, "internacional")` → `$18.94 USD`.
    - `calcular_precio_artista($18.00, "internacional", con_conversion=True)` → `$19.26 USD`.
    - Migración 0006: `alembic upgrade head` → exit 0; `downgrade -1` → exit 0; 9 params nuevos en config.

---

## Archivos a crear / modificar

| Ruta | Acción |
|------|--------|
| `alembic/versions/0006_paquetes_usd.py` | crear |
| `src/services/paquetes_service.py` | crear |
| `src/models/dto/paquetes.py` | crear |
| `src/api/admin_paquetes.py` | crear |
| `src/services/stripe_service.py` | modificar — price_data dinámico |
| `src/api/creditos.py` | modificar — usar paquetes_service |
| `app/(dashboard)/admin/paquetes/page.tsx` | crear |
| `components/admin/ConfigGlobalCard.tsx` | crear |
| `components/admin/NuevoPaqueteForm.tsx` | crear |
| `components/admin/PaqueteCard.tsx` | crear |
| `hooks/usePaqueteCard.ts` | crear |
| `app/(dashboard)/artista/creditos/page.tsx` | modificar — USD + transparencia + modal |
| `components/creditos/ConfirmarCompraModal.tsx` | crear — modal con desglose y disclaimer |
| `tests/integration/test_admin_paquetes.py` | crear |

---

## Tests / validaciones clave

- Paquete 30 créditos / $54.00 USD / comision_pct=50 → `precio_por_credito=$1.80`, `curador_recibe=$0.90/c`, `total_curador=$27.00`, `artista_paga≈$56.12`.
- Admin cambia `comision_resuena_pct` a 60 → nuevo paquete hereda 60% como default.
- Stripe Checkout Session creado con `currency='usd'` y `unit_amount` en centavos.
- Webhook procesa `metadata.cantidad_creditos` para acreditar wallet.

---

## Notas para el agente

- **No tocar** `wallets`, `sello_artistas`, estados de campañas, ni nada de flujo de campañas. Eso va en fases 08 y 09.
- **No hay `precio_stripe_id`** — Stripe recibe el monto directamente como `price_data`.
- **No hay tipo de cambio MXN** — todo en USD. Sin equivalencias, sin conversión.
- El modelo A de wallet (por artista) **ya está implementado** en fase 02 y 06. No requiere cambios.
- El `comision_pct` por paquete puede ser `NULL` → se usa el global `comision_resuena_pct`.
- Todos los campos calculados van en `paquetes_service.calcular_campos()` — nunca en BD.

---

## Skill recomendado

- **T1:** `dba-skill`.
- **T2-T10:** `developer-skill`.
- **T11-T16:** `frontend-skill`.
- **T17:** `testing-skill`.

---

## PROGRESO

- [x] T1 — Migración 0006 (precio_total_usd, comision_pct, seed params nuevos)
- [x] T2 — paquetes_service (calcular_campos + CRUD)
- [x] T3 — GET /admin/paquetes
- [x] T4 — POST /admin/paquetes
- [x] T5 — PATCH /admin/paquetes/:id
- [x] T6 — GET /admin/config/creditos
- [x] T7 — PATCH /admin/config/creditos
- [x] T8 — Actualizar GET /creditos/paquetes → USD
- [x] T9 — Actualizar stripe_service → price_data dinámico
- [x] T10 — Actualizar handle_webhook → metadata.cantidad_creditos
- [x] T11 — Vista admin/paquetes/page.tsx
- [x] T12 — ConfigGlobalCard
- [x] T13 — NuevoPaqueteForm (con preview tiempo real)
- [x] T14 — PaqueteCard (editable + badge + desglose)
- [x] T15 — usePaqueteCard hook
- [x] T16 — Actualizar vista artista/creditos → USD + ConfirmarCompraModal con disclaimer de fee
- [x] T17 — Tests

**Última sesión:** 2026-07-07
**Próximo paso al reanudar:** Fase 07 — Géneros musicales + Configuración de categorías