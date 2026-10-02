# Decisiones

## Python sin dependencias externas

La biblioteca estándar cubre HTTP, JSON, CSV, CLI y tests. Mantener un único `checker.py` dividido en secciones evita añadir una arquitectura innecesaria para este tamaño. No se crea un requirements vacío.

## Token obligatorio y cuenta propia

La propuesta inicial contemplaba consultas públicas sin token. La implementación inicial se centra en el flujo que preparó el usuario: token personal en GITHUB_TOKEN y cuenta propia. `/user` confirma la identidad; `--username` es una comprobación opcional.

Motivo: los endpoints de listas pueden devolver vacío para perfiles privados ajenos. Exigir que el token pertenezca al objetivo evita tratar relaciones ocultas como ausencia de seguidores. Se usan `/users/{username}/followers` y `/following`, que no requieren permisos adicionales del token, también cuando consulta su propietario. No sustituirlos por `/user/followers` sin revisar sus permisos.

## Comparación por ID

El ID es estable frente a un cambio de login. Se conserva el login para mostrar, ordenar y construir enlaces. Los diccionarios eliminan IDs duplicados.

## Paginación y token

Se utiliza Link únicamente para saber si hay página siguiente y se construye una ruta conocida en el mismo dominio. Se rechazan redirecciones HTTP. Así las respuestas no deciden dónde enviar Authorization.

## Datos recientes y fallos explícitos

Sin caché persistente: las relaciones cambian y la caché podría generar resultados antiguos. Sin reintentos automáticos: se informa de la espera ante límites. Una descarga fallida no produce un informe parcial. Escritura temporal y reemplazo para preservar informes anteriores ante errores.

## Documentación y comentarios

README principal en inglés y español en READMEs/, continuando la organización de Instagram Checker. Documentacion-Interna usa enlaces Markdown relativos compatibles con Obsidian. Los comentarios siguen exclusivamente divisiones numeradas, con dos explicaciones puntuales sobre protección del token.

## Fuera del alcance

Sin navegador, API web propia, base de datos, Docker o publicación remota. El usuario solicitó posteriormente unfollow supervisado; se implementa en un script separado. Ver [Unfollow](Unfollow.md).

## Referencias consultadas

- [Seguidores y seguidos](https://docs.github.com/en/rest/users/followers)
- [Usuario autenticado](https://docs.github.com/en/rest/users/users)
- [Versiones de API](https://docs.github.com/en/rest/about-the-rest-api/api-versions)
