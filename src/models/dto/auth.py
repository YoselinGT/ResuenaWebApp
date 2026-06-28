"""DTOs Pydantic para los endpoints de autenticación."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterDTO(BaseModel):
    """Registro de artista o profesional (mismos campos)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    nombre_completo: str = Field(min_length=2, max_length=255)
    correo: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginDTO(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    correo: EmailStr
    password: str = Field(min_length=1, max_length=128)


class OTPVerifyDTO(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    pre_auth_session_id: str = Field(min_length=8, max_length=128)
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ForgotPasswordDTO(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    correo: EmailStr


class ResetPasswordDTO(BaseModel):
    password: str = Field(min_length=8, max_length=128)


class AplicarDTO(BaseModel):
    """Solicitud de aplicación de un profesional ya confirmado."""

    model_config = ConfigDict(str_strip_whitespace=True)

    tipo_profesional: str = Field(min_length=2, max_length=50)
    url_portfolio: str | None = Field(default=None, max_length=500)


# ── Respuestas ───────────────────────────────────────────────────
class LoginResponseDTO(BaseModel):
    """Respuesta del login: requiere verificar OTP a continuación."""

    pre_auth_session_id: str
    otp_required: bool = True
    mensaje: str = "Se envió un código de verificación a tu correo."


class UsuarioPublicoDTO(BaseModel):
    """Datos públicos del usuario autenticado (nunca incluye password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    nombre_completo: str
    correo: EmailStr
    tipo: str
