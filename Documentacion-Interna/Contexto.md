# Contexto

## Origen

Jesús pidió crear desde cero un equivalente de Instagram Checker para GitHub. Se leyó la documentación interna de Instagram Checker para conservar su objetivo: cuentas seguidas que no siguen de vuelta y salida TXT/CSV/JSON.

GitHub proporciona estos datos mediante una API oficial. No hace falta exportar JSON manualmente ni usar Playwright.

## Preferencias del usuario

- Desarrollo incremental; explicar antes los cambios de estructura, dependencias y configuración.
- Soluciones sencillas y educativas.
- Comentarios de división de secciones como los del archivo de referencia `aim-trainer/app.js`: líneas de iguales, títulos numerados y subsecciones.
- Comentarios por línea solo si aportan contexto importante.
- Documentación Markdown conectada para Obsidian.

El archivo JavaScript se utilizó únicamente como referencia de comentarios, sin modificarlo ni adoptar su lógica.

## Token y entorno

El usuario creó un token y lo cargó en una sesión propia de PowerShell. Confirmó que la variable tenía valor; eso no equivale a una autenticación validada. La sesión del agente no comparte necesariamente esa variable. No pedir que copie el secreto al chat.

Directorio local inicial: `C:\Users\jesus\OneDrive\Escritorio\github-checker`. Estaba vacío. No se ha solicitado publicar el proyecto ni crear un repositorio remoto.

## Alcance inicial

Herramienta local de consola, Python 3.10+, sin paquetes externos, base de datos o Docker. Token obligatorio en esta implementación y análisis de su propietario. El analizador es de solo lectura. El usuario confirmó que funciona y pidió añadir unfollow supervisado; ver [Unfollow](Unfollow.md). Ver [Decisiones](Decisiones.md).
