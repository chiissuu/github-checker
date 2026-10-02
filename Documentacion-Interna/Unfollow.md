# Unfollow — uso y funcionamiento

## Preparar el token

En [Fine-grained tokens](https://github.com/settings/personal-access-tokens), abre el token `github-checker`. En Permissions, añade el permiso de cuenta **Followers**, elige **Read and write** y guarda con Update token. Según la interfaz puede aparecer bajo Account permissions o Add permissions. Mantén tu cuenta como Resource owner y el acceso a repositorios como estaba.

Puedes editar el token existente; no necesitas crear otro programa ni una API propia. Si prefieres un token separado, créalo con ese permiso. Si lo regeneras o creas uno nuevo, carga el nuevo valor en la terminal:

```powershell
$tokenSeguro = Read-Host "Pega tu token de GitHub" -AsSecureString
$env:GITHUB_TOKEN = [System.Net.NetworkCredential]::new("", $tokenSeguro).Password
Remove-Variable tokenSeguro
```

## Uso desde la raíz del proyecto

Vista previa de las cuentas que actualmente no te siguen:

```powershell
python unfollow.py
```

Vista previa limitada a un informe anterior:

```powershell
python checker.py --format json
python unfollow.py --from-json resultados/personas_que_no_te_siguen_de_vuelta_github_chiissuu.json
```

El informe debe ser JSON producido por checker. TXT y CSV no se importan. Se puede eliminar una fila de `cuentas` en el JSON para reducir la selección; conserva JSON válido. El programa valida propietario e IDs y cruza la selección con datos recién descargados. No añade personas ajenas a la selección del archivo.

Para conservar cuentas concretas:

```powershell
python unfollow.py --exclude usuario1 usuario2
```

Para ejecutar, repite tus opciones añadiendo `--execute`:

```powershell
python unfollow.py --execute
python unfollow.py --from-json resultados/personas_que_no_te_siguen_de_vuelta_github_chiissuu.json --exclude usuario1 --execute
```

Se muestra otra vista previa actualizada y se pide escribir exactamente `UNFOLLOW usuario cantidad`, con los valores mostrados. Cualquier otra respuesta cancela. Sin `--execute` no se envía DELETE. No existe opción para saltar la confirmación ni programación periódica.

## Ejecución

`unfollow.py` reutiliza ClienteGitHub, obtener_cuentas, comparar y validar_cuenta. `checker.py` mantiene su comportamiento de análisis. El cliente compartido añade DELETE con éxito exclusivo en HTTP 204, cuyo cuerpo vacío no se interpreta como JSON.

Antes de cada DELETE se comprueba que el login sigue asociado al ID seleccionado. Se hacen peticiones secuenciales, con dos segundos de pausa entre cuentas. El programa se detiene ante el primer error, incluyendo 403/429, y muestra Retry-After o la renovación de cuota cuando GitHub los proporciona. No reintenta automáticamente.

GitHub recomienda al menos un segundo entre peticiones de escritura; dos segundos no garantizan ausencia de límites. Las 5.000 peticiones por hora no equivalen a una cuota de 5.000 unfollows. No se simulan movimientos humanos ni se evaden restricciones.

## Registro y recuperación

Cada ejecución confirmada crea `resultados/unfollow_<id-aleatorio>.jsonl`. `--output-dir` cambia la carpeta. Una línea JSON por evento: inicio con propietario y selección, intento, confirmado, no_confirmado, detenido_identidad o finalizado. El registro se vacía al disco antes y después de cada DELETE; no contiene credenciales. Está gitignorado por nombre incluso fuera de resultados/.

Si la conexión se corta, un intento puede haberse aplicado en GitHub sin que llegase la respuesta. **No confirmado no significa que no se haya hecho**. Si falla la escritura posterior, también puede quedar solo el intento. El registro no es una transacción con GitHub.

Para continuar, corrige el problema o respeta la espera y ejecuta de nuevo el mismo comando. Se consultan las relaciones actuales: quienes ya no sigues quedan fuera. Con `--from-json` se sigue limitando a los IDs del archivo. Revisa y confirma la nueva selección.

Ctrl+C detiene; los unfollows ya hechos permanecen. No hay rollback automático. Tampoco se admite ejecutar varias instancias a la vez como forma de acelerar el proceso.

## Limitaciones

Puede cambiar una relación entre la vista previa y DELETE, especialmente si dejas la confirmación abierta mucho tiempo. Si ocurre, cancela y genera otra vista previa. La API no ofrece una operación condicional atómica «dejar de seguir solo si todavía no me sigue». La comprobación de identidad tampoco elimina por completo la posibilidad de cambios entre peticiones.

## Referencias

- [Unfollow y permisos](https://docs.github.com/en/rest/users/followers#unfollow-a-user)
- [Pausas y límites](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api)
