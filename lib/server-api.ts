/**
 * Cliente HTTP para Server Components.
 *
 * A diferencia de `lib/api.ts` (que corre en el navegador y usa el rewrite
 * same-origin `/api/*`), los Server Components corren dentro del contenedor de
 * Next y deben llamar al backend directamente. Se reenvía la cookie de sesión
 * tomada de `next/headers` para que el backend autentique la petición.
 */

// Nota: este módulo es solo para Server Components (usa next/headers). No
// importar desde componentes cliente.
import { cookies } from "next/headers";

const API_INTERNAL_URL = process.env.API_INTERNAL_URL || "http://localhost:8000";

export class ServerApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ServerApiError";
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const cookieHeader = cookies().toString();

  let res: Response;
  try {
    res = await fetch(`${API_INTERNAL_URL}/api${path}`, {
      cache: "no-store",
      ...options,
      headers: {
        "Content-Type": "application/json",
        // Reenvía la sesión del usuario al backend.
        cookie: cookieHeader,
        ...(options.headers ?? {}),
      },
    });
  } catch {
    throw new ServerApiError(0, "No se pudo conectar con el servidor.");
  }

  if (!res.ok) {
    throw new ServerApiError(res.status, `Error ${res.status} en ${path}`);
  }

  // 204 No Content u otros sin cuerpo JSON.
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const serverApi = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
};
