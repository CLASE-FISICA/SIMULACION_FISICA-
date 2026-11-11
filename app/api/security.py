"""Identidad de la petición.

ADAPTADOR TEMPORAL. La autenticación real es de BE3 (BE13) según el diseño de Seguridad
(SE01): JWT de corta duración en cookie httpOnly. Aquí solo se resuelve *quién* llama,
para que las rutas puedan exigir rol desde el primer día y el contrato no cambie cuando
llegue la implementación real.

En modo desarrollo se puede suplantar un usuario con las cabeceras X-Dev-Usuario y
X-Dev-Rol, para que el frontend y las pruebas trabajen sin el módulo de cuentas.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import Depends, Request

from app.api.errors import Problema
from app.config import ajustes

Rol = Literal["aprendiz", "instructor", "administrador"]


class Usuario:
    """Identidad mínima que consume la capa API."""

    __slots__ = ("ficha_id", "id", "rol")

    def __init__(self, id: str, rol: Rol, ficha_id: str | None = None) -> None:
        self.id = id
        self.rol = rol
        self.ficha_id = ficha_id


def _desde_cabeceras(request: Request) -> Usuario | None:
    if not ajustes.dev_mode:
        return None
    usuario = request.headers.get("X-Dev-Usuario")
    if not usuario:
        return None
    rol = request.headers.get("X-Dev-Rol", "aprendiz")
    if rol not in ("aprendiz", "instructor", "administrador"):
        rol = "aprendiz"
    return Usuario(id=usuario, rol=rol, ficha_id=request.headers.get("X-Dev-Ficha"))  # type: ignore[arg-type]


async def usuario_actual(request: Request) -> Usuario:
    """Resuelve el usuario de la petición o falla con 401."""
    usuario = _desde_cabeceras(request)
    if usuario is None:
        # BE3 sustituye esto por la validación del JWT de la cookie `sesion`.
        raise Problema(
            status=401,
            code="no_autenticado",
            title="Falta la sesión",
            detail="Se requiere una sesión válida para esta operación.",
            instance=str(request.url.path),
        )
    return usuario


UsuarioActual = Annotated[Usuario, Depends(usuario_actual)]


async def solo_instructor_o_admin(usuario: UsuarioActual) -> Usuario:
    if usuario.rol not in ("instructor", "administrador"):
        raise Problema(
            status=403,
            code="sin_permiso",
            title="La sesión no tiene permiso sobre este recurso",
            detail="Esta operación requiere rol de instructor o administrador.",
        )
    return usuario


InstructorOAdmin = Annotated[Usuario, Depends(solo_instructor_o_admin)]
