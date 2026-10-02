# Funcionamiento

## Flujo

1. `parse_args` obtiene `--username`, `--format` y `--output-dir`.
2. `main` lee `GITHUB_TOKEN`, comprueba su formato básico y consulta `/user`.
3. `validar_cuenta` comprueba identificador y login. Si se indicó username, debe coincidir con el propietario.
4. `obtener_cuentas` descarga seguidores y seguidos usando páginas de 100 elementos. Mientras haya `rel="next"` en Link, incrementa la página. No visita las URL recibidas en la cabecera.
5. Guarda cuentas en diccionarios indexados por ID para eliminar duplicados. Si hay página siguiente pero no aparecen IDs nuevos, aborta para evitar un bucle.
6. `comparar` calcula la diferencia por ID y ordena por login sin distinguir mayúsculas.
7. `escribir_informe` escribe un temporal en la carpeta de destino y lo reemplaza sobre el informe final al terminar. Limpia el temporal en caso de error.

## Cliente HTTP

Actualización: `consultar` conserva GET y `dejar_de_seguir` añade DELETE exclusivamente para `/user/following/{usuario}`, esperando HTTP 204 sin cuerpo. `checker.py` sigue consultando; el flujo de escritura lo dirige [unfollow.py](Unfollow.md).

`ClienteGitHub` usa `urllib.request`, un timeout de 30 segundos y las cabeceras Accept, Authorization, User-Agent y X-GitHub-Api-Version. Versión fijada: `2026-03-10`. `SinRedirecciones` evita reenviar credenciales a otro destino. Se usa GET para consultar y DELETE para unfollow contra `https://api.github.com`.

Los mensajes de error se construyen localmente, sin imprimir cuerpos HTTP ni el token. Se distinguen token inválido, recurso inaccesible, límites, fallos de servidor, conexión y JSON inválido. Se atienden Retry-After y X-RateLimit-Reset para informar al usuario, sin espera ni reintento automático.

## Informes

TXT: usuario, fecha UTC, cantidad y URL por cuenta. CSV: id, usuario, url. JSON: usuario, consultado_en, seguidores, seguidos, no_te_siguen y cuentas. Las tres salidas se construyen a partir del mismo análisis.

La salida por defecto está junto al script en `resultados/`. Los archivos de un mismo usuario/formato se reemplazan tras una ejecución correcta. Un informe anterior puede permanecer si falla una nueva consulta: comprobar la fecha del TXT/JSON y el mensaje de la terminal.

## Límites de consistencia

Las listas no se obtienen en una única operación atómica de GitHub. Si cambian durante las peticiones, pueden aparecer discrepancias. Eliminar duplicados no recupera entradas que se hayan desplazado entre páginas. Repetir el análisis si se modificaron seguimientos durante la ejecución.

## Pruebas

`tests/test_checker.py`, con unittest y unittest.mock. Cubre paginación, duplicados, falta de avance, comparación por ID, datos inválidos, cabeceras, timeout, errores HTTP/red/JSON, redirecciones, exportaciones, listas vacías, flujo completo simulado y conservación del informe anterior ante fallos de red o disco.
