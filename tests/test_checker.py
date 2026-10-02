# ==================================================
# 1. PREPARACIÓN DE LAS PRUEBAS
# ==================================================

import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError, URLError

import checker


def cuenta(identificador, usuario):
    return {"id": identificador, "login": usuario}


# ==================================================
# 2. CONSULTAS Y ANÁLISIS
# ==================================================

class PruebasConsulta(unittest.TestCase):
    def test_paginacion_y_duplicados(self):
        cliente = Mock()
        cliente.consultar.side_effect = [
            ([cuenta(1, "uno")], {"Link": '<https://api.github.com/next>; rel="next"'}),
            ([cuenta(1, "uno"), cuenta(2, "dos")], {}),
        ]
        with redirect_stdout(io.StringIO()):
            resultado = checker.obtener_cuentas(cliente, "demo", "following")
        self.assertEqual(set(resultado), {1, 2})
        self.assertEqual(cliente.consultar.call_args.args[0],
                         "/users/demo/following?per_page=100&page=2")

    def test_paginacion_sin_avance(self):
        cliente = Mock()
        cliente.consultar.return_value = ([], {"Link": '<https://otro>; rel="next"'})
        with redirect_stdout(io.StringIO()), self.assertRaises(checker.ErrorChecker):
            checker.obtener_cuentas(cliente, "demo", "followers")

    def test_comparacion_por_id_y_orden(self):
        seguidores = {1: checker.validar_cuenta(cuenta(1, "nombre-antiguo"))}
        seguidos = {i: checker.validar_cuenta(cuenta(i, nombre))
                    for i, nombre in [(1, "nuevo"), (2, "zeta"), (3, "Ana")]}
        self.assertEqual([c["usuario"] for c in checker.comparar(seguidores, seguidos)],
                         ["Ana", "zeta"])

    def test_respuestas_invalidas(self):
        for datos in [None, {}, cuenta(True, "demo"), cuenta(1, "../ruta"), cuenta(1, "=formula")]:
            with self.subTest(datos=datos), self.assertRaises(checker.ErrorChecker):
                checker.validar_cuenta(datos)

    def test_cabeceras_y_timeout(self):
        cliente = checker.ClienteGitHub("token_ficticio")
        respuesta = Mock()
        respuesta.read.return_value = b'[]'
        respuesta.headers = {}
        cliente.opener = Mock()
        cliente.opener.open.return_value = MagicMock()
        cliente.opener.open.return_value.__enter__.return_value = respuesta
        self.assertEqual(cliente.consultar("/user"), ([], {}))
        peticion = cliente.opener.open.call_args.args[0]
        self.assertEqual(peticion.full_url, "https://api.github.com/user")
        self.assertEqual(peticion.get_header("Authorization"), "Bearer token_ficticio")
        self.assertEqual(cliente.opener.open.call_args.kwargs["timeout"], 30)

    def test_errores_http_sin_filtrar_token(self):
        for codigo in [401, 403, 404, 429, 500]:
            cliente = checker.ClienteGitHub("secreto_ficticio")
            cliente.opener = Mock()
            cliente.opener.open.side_effect = HTTPError(
                "https://api.github.com/user", codigo, "secreto_ficticio", {}, None
            )
            with self.subTest(codigo=codigo), self.assertRaises(checker.ErrorChecker) as contexto:
                cliente.consultar("/user")
            self.assertNotIn("secreto_ficticio", str(contexto.exception))

    def test_limite_con_espera(self):
        error = HTTPError("url", 429, "", {"Retry-After": "60"}, None)
        self.assertIn("60 segundos", checker.describir_error(error))

    def test_red_y_json_invalidos(self):
        for error in [URLError("fallo"), TimeoutError(), ValueError("JSON")]:
            cliente = checker.ClienteGitHub("ficticio")
            cliente.opener = Mock()
            cliente.opener.open.side_effect = error
            with self.subTest(error=error), self.assertRaises(checker.ErrorChecker):
                cliente.consultar("/user")

    def test_no_redirige_credenciales(self):
        self.assertIsNone(checker.SinRedirecciones().redirect_request(
            None, None, 302, "", {}, "https://otro.example"
        ))


# ==================================================
# 3. INFORMES Y EJECUCIÓN COMPLETA
# ==================================================

class PruebasEjecucion(unittest.TestCase):
    def test_tres_formatos(self):
        informe = {"usuario": "demo", "consultado_en": "2026-10-02T00:00:00+00:00",
                   "cuentas": [checker.validar_cuenta(cuenta(1, "ana"))]}
        with tempfile.TemporaryDirectory() as carpeta:
            rutas = {f: checker.escribir_informe(informe, f, Path(carpeta))
                     for f in ["txt", "csv", "json"]}
            self.assertIn("https://github.com/ana", rutas["txt"].read_text(encoding="utf-8"))
            self.assertEqual(json.loads(rutas["json"].read_text(encoding="utf-8")), informe)
            with rutas["csv"].open(encoding="utf-8", newline="") as archivo:
                self.assertEqual(list(csv.DictReader(archivo))[0]["usuario"], "ana")

    def test_resultado_vacio(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = checker.escribir_informe(
                {"usuario": "demo", "consultado_en": "ahora", "cuentas": []}, "csv", Path(carpeta)
            )
            self.assertEqual(ruta.read_text().strip(), "id,usuario,url")

    @patch.dict("os.environ", {"GITHUB_TOKEN": "token_ficticio"})
    @patch("checker.ClienteGitHub")
    def test_flujo_completo(self, clase):
        clase.return_value.consultar.side_effect = [
            (cuenta(9, "demo"), {}), ([cuenta(1, "uno")], {}),
            ([cuenta(1, "uno"), cuenta(2, "dos")], {}),
        ]
        with tempfile.TemporaryDirectory() as carpeta, redirect_stdout(io.StringIO()):
            self.assertEqual(checker.main(["--format", "json", "--output-dir", carpeta]), 0)
            informe = json.loads(next(Path(carpeta).glob("*.json")).read_text(encoding="utf-8"))
            self.assertEqual(informe["no_te_siguen"], 1)
            self.assertEqual(informe["cuentas"][0]["usuario"], "dos")

    @patch.dict("os.environ", {"GITHUB_TOKEN": "token_ficticio"})
    @patch("checker.ClienteGitHub")
    def test_fallo_intermedio_conserva_informe(self, clase):
        clase.return_value.consultar.side_effect = [
            (cuenta(9, "demo"), {}), ([], {}), checker.ErrorChecker("sin conexión")
        ]
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "personas_que_no_te_siguen_de_vuelta_github_demo.txt"
            ruta.write_text("informe anterior", encoding="utf-8")
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(checker.main(["--output-dir", carpeta]), 1)
            self.assertEqual(ruta.read_text(encoding="utf-8"), "informe anterior")
            self.assertEqual(len(list(Path(carpeta).iterdir())), 1)

    @patch.dict("os.environ", {"GITHUB_TOKEN": ""})
    @patch("checker.ClienteGitHub")
    def test_token_ausente(self, clase):
        with redirect_stderr(io.StringIO()):
            self.assertEqual(checker.main([]), 1)
        clase.assert_not_called()

    @patch.dict("os.environ", {"GITHUB_TOKEN": "token_ficticio"})
    @patch("checker.ClienteGitHub")
    def test_usuario_ajeno(self, clase):
        clase.return_value.consultar.return_value = (cuenta(9, "demo"), {})
        with redirect_stderr(io.StringIO()):
            self.assertEqual(checker.main(["--username", "otro"]), 1)
        self.assertEqual(clase.return_value.consultar.call_count, 1)

    def test_escritura_fallida_conserva_anterior(self):
        with tempfile.TemporaryDirectory() as carpeta:
            informe = {"usuario": "demo", "consultado_en": "ahora", "cuentas": []}
            ruta = checker.escribir_informe(informe, "json", Path(carpeta))
            anterior = ruta.read_bytes()
            with patch("checker.json.dump", side_effect=OSError("disco lleno")):
                with self.assertRaises(OSError):
                    checker.escribir_informe(informe, "json", Path(carpeta))
            self.assertEqual(ruta.read_bytes(), anterior)
            self.assertEqual(list(Path(carpeta).iterdir()), [ruta])


if __name__ == "__main__":
    unittest.main()
