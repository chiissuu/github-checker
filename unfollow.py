# ==================================================
# 1. PREPARACIÓN Y DATOS
# ==================================================

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from checker import ClienteGitHub, ErrorChecker, SALIDA, comparar, obtener_cuentas, validar_cuenta

PAUSA_SEGUNDOS = 2


# ==================================================
# 2. PREPARACIÓN DE LA LISTA
# ==================================================

# 2.1. Selección desde un informe JSON

def cargar_seleccion(ruta: Path, propietario: str) -> set[int]:
    try:
        informe = json.loads(ruta.read_text(encoding="utf-8-sig"))
    except (ValueError, UnicodeError):
        raise ErrorChecker("El informe no contiene JSON válido.") from None
    if not isinstance(informe, dict) or not isinstance(informe.get("usuario"), str):
        raise ErrorChecker("Informe sin propietario válido.")
    if informe["usuario"].casefold() != propietario.casefold():
        raise ErrorChecker("El informe pertenece a otro usuario.")
    if not isinstance(informe.get("cuentas"), list):
        raise ErrorChecker("El informe no contiene una lista de cuentas.")
    identificadores = set()
    for fila in informe["cuentas"]:
        if not isinstance(fila, dict):
            raise ErrorChecker("Cuenta inválida en el informe.")
        cuenta = validar_cuenta({"id": fila.get("id"), "login": fila.get("usuario")})
        identificadores.add(cuenta["id"])
    return identificadores


# 2.2. Actualización y exclusiones

def preparar_lista(cliente, propietario, seleccion=None, excluir=()):
    seguidores = obtener_cuentas(cliente, propietario, "followers")
    seguidos = obtener_cuentas(cliente, propietario, "following")
    exclusiones = {usuario.casefold() for usuario in excluir}
    return [cuenta for cuenta in comparar(seguidores, seguidos)
            if (seleccion is None or cuenta["id"] in seleccion)
            and cuenta["usuario"].casefold() not in exclusiones]


# ==================================================
# 3. EJECUCIÓN Y REGISTRO
# ==================================================

# 3.1. Registro persistente por evento

def registrar(archivo, estado, **datos):
    evento = {"fecha_utc": datetime.now(timezone.utc).isoformat(), "estado": estado, **datos}
    archivo.write(json.dumps(evento, ensure_ascii=False) + "\n")
    archivo.flush()
    os.fsync(archivo.fileno())


# 3.2. Unfollows secuenciales

def ejecutar(cliente, propietario, cuentas, directorio):
    directorio.mkdir(parents=True, exist_ok=True)
    ruta = directorio / f"unfollow_{uuid4().hex}.jsonl"
    print(f"Registro: {ruta}")
    completados = 0
    with ruta.open("x", encoding="utf-8") as archivo:
        registrar(archivo, "inicio", propietario=propietario, cuentas=cuentas)
        for indice, cuenta in enumerate(cuentas):
            if indice:
                time.sleep(PAUSA_SEGUNDOS)
            datos, _ = cliente.consultar(f"/users/{cuenta['usuario']}")
            actual = validar_cuenta(datos)
            if actual["id"] != cuenta["id"] or actual["usuario"].casefold() != cuenta["usuario"].casefold():
                registrar(archivo, "detenido_identidad", cuenta=cuenta)
                raise ErrorChecker("Una cuenta cambió de identidad o nombre. Genera otra vista previa.")
            # El intento queda en disco antes de DELETE: sin confirmación, el resultado es incierto.
            registrar(archivo, "intento", cuenta=cuenta)
            try:
                cliente.dejar_de_seguir(cuenta["usuario"])
            except (ErrorChecker, KeyboardInterrupt):
                registrar(archivo, "no_confirmado", cuenta=cuenta)
                raise
            registrar(archivo, "confirmado", cuenta=cuenta)
            completados += 1
            print(f"  [{completados}/{len(cuentas)}] Unfollow confirmado: {cuenta['usuario']}")
        registrar(archivo, "finalizado", confirmados=completados)
    return ruta


# ==================================================
# 4. CONSOLA Y PUNTO DE ENTRADA
# ==================================================

# 4.1. Argumentos

def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Vista previa y unfollow de cuentas que no te siguen.")
    parser.add_argument("--from-json", type=Path, help="Limitar la selección a un informe JSON de checker.")
    parser.add_argument("--exclude", nargs="+", default=[], metavar="USUARIO", help="Cuentas a conservar.")
    parser.add_argument("--execute", action="store_true", help="Pedir confirmación y ejecutar los unfollows.")
    parser.add_argument("--output-dir", type=Path, default=SALIDA, help="Carpeta de registros JSONL.")
    return parser.parse_args(argv)


# 4.2. Flujo principal

def main(argv=None):
    args = parse_args(argv)
    try:
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        if not token or not re.fullmatch(r"[A-Za-z0-9_]+", token):
            raise ErrorChecker("Carga un GITHUB_TOKEN válido en esta terminal.")
        cliente = ClienteGitHub(token)
        datos, _ = cliente.consultar("/user")
        propietario = validar_cuenta(datos)["usuario"]
        seleccion = cargar_seleccion(args.from_json, propietario) if args.from_json else None
        cuentas = preparar_lista(cliente, propietario, seleccion, args.exclude)
        print(f"\nCuenta: {propietario} | Unfollows seleccionados: {len(cuentas)}")
        for cuenta in cuentas:
            print(f"  {cuenta['usuario']} — {cuenta['url']}")
        if not cuentas:
            print("No hay cuentas seleccionadas. No se ha cambiado ningún seguimiento.")
            return 0
        if not args.execute:
            print("\nSolo vista previa. Para aplicar esta selección, repite con --execute.")
            return 0
        frase = f"UNFOLLOW {propietario} {len(cuentas)}"
        print("\nSe modificará tu cuenta. Los cambios ya completados no se deshacen al cancelar.")
        if input(f"Escribe exactamente '{frase}' para continuar: ").strip() != frase:
            print("Cancelado. No se ha cambiado ningún seguimiento.")
            return 0
        ejecutar(cliente, propietario, cuentas, args.output_dir)
        print("Proceso completado.")
        return 0
    except ErrorChecker as error:
        print(f"Detenido: {error}", file=sys.stderr)
        print("Si comenzó la ejecución, revisa el registro y genera una nueva vista previa.", file=sys.stderr)
        return 1
    except OSError:
        print("Detenido por un error de archivo. Revisa el registro; puede haber cambios ya aplicados.", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nCancelado. Si comenzó la ejecución, revisa el registro de cambios.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
