# ADR 014: Logging y monitoring básicos

## Estado
**Propuesto**

## Contexto

Se requiere visibilidad de errores y métricas mínimas para depuración durante el desarrollo y entrega.

## Decisión

Usar el `logging` estándar de Python configurado en nivel `INFO` por defecto y exportar métricas básicas a la salida estándar para que el orquestador (Docker) y el profesor puedan ver logs. En paralelo, documentar la integración futura con Prometheus/Grafana.

## Justificación

- Rápido de implementar y suficiente para Fase 1.

## Consecuencias

- Logs estructurados (JSON) pueden añadirse si se requiere en entregas futuras.

## Fecha

2026-03-12
