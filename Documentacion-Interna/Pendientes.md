# Pendientes

## Validación con la cuenta real

El usuario confirmó que checker funciona. Queda habilitar Followers: Read and write y ejecutar unfollow en su terminal. El agente solo prueba DELETE simulados. Ver [Unfollow](Unfollow.md).

## Limitaciones conocidas

- Solo se analiza la cuenta propietaria del token.
- Las relaciones pueden cambiar durante la paginación; no hay una instantánea atómica.
- No hay reintentos automáticos ni caché entre ejecuciones.
- Los informes anteriores permanecen si falla una nueva ejecución.

## Posibles pasos posteriores

Solo si se solicitan: modo público sin token con manejo explícito de visibilidad, CI en GitHub Actions y publicación del repositorio. No hay remoto, release o ejecución de CI confirmados.
