/**
 * Cliente HTTP de la API de Resuena.
 *
 * Todas las llamadas pasan por el rewrite same-origin `/api/*` (ver
 * next.config.mjs), de modo que la cookie de sesión HttpOnly viaja como
 * first-party. Por eso se usa `credentials: "include"` y `cache: "no-store"`.
 */

const BASE = "/api";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;
  /** Código de dominio del backend (p. ej. "LOCKED", "VALIDATION_ERROR"). */
  readonly code: string | null;

  constructor(
    status: number,
    message: string,
    detail?: unknown,
    code: string | null = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
    this.code = code;
  }
}

type Json = Record<string, unknown> | unknown[];

/** Extrae {message, code} legibles del cuerpo de error de FastAPI / dominio. */
function parseError(
  body: unknown,
  fallback: string,
): { message: string; code: string | null } {
  if (body && typeof body === "object") {
    // Envelope de dominio: { error: { code, message } }.
    const error = (body as { error?: { code?: string; message?: string } }).error;
    if (error && typeof error.message === "string") {
      return { message: error.message, code: error.code ?? null };
    }
    const mensaje = (body as { mensaje?: unknown }).mensaje;
    if (typeof mensaje === "string") return { message: mensaje, code: null };
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === "string") return { message: detail, code: null };
    // Errores de validación 422 de FastAPI: lista de {loc, msg}.
    if (Array.isArray(detail) && detail.length > 0) {
      const first = detail[0] as { msg?: string };
      if (first?.msg) return { message: first.msg, code: "VALIDATION_ERROR" };
    }
  }
  return { message: fallback, code: null };
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
        ...(options.headers ?? {}),
      },
      ...options,
    });
  } catch {
    throw new ApiError(0, "No se pudo conectar con el servidor. Reintenta.");
  }

  const isJson = res.headers
    .get("content-type")
    ?.includes("application/json");
  const body = isJson ? await res.json().catch(() => null) : null;

  if (!res.ok) {
    const { message, code } = parseError(body, `Error ${res.status}`);
    throw new ApiError(res.status, message, body, code);
  }
  return body as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, data?: Json) =>
    request<T>(path, {
      method: "POST",
      body: data === undefined ? undefined : JSON.stringify(data),
    }),
  put: <T>(path: string, data?: Json) =>
    request<T>(path, {
      method: "PUT",
      body: data === undefined ? undefined : JSON.stringify(data),
    }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
