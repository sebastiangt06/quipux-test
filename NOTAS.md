# Notas Técnicas de Implementación — Servicio de Tarifas Línea T2

## 1. Hallazgos en el código heredado

Más allá del bug reportado (BUG-17), la inspección del código reveló aspectos críticos:
- **Redondeo bancario inapropiado**: `app/tarifas.py` utilizaba `round()` de Python. Al aplicar "round-half-to-even", un transbordo de estudiante (\$500 con 35 % de descuento = \$325, o 6.5 múltiplos de \$50) se redondeaba hacia abajo a 6 (\$300) en lugar de \$350, violando el cobro requerido.
- **Ausencia de validación de husos horarios**: Pydantic aceptaba fechas "naive" (sin offset). Esto permitía mezclar datetimes locales sin contexto, generando fallos en comparaciones cronológicas.
- **Permisividad ante duplicados**: La solicitud aceptaba múltiples validaciones con el mismo `id`, lo cual permitiría procesar cobros repetidos por error de red o reintento de cliente.
- **Enmascaramiento en pruebas existentes**: En `tests/test_api.py`, la aserción original `assert len(r.json()) >= 1` ocultaba el BUG-17, permitiendo que la prueba pasara a pesar de la fuga de datos entre tarjetas.
- **Configuración de Docker**: El `Dockerfile` original omitía `--host 0.0.0.0` en `uvicorn`, impidiendo la comunicación externa a través del reenvío de puertos del host.

---

## 2. Casos borde identificados y resolución

| Caso borde | Comportamiento esperado | Solución implementada |
| :--- | :--- | :--- |
| **Límite exacto de 90 min** | Debe computar como transbordo. | Condición $\Delta t \le 90\text{ min}$ (inclusive). Una validación a los $90\text{ min y } 1\text{ s}$ inicia nuevo viaje (\$3.200). |
| **Ciclo de transbordos** | 1.º transbordo (\$500 con desc.), 2.º gratis (\$0), 3.º nuevo viaje. | Máquina de estados con contador `transbordos_en_viaje`. Al alcanzar 2, la siguiente validación resetea el viaje y el reloj a esa nueva fecha. |
| **Desorden y zonas mixtas** | Interpretar instantes universales exactos. | Ordenamiento por `fecha_hora`. Python compara objetos tz-aware en UTC absoluto (ej. `11:58:27Z` antes que `07:41:12-05:00`). |
| **Redondeo en empate (mitad)** | Redondear siempre hacia arriba. | Uso de `Decimal` y `ROUND_HALF_UP` en unidades de \$50 ($6.5 \to 7 = \$350$; $4.5 \to 5 = \$250$). |
| **Lista vacía de validaciones** | No generar cobros pero responder HTTP 200. | Retorno explícito `cobros: []`, `total: 0`. |
| **Perfil omitido o inválido** | Si se omite o es `null` asume `general`; si es inválido $\to$ HTTP 422. | Validador Pydantic con normalización previa a `general` y validación contra Enum `Perfil`. |
| **Identificadores duplicados** | Rechazar con HTTP 422. | Validador en `SolicitudTarifa` que compara `len(ids) != len(set(ids))`. |


## 3. Supuestos adoptados

1. **Simultaneidad de validaciones**: Si dos validaciones tienen el mismo timestamp exacto, se mantiene el orden de llegada de la lista de forma estable.
2. **Ciclo de vida del almacenamiento**: Siguiendo la arquitectura actual del repositorio, el almacenamiento en memoria (`_historiales`) es de alcance temporal durante la ejecución del proceso.

## 4. Aspectos pendientes para ambiente productivo

1. **Persistencia y transaccionalidad**: Migrar `_historiales` a una base de datos relacional (PostgreSQL) con índices compuestos en `(tarjeta, fecha_hora)` y control transaccional ACID.
2. **Idempotencia y concurrencia**: Implementar bloqueos distribuidos (ej. Redis Lock por `tarjeta`) para evitar condiciones de carrera si dos terminales procesan validaciones casi simultáneas.
3. **Observabilidad y resiliencia**: Incorporar métricas de negocio (tarifas cobradas por perfil, volumen de transbordos) con Prometheus y registro estructurado en formato JSON.