# Bitácora de Uso de IA — Prueba Técnica Desarrollador Python Junior

## 1. Herramientas utilizadas

Se utilizó **Google Antigravity** con el modelo **Gemini 3.8 Flash (High)** en modalidad pair programmer interactivo, con terminal PowerShell integrada para ejecución de pruebas unitarias/integración, construcción de imágenes en Docker y control de versiones con Git.
Se utilizó  **Google Gemini** con el modelo **Argon** Utilizado como asistente de análisis del repositorio y resolución de dudas sobre el entorno de ejecución (Docker y pytest).

## 2. Los tres mejores prompts utilizados

### Prompt 1: Análisis arquitectónico y causa raíz (sin asumir supuestos)
> *"Actúa como un desarrollador Python que debe resolver una prueba técnica sobre un servicio de tarifas de transporte público. Trabaja sobre el repositorio: primero inspecciona su estructura, código, pruebas, configuración, almacenamiento y el historial de Git. Antes de modificar archivos, resume brevemente los hallazgos relevantes identificando la causa raíz de BUG-17 y las deficiencias del cálculo tarifario actual. Mantén los contratos existentes y evita cambios innecesarios."*

### Prompt 2: Implementación matemática estricta y lógica de dominio
> *"Actualiza el endpoint POST /tarifas/calcular implementando la máquina de estados de transbordo (90 minutos exactos inclusive, primer transbordo $500, segundo $0, siguiente nueva tarifa base $3.200). Refactoriza aplicar_descuento utilizando Decimal con ROUND_HALF_UP al múltiplo de $50 para garantizar que mitades exactas (ej. $325 y $225) redondeen hacia arriba. Ordena cronológicamente las validaciones respetando zonas horarias y valida con HTTP 422 fechas naive, IDs duplicados y perfiles inválidos."*

### Prompt 3: Estrategia de pruebas, control de warnings y Docker
> *"Diseña una batería de pruebas exhaustiva en tests/test_tarifas.py y tests/test_api.py que reproduzca y confirme el aislamiento de BUG-17 entre múltiples tarjetas, verifique el límite exacto de 90 min y 90m 1s, pruebe el redondeo de mitad exacta para estudiantes y adulto mayor, y procese los datos de ejemplo de validaciones_2025-03-10.json. Garantiza que pytest pase con filterwarnings = ['error'] sin apagarlo, y ajusta Dockerfile para que uvicorn enlace a 0.0.0.0."*

### Prompt 4:Prompt de auditoría sobre el archivo de pruebas (test_api.py):

>*"test_rechaza_fecha_sin_zona_horaria_con_422() Esta en el archivo test apii no la definiste"*

### Prompt 5:Prompt de depuración de estado compartido al ejecutar pytest:

>*"tests\test_api.py:201: def test_aislamiento_historial_entre_tarjetas_bug_17(): ... assert len(hist_a) == 1 -> AssertionError: assert 2 == 1. FAILED tests/test_api.py::TestApiIntegration::test_suite_api - AssertionError: assert 2 == 1"*

## 3. Discrepancias, verificación y decisiones críticas

1. **Código duplicado inicial en el archivo test_tarifas**:
   - *Hallazgo*: La IA habría duplcado el archivo test_tarifas.
   - *Problema*: El código tiraba error al realizar las pruebas por lo que fallaban los tests.
   - *Acción*: Se borró el metodo duplicado.
2. **Error en el método de calcular_tarifa en el archivo tarifas.py**:
   - *Hallazgo*: Test fallando en el método.
   - *Decisión*: Modificación de la lógica debido a que no habia validacion inicial de lista vacia, Esto significa que, si la lista está vacía, retorna inmediatamente una respuesta sin cobros.
3. **Validación activa del entorno Docker**:
   - *Hallazgo*: El contenedor no recibía peticiones debido a que `uvicorn` escuchaba en `127.0.0.1` dentro del contenedor.
   - *Acción*: Se modificó el `Dockerfile` a `--host 0.0.0.0` y se añadieron parámetros de timeout y reintentos para soportar latencia de red en `pip`.

---

## 4. Aporte del desarrollador que la IA no habría aportado sola

- **Narrativa de Git en commits semánticos**: Mantener commit por cambio logico con su respectiva rama y realizar el merge correspondiente hacia la rama principal.
- **Validar archivo docker**: El archivo docker queda actualizado para permitir su ejecución aunque la conexión sea lenta o inestable, el archivo anterior no lo permitía.