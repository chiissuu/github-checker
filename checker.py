# ==================================================
# 1. PREPARACIÓN Y DATOS
# ==================================================

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import tempfile
from http.client import HTTPException
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

# 1.1. Configuración

API_URL = "https://api.github.com"
API_VERSION = "2026-03-10"
TIMEOUT = 30
USUARIO_VALIDO = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?")
SALIDA = Path(__file__).resolve().parent / "resultados"


# 1.2. Errores y redirecciones

class ErrorChecker(Exception):
    pass


class SinRedirecciones(HTTPRedirectHandler):
    # No reenviar Authorization a destinos que no haya elegido el programa.
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


# ==================================================
# 2. CONSULTAS A GITHUB
# ==================================================

# 2.1. Mensajes de error HTTP

def describir_error(error: HTTPError) -> str:
    if error.code == 401:
        return "Token inválido o caducado. Actualiza GITHUB_TOKEN en esta terminal."
    if error.code == 404:
        return "GitHub no encuentra la cuenta o no permite acceder a ella."
    if error.code in (403, 429):
        espera = error.headers.get("Retry-After")
        reinicio = error.headers.get("X-RateLimit-Reset")
        if espera and espera.isdigit():
            return f"GitHub limita las peticiones. Espera al menos {espera} segundos."
        if error.headers.get("X-RateLimit-Remaining") == "0":
            try:
                fecha = datetime.fromtimestamp(int(reinicio), timezone.utc)
                return f"Límite agotado. Vuelve a probar después de {fecha.isoformat()}."
            except (TypeError, ValueError, OverflowError, OSError):
                return "Límite agotado. Espera a que GitHub renueve la cuota."
        return "GitHub ha denegado la petición o aplicado un límite temporal. Para unfollow, revisa Followers: Read and write."
    if error.code >= 500:
        return "GitHub no está disponible temporalmente. Prueba más tarde."
    return f"GitHub devolvió HTTP {error.code}. La petición no se ha confirmado."


# 2.2. Cliente HTTP

class ClienteGitHub:
    def __init__(self, token: str):
        self.token = token
        self.opener = build_opener(SinRedirecciones())

    def consultar(self, ruta: str):
        return self.solicitar(ruta, "GET")

    def dejar_de_seguir(self, usuario: str):
        if not USUARIO_VALIDO.fullmatch(usuario):
            raise ErrorChecker("Usuario inválido para unfollow.")
        self.solicitar(f"/user/following/{usuario}", "DELETE")

    def solicitar(self, ruta: str, metodo: str):
        if not ruta.startswith("/") or ruta.startswith("//"):
            raise ErrorChecker("Ruta de API inválida.")
        peticion = Request(
            API_URL + ruta,
            method=metodo,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": API_VERSION,
                "User-Agent": "github-checker",
            },
        )
        try:
            with self.opener.open(peticion, timeout=TIMEOUT) as respuesta:
                if metodo == "DELETE":
                    if respuesta.status != 204:
                        raise ErrorChecker("GitHub no confirmó el unfollow con HTTP 204.")
                    return None, respuesta.headers
                return json.load(respuesta), respuesta.headers
        except HTTPError as error:
            mensaje = describir_error(error)
            error.close()
            raise ErrorChecker(mensaje) from None
        except (URLError, TimeoutError, OSError, HTTPException):
            raise ErrorChecker("No se pudo completar la conexión con GitHub.") from None
        except (ValueError, UnicodeError):
            raise ErrorChecker("GitHub devolvió una respuesta JSON inválida.") from None


# 2.3. Validación de cuentas

def validar_cuenta(datos: object) -> dict:
    if not isinstance(datos, dict):
        raise ErrorChecker("Respuesta de cuenta inesperada.")
    identificador = datos.get("id")
    usuario = datos.get("login")
    if (
        type(identificador) is not int
        or identificador <= 0
        or not isinstance(usuario, str)
        or not USUARIO_VALIDO.fullmatch(usuario)
    ):
        raise ErrorChecker("GitHub devolvió una cuenta sin identificador o usuario válido.")
    return {"id": identificador, "usuario": usuario, "url": f"https://github.com/{usuario}"}


# 2.4. Descarga paginada

def obtener_cuentas(cliente: ClienteGitHub, usuario: str, relacion: str) -> dict[int, dict]:
    cuentas = {}
    pagina = 1
    while True:
        datos, cabeceras = cliente.consultar(
            f"/users/{usuario}/{relacion}?per_page=100&page={pagina}"
        )
        if not isinstance(datos, list):
            raise ErrorChecker("GitHub devolvió una lista inesperada.")
        anteriores = len(cuentas)
        for datos_cuenta in datos:
            cuenta = validar_cuenta(datos_cuenta)
            cuentas[cuenta["id"]] = cuenta
        print(f"  {relacion}: página {pagina}, {len(cuentas)} cuentas recibidas.")
        if not re.search(r'rel="next"', cabeceras.get("Link", "")):
            return cuentas
        if len(cuentas) == anteriores:
            raise ErrorChecker("La paginación no avanza. Repite el análisis más tarde.")
        # Construimos la siguiente ruta localmente para no enviar el token a URLs recibidas.
        pagina += 1


# ==================================================
# 3. ANÁLISIS Y EXPORTACIÓN
# ==================================================

# 3.1. Comparación por identificador

def comparar(seguidores: dict, seguidos: dict) -> list[dict]:
    return sorted(
        (cuenta for identificador, cuenta in seguidos.items() if identificador not in seguidores),
        key=lambda cuenta: cuenta["usuario"].casefold(),
    )


# 3.2. Escritura del informe

def escribir_informe(informe: dict, formato: str, directorio: Path) -> Path:
    directorio.mkdir(parents=True, exist_ok=True)
    destino = directorio / (
        f"personas_que_no_te_siguen_de_vuelta_github_{informe['usuario']}.{formato}"
    )
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", dir=directorio,
            prefix=".informe-", suffix=".tmp", delete=False,
        ) as archivo:
            temporal = Path(archivo.name)
            if formato == "json":
                json.dump(informe, archivo, ensure_ascii=False, indent=2)
                archivo.write("\n")
            elif formato == "csv":
                escritor = csv.DictWriter(archivo, fieldnames=["id", "usuario", "url"])
                escritor.writeheader()
                escritor.writerows(informe["cuentas"])
            else:
                archivo.write(f"GitHub Checker — {informe['usuario']}\n")
                archivo.write(f"Consulta UTC: {informe['consultado_en']}\n")
                archivo.write(f"No te siguen de vuelta: {len(informe['cuentas'])}\n\n")
                for cuenta in informe["cuentas"]:
                    archivo.write(cuenta["url"] + "\n")
        temporal.replace(destino)
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)
    return destino


# ==================================================
# 4. EJECUCIÓN DEL PROGRAMA
# ==================================================

# 4.1. Argumentos de consola

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Obtiene las cuentas de GitHub que sigues y no te siguen de vuelta."
    )
    parser.add_argument("--username", help="Tu usuario; debe coincidir con el propietario del token.")
    parser.add_argument("--format", choices=("txt", "csv", "json"), default="txt")
    parser.add_argument("--output-dir", type=Path, default=SALIDA, help="Carpeta de resultados.")
    return parser.parse_args(argv)


# 4.2. Flujo principal

def main(argv=None) -> int:
    args = parse_args(argv)
    try:
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if not token:
            raise ErrorChecker("Falta GITHUB_TOKEN. Cárgalo en esta misma terminal; consulta el README.")
        if not re.fullmatch(r"[A-Za-z0-9_]+", token):
            raise ErrorChecker("GITHUB_TOKEN tiene caracteres inesperados. Copia de nuevo el token.")
        cliente = ClienteGitHub(token)
        datos, _ = cliente.consultar("/user")
        propia = validar_cuenta(datos)
        usuario = propia["usuario"]
        if args.username and args.username.casefold() != usuario.casefold():
            raise ErrorChecker("--username debe ser el propietario del token. Omítelo para detectarlo.")
        print(f"Analizando la cuenta {usuario}...")
        seguidores = obtener_cuentas(cliente, usuario, "followers")
        seguidos = obtener_cuentas(cliente, usuario, "following")
        cuentas = comparar(seguidores, seguidos)
        informe = {
            "usuario": usuario,
            "consultado_en": datetime.now(timezone.utc).isoformat(),
            "seguidores": len(seguidores),
            "seguidos": len(seguidos),
            "no_te_siguen": len(cuentas),
            "cuentas": cuentas,
        }
        destino = escribir_informe(informe, args.format, args.output_dir)
        print(f"Seguidores: {len(seguidores)} | Seguidos: {len(seguidos)}")
        print(f"No te siguen de vuelta: {len(cuentas)}\nInforme: {destino}")
        return 0
    except ErrorChecker as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except OSError:
        print("Error al guardar el informe. Comprueba permisos y espacio disponible.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nAnálisis cancelado.", file=sys.stderr)
        return 130


# 4.3. Punto de entrada

if __name__ == "__main__":
    sys.exit(main())
