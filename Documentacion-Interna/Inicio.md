# GitHub Checker — Inicio

Válvula de contexto para Obsidian y futuras sesiones de desarrollo.

## Objetivo

Consultar seguidores y seguidos de la cuenta propietaria de un token personal de GitHub y exportar quién no sigue de vuelta. Proyecto inspirado en Instagram Checker: el cálculo se mantiene, la entrada cambia de exportación manual a API REST.

## Mapa

- [Unfollow](Unfollow.md): preparación del token, vista previa, ejecución y registros.
- [Sesión de unfollow](Sesiones/2026-10-02-unfollow.md): ampliación solicitada.

- [Contexto](Contexto.md): petición inicial y alcance.
- [Funcionamiento](Funcionamiento.md): flujo, funciones y errores.
- [Decisiones](Decisiones.md): motivos de las decisiones técnicas.
- [Pendientes](Pendientes.md): estado y límites de validación.
- [Sesión inicial](Sesiones/2026-10-02-creacion-inicial.md): trabajo realizado.
- [Guía de uso](../READMEs/README.es.md).

## Estructura

```text
github-checker/
├── checker.py
├── unfollow.py
├── tests/test_unfollow.py
├── tests/test_checker.py
├── README.md
├── READMEs/README.es.md
├── .gitignore
├── Documentacion-Interna/
└── resultados/                 (se crea al ejecutar; gitignorado)
```

## Retomar el trabajo

Leer primero Contexto y Decisiones. Ejecutar `python -m unittest discover -s tests -v` desde la raíz. Mantener los comentarios como divisores numerados de secciones; evitar comentarios obvios por línea. Nunca incluir tokens o resultados reales en ejemplos públicos.
