/**
 * Validación de patrón de password en cliente.
 *
 * Espeja `src/services/password_service.validate_pattern`:
 * 8–128 caracteres con al menos una minúscula, una mayúscula, un número y
 * un símbolo (cualquier carácter no alfanumérico). El servidor es la fuente
 * de verdad; esto sólo da feedback inmediato.
 */

export const PASSWORD_MIN = 8;
export const PASSWORD_MAX = 128;

export type PasswordCheck = {
  label: string;
  ok: boolean;
};

export function passwordChecks(password: string): PasswordCheck[] {
  return [
    { label: "Mínimo 8 caracteres", ok: password.length >= PASSWORD_MIN },
    { label: "Una letra minúscula", ok: /[a-z]/.test(password) },
    { label: "Una letra mayúscula", ok: /[A-Z]/.test(password) },
    { label: "Un número", ok: /[0-9]/.test(password) },
    { label: "Un símbolo", ok: /[^A-Za-z0-9]/.test(password) },
  ];
}

export function isStrongPassword(password: string): boolean {
  return (
    password.length <= PASSWORD_MAX &&
    passwordChecks(password).every((c) => c.ok)
  );
}

/** Puntuación 0–4 para el medidor visual. */
export function passwordScore(password: string): number {
  if (!password) return 0;
  const passed = passwordChecks(password).filter((c) => c.ok).length;
  // 5 checks → escala a 0..4.
  return Math.min(4, Math.max(0, passed - 1));
}
