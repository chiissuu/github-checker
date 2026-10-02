# ==================================================
# 1. PREPARACIÓN DE PRUEBAS
# ==================================================

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import checker
import unfollow

CUENTA = {"id": 1, "usuario": "ana", "url": "https://github.com/ana"}


# ==================================================
# 2. SELECCIÓN Y CONFIRMACIÓN
# ==================================================

class PruebasSeleccion(unittest.TestCase):
    def test_informe_propietario_y_validacion(self):
        with tempfile.TemporaryDirectory() as carpeta:
            ruta = Path(carpeta) / "informe.json"
            ruta.write_text(json.dumps({"usuario": "demo", "cuentas": [CUENTA]}))
            self.assertEqual(unfollow.cargar_seleccion(ruta, "DEMO"), {1})
            with self.assertRaises(checker.ErrorChecker):
                unfollow.cargar_seleccion(ruta, "otro")
            ruta.write_text('{"usuario":"demo","cuentas":[{"id":1,"usuario":"../x"}]}')
            with self.assertRaises(checker.ErrorChecker):
                unfollow.cargar_seleccion(ruta, "demo")

    @patch("unfollow.obtener_cuentas")
    def test_actualiza_filtra_y_excluye(self, obtener):
        obtener.side_effect = [{2: {}}, {1: CUENTA, 2: {"usuario": "mutuo"},
                                        3: {"id": 3, "usuario": "nuevo"}}]
        self.assertEqual(unfollow.preparar_lista(Mock(), "demo", {1, 2}, ["ANA"]), [])

    def ejecutar_main(self, argumentos, confirmacion=None):
        with patch.dict("os.environ", {"GITHUB_TOKEN": "ficticio"}), \
             patch("unfollow.ClienteGitHub") as clase, \
             patch("unfollow.preparar_lista", return_value=[CUENTA]), \
             patch("unfollow.ejecutar") as ejecutar, \
             patch("builtins.input", return_value=confirmacion) as entrada, \
             redirect_stdout(io.StringIO()):
            clase.return_value.consultar.return_value = ({"id": 9, "login": "demo"}, {})
            codigo = unfollow.main(argumentos)
            return codigo, ejecutar.call_count, entrada.call_count

    def test_previsualizacion_no_modifica(self):
        self.assertEqual(self.ejecutar_main([]), (0, 0, 0))

    def test_confirmacion_incorrecta_no_modifica(self):
        self.assertEqual(self.ejecutar_main(["--execute"], "si"), (0, 0, 1))

    def test_confirmacion_exacta_ejecuta(self):
        self.assertEqual(self.ejecutar_main(["--execute"], "UNFOLLOW demo 1"), (0, 1, 1))

    @patch.dict("os.environ", {"GITHUB_TOKEN": "ficticio"})
    @patch("unfollow.ClienteGitHub")
    def test_fallo_descarga_no_modifica(self, clase):
        clase.return_value.consultar.side_effect = [({"id": 9, "login": "demo"}, {}),
                                                   checker.ErrorChecker("límite")]
        with redirect_stderr(io.StringIO()):
            self.assertEqual(unfollow.main(["--execute"]), 1)
        clase.return_value.dejar_de_seguir.assert_not_called()


# ==================================================
# 3. PETICIONES Y REGISTROS
# ==================================================

class PruebasEjecucion(unittest.TestCase):
    def test_delete_204_sin_json(self):
        cliente = checker.ClienteGitHub("ficticio")
        cliente.opener = MagicMock()
        respuesta = cliente.opener.open.return_value.__enter__.return_value
        respuesta.status = 204
        cliente.dejar_de_seguir("ana")
        peticion = cliente.opener.open.call_args.args[0]
        self.assertEqual(peticion.method, "DELETE")
        self.assertEqual(peticion.full_url, "https://api.github.com/user/following/ana")
        respuesta.read.assert_not_called()
        respuesta.status = 200
        with self.assertRaises(checker.ErrorChecker):
            cliente.dejar_de_seguir("ana")

    def test_secuencia_pausa_y_registro(self):
        cliente = Mock()
        cliente.consultar.side_effect = [({"id": 1, "login": "ana"}, {}),
                                        ({"id": 2, "login": "bea"}, {})]
        with tempfile.TemporaryDirectory() as carpeta, patch("unfollow.time.sleep") as pausa, \
             redirect_stdout(io.StringIO()):
            ruta = unfollow.ejecutar(cliente, "demo", [CUENTA, {"id": 2, "usuario": "bea"}], Path(carpeta))
            eventos = [json.loads(linea) for linea in ruta.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([e["estado"] for e in eventos],
                         ["inicio", "intento", "confirmado", "intento", "confirmado", "finalizado"])
        pausa.assert_called_once_with(2)
        self.assertEqual(cliente.dejar_de_seguir.call_count, 2)

    def test_identidad_cambiada_no_modifica(self):
        cliente = Mock()
        cliente.consultar.return_value = ({"id": 999, "login": "ana"}, {})
        with tempfile.TemporaryDirectory() as carpeta, redirect_stdout(io.StringIO()):
            with self.assertRaises(checker.ErrorChecker):
                unfollow.ejecutar(cliente, "demo", [CUENTA], Path(carpeta))
        cliente.dejar_de_seguir.assert_not_called()

    def test_error_o_cancelacion_detiene_y_registra(self):
        for error in [checker.ErrorChecker("límite"), KeyboardInterrupt()]:
            cliente = Mock()
            cliente.consultar.return_value = ({"id": 1, "login": "ana"}, {})
            cliente.dejar_de_seguir.side_effect = error
            with tempfile.TemporaryDirectory() as carpeta, redirect_stdout(io.StringIO()):
                with self.assertRaises(type(error)):
                    unfollow.ejecutar(cliente, "demo", [CUENTA, CUENTA], Path(carpeta))
                eventos = [json.loads(linea) for linea in next(Path(carpeta).glob("*.jsonl")).read_text().splitlines()]
            self.assertEqual(eventos[-1]["estado"], "no_confirmado")
            self.assertEqual(cliente.dejar_de_seguir.call_count, 1)

    def test_error_registro_impide_delete(self):
        cliente = Mock()
        cliente.consultar.return_value = ({"id": 1, "login": "ana"}, {})
        with tempfile.TemporaryDirectory() as carpeta, redirect_stdout(io.StringIO()), \
             patch("unfollow.registrar", side_effect=[None, OSError("disco lleno")]):
            with self.assertRaises(OSError):
                unfollow.ejecutar(cliente, "demo", [CUENTA], Path(carpeta))
        cliente.dejar_de_seguir.assert_not_called()


if __name__ == "__main__":
    unittest.main()
