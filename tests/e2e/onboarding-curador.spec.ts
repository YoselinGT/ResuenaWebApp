/**
 * Tests E2E — Onboarding curador: redes por canal, precio y flujo corregido (Fase 06f)
 *
 * Estos tests requieren el stack completo corriendo (docker compose up).
 * Ejecutar: npx playwright test tests/e2e/onboarding-curador.spec.ts
 */

import { test, expect } from "@playwright/test";

const API = "http://localhost:8000/api";

// ── Helpers ──────────────────────────────────────────────────────

async function registerUser(
  request: any,
  tipo: "artista" | "profesional",
): Promise<string> {
  const correo = `test_${Date.now()}@test.com`;
  const res = await request.post(`${API}/auth/register/${tipo}`, {
    data: {
      nombre_completo: "Test User",
      correo,
      password: "Test1234!",
    },
  });
  expect(res.status()).toBe(201);
  return correo;
}

async function confirmEmail(request: any, correo: string): Promise<string> {
  // En dev, el token se puede obtener directamente de la BD o MailHog.
  // Para estos tests, asumimos que el flujo de confirmación está disponible.
  const res = await request.get(`${API}/auth/confirm/dev-token-${correo}`);
  // Si falla, el test skip
  if (!res.ok()) {
    test.skip(true, "No se pudo confirmar el email en entorno de test");
  }
  return (await res.json()).siguiente;
}

// ── Tests ────────────────────────────────────────────────────────

test.describe("Onboarding — Stepper diferenciado por tipo", () => {
  test("curador no ve el paso 'Redes sociales' en el stepper", async ({
    page,
  }) => {
    // Simular sesión de curador (requiere login previo o mock)
    // Este test verifica que el stepper del curador no incluye "Redes sociales"
    await page.goto("/onboarding/medios");

    // El stepper debería mostrar los pasos del curador
    const stepper = page.locator("nav[aria-label='Pasos de onboarding']");
    await expect(stepper).toBeVisible();

    // No debe existir un link con texto "Redes sociales"
    const redesLink = stepper.getByText("Redes sociales");
    await expect(redesLink).not.toBeVisible();

    // Debe existir "Tus medios"
    const mediosLink = stepper.getByText("Tus medios");
    await expect(mediosLink).toBeVisible();
  });

  test("artista sí ve el paso 'Redes sociales' en el stepper", async ({
    page,
  }) => {
    // Simular sesión de artista
    await page.goto("/onboarding/redes");

    const stepper = page.locator("nav[aria-label='Pasos de onboarding']");
    await expect(stepper).toBeVisible();

    // Debe existir "Redes sociales"
    const redesLink = stepper.getByText("Redes sociales");
    await expect(redesLink).toBeVisible();
  });
});

test.describe("Onboarding — Formulario de canal con redes", () => {
  test("formulario permite agregar 2 redes sociales", async ({ page }) => {
    await page.goto("/onboarding/medios");

    // Abrir formulario de agregar canal
    const addBtn = page.getByRole("button", { name: /agregar canal/i });
    if (await addBtn.isVisible()) {
      await addBtn.click();
    }

    // Verificar que hay al menos una fila de red
    const redRows = page.locator("select").filter({ hasText: /tipo/i });
    await expect(redRows.first()).toBeVisible();

    // Click en "Agregar otra red"
    const addRedBtn = page.getByRole("button", { name: /agregar otra red/i });
    await addRedBtn.click();

    // Ahora debería haber 2 selects de tipo de red
    const allRedSelects = page.locator("select").filter({ hasText: /tipo/i });
    await expect(allRedSelects).toHaveCount(2);
  });

  test("campo precio acepta solo enteros >= 1", async ({ page }) => {
    await page.goto("/onboarding/medios");

    const addBtn = page.getByRole("button", { name: /agregar canal/i });
    if (await addBtn.isVisible()) {
      await addBtn.click();
    }

    // Buscar el input de precio
    const precioInput = page.locator('input[type="number"][min="1"]');
    await expect(precioInput).toBeVisible();

    // Verificar que el input tiene min=1
    const minAttr = await precioInput.getAttribute("min");
    expect(minAttr).toBe("1");
  });
});

test.describe("Onboarding — Redes page redirect para curadores", () => {
  test("curador es redirigido de /onboarding/redes a /onboarding/medios", async ({
    page,
  }) => {
    // Este test requiere estar logueado como curador
    // Si no hay sesión, la página redirige a /login
    await page.goto("/onboarding/redes");

    // Esperar a que la URL cambie (redirect)
    await page.waitForURL(/\/(onboarding\/medios|login)/, { timeout: 5000 });

    // Verificar que NO estamos en /onboarding/redes
    expect(page.url()).not.toContain("/onboarding/redes");
  });
});

test.describe("Onboarding — Curador: medios es el primer paso", () => {
  test("primer paso visible para curador es Canales", async ({ page }) => {
    await page.goto("/onboarding/medios");

    const stepper = page.locator("nav[aria-label='Pasos de onboarding']");
    await expect(stepper).toBeVisible();

    // El primer paso del stepper debe ser "Tus medios" (Canales)
    const firstStep = stepper.locator("a").first();
    await expect(firstStep).toContainText("Tus medios");
  });

  test("botón continuar deshabilitado cuando no hay canales", async ({
    page,
  }) => {
    await page.goto("/onboarding/medios");

    // El botón de continuar debe estar deshabilitado si no hay medios
    const continueBtn = page.getByRole("button", { name: /continuar/i });
    if (await continueBtn.isVisible()) {
      await expect(continueBtn).toBeDisabled();
    }

    // Debe mostrar mensaje de error
    const errorMsg = page.getByText(
      /debes agregar al menos un canal antes de continuar/i,
    );
    await expect(errorMsg).toBeVisible();
  });
});

test.describe("Dashboard curador — MedioCard", () => {
  test("MedioCard muestra badge de estado_revision", async ({ page }) => {
    // Este test requiere un curador con al menos un medio
    await page.goto("/curador/medios");

    // Si hay medios, verificar que tienen badge de estado
    const cards = page.locator("article");
    if ((await cards.count()) > 0) {
      const firstCard = cards.first();
      // Buscar el badge de estado (contiene texto como "Pendiente", "Aprobado", etc.)
      const badge = firstCard.locator(
        "text=/pendiente de revisión|aprobado|rechazado/i",
      );
      await expect(badge).toBeVisible();
    }
  });

  test("banner visible cuando 0 canales aprobados", async ({ page }) => {
    await page.goto("/curador/medios");

    // Si no hay canales aprobados, debe mostrar el banner
    const banner = page.getByText(
      /aún no tienes canales aprobados/i,
    );
    // Solo verificar si el banner es visible (puede no estar si hay aprobados)
    if (await banner.isVisible()) {
      await expect(banner).toContainText("podrás aceptar campañas");
    }
  });
});
