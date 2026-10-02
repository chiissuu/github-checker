[English](../README.md) · Español

# GitHub Checker

Programa de consola en Python que obtiene las cuentas que sigues en GitHub y que no te siguen de vuelta. Consulta la API oficial y guarda el resultado en TXT, CSV o JSON.

## Requisitos

- Python 3.10 o superior, sin dependencias externas.
- Conexión a internet.
- Token personal cargado en `GITHUB_TOKEN`.

Esta primera versión analiza la cuenta propietaria del token. Detecta automáticamente su usuario, también cuando tiene un perfil privado.

## 1. Crear el token

En GitHub: foto de perfil → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token.

También puedes abrir el [formulario directo](https://github.com/settings/personal-access-tokens/new).

| Campo | Valor |
|---|---|
| Token name | `github-checker` |
| Expiration | Por ejemplo, 30 días |
| Resource owner | Tu cuenta personal |
| Repository access | Public repositories |
| Permissions | Sin permisos adicionales |

Los endpoints utilizados no requieren permisos adicionales del token. Copia el token generado y guárdalo de forma segura. No lo escribas en el código, lo subas al repositorio ni lo compartas en chats. [Documentación de GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

## 2. Abrir PowerShell y cargar el token

En este equipo, la ruta del proyecto es:

```powershell
cd "C:\Users\jesus\OneDrive\Escritorio\github-checker"
```

En otro equipo, sustituye esa ruta por la carpeta donde hayas guardado el programa.

```powershell
$tokenSeguro = Read-Host "Pega tu token de GitHub" -AsSecureString
$env:GITHUB_TOKEN = [System.Net.NetworkCredential]::new("", $tokenSeguro).Password
Remove-Variable tokenSeguro
```

El token no se muestra en pantalla ni queda como texto del comando en el historial. La variable pertenece a esa terminal: si la cierras, debes cargarlo de nuevo. El programa no carga archivos `.env`.

## 3. Ejecutar

```powershell
python checker.py
```

Si tienes instalado el lanzador de Python y `python` no se reconoce, prueba `py checker.py`.

El programa identifica tu cuenta y muestra el avance por páginas. Al terminar indica los totales y la ruta del informe.

```powershell
python checker.py --username chiissuu --format csv
python checker.py --format json
python checker.py --help
```

| Opción | Comportamiento |
|---|---|
| `--username` | Opcional; debe coincidir con el propietario del token |
| `--format txt\|csv\|json` | Formato del informe; TXT por defecto |
| `--output-dir RUTA` | Carpeta de destino; `resultados/` junto al script por defecto |

Una ruta de salida relativa personalizada se interpreta desde la carpeta actual de la terminal.

## Resultados

Ejemplo de nombre:

```text
resultados/personas_que_no_te_siguen_de_vuelta_github_chiissuu.txt
```

- **TXT:** cabecera con fecha UTC, total y enlaces a los perfiles.
- **CSV:** columnas `id`, `usuario` y `url`.
- **JSON:** cuentas y metadatos del análisis: usuario, fecha UTC y totales.

Una ejecución correcta reemplaza el resultado anterior para ese usuario y formato. Si falla la descarga o la escritura, conserva el informe anterior. Un resultado de cero cuentas es válido; el TXT lo indica, el CSV conserva las cabeceras y el JSON contiene una lista vacía.

`resultados/` y los nombres de informes están incluidos en `.gitignore`. Los archivos se guardan localmente; si la carpeta está dentro de OneDrive, se aplicará la sincronización que tengas configurada.

## Funcionamiento y límites

Se consulta `/user` para conocer la cuenta autenticada, se descargan todas las páginas de seguidores y seguidos y se calcula `seguidos − seguidores` por identificador numérico. Los nombres solo se usan para mostrar y ordenar.

Las peticiones personales autenticadas suelen disponer de 5.000 solicitudes por hora. La cuota se comparte con otras consultas de la misma cuenta y existen límites secundarios. Cada página contiene hasta 100 cuentas. [Límites oficiales](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api).

Las listas se descargan en peticiones sucesivas: si cambian las relaciones durante el análisis, puede haber diferencias. El informe refleja lo observado durante la consulta, no una instantánea indivisible. No se guarda una caché de relaciones entre ejecuciones.

`checker.py` solo consulta datos mediante GET; `unfollow.py` permite unfollow con confirmación explícita. El token se envía únicamente a `api.github.com`; no se siguen redirecciones.

## Errores frecuentes

| Mensaje o situación | Qué hacer |
|---|---|
| Falta `GITHUB_TOKEN` | Cargar el token en la terminal donde ejecutas Python |
| Token inválido o caducado | Renovarlo y cargar el nuevo valor |
| Usuario distinto del propietario | Omitir `--username` o indicar tu usuario |
| HTTP 403/429 | Respetar la espera indicada; puede ser un límite temporal o una denegación |
| HTTP 404 | Comprobar que la cuenta/recurso sigue siendo accesible |
| Fallo de conexión | Revisar internet y volver a ejecutar |
| Error al guardar | Revisar permisos, espacio y si el archivo está abierto en otra aplicación |

No hay reintentos automáticos ni informes parciales. Ctrl+C cancela. Código de salida: 0 correcto, 1 error, 130 cancelación.

## Pruebas

Desde la raíz del proyecto:

```powershell
python -m unittest discover -s tests -v
```

Usan datos ficticios y respuestas HTTP simuladas. No necesitan token ni internet.

## Unfollow opcional

Ejecuta `python unfollow.py` para una vista previa actualizada. Añade `--execute` para confirmar y aplicar los unfollows. Necesita **Followers: Read and write** en el token. Puedes usar `--exclude usuario1 usuario2` para conservar cuentas o `--from-json RUTA` para limitarte a un informe JSON anterior.

Consulta la [guía de unfollow](../Documentacion-Interna/Unfollow.md): permisos, ejemplos, pausas, registros y recuperación tras errores. Las peticiones se hacen una a una, con dos segundos entre cuentas, y se detienen ante errores. Los cambios ya aplicados permanecen al cancelar.

## Documentación para Obsidian

Empieza por [Inicio](../Documentacion-Interna/Inicio.md). El directorio contiene contexto, decisiones, funcionamiento, pendientes y sesiones, conectados mediante enlaces Markdown.
