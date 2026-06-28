# F1 Race Intelligence Platform

> Proyecto personal de **aprendizaje de ingeniería de datos**: una plataforma local que ingiere, organiza y (más adelante) analiza y predice datos de Fórmula 1 usando la API pública [OpenF1](https://openf1.org/).

El objetivo no es montar una solución empresarial, sino aprender de forma ordenada el ciclo completo de datos —ingesta, capas Bronze/Silver/Gold, calidad, dashboard y un modelo predictivo simple— con herramientas gratuitas y ejecutables en local.

---

## Arquitectura (Medallion)

Los datos fluyen por capas, cada una más procesada que la anterior:

```text
OpenF1 API
   │
   ▼
Bronze   datos crudos tal como llegan de la API (Parquet)
   │
   ▼
Silver   datos limpios: tipos correctos, sin duplicados, fechas normalizadas
   │
   ▼
Gold     tablas listas para negocio: métricas por piloto, equipo y carrera
   │
   ▼
Dashboard + Modelo predictivo
```

Esta separación permite **reprocesar** sin perder nunca el dato original.

---

## Fuente de datos: OpenF1

- API: `https://api.openf1.org/v1/`
- Documentación: <https://openf1.org/docs/>
- Plan gratuito: datos históricos desde 2023, sin autenticación, en JSON/CSV.
- Límites: **3 requests/segundo** y **30 requests/minuto**.

### ⚠️ Nota importante: bloqueo durante sesiones en vivo

Mientras hay una **sesión de F1 en curso** (desde ~30 min antes hasta ~30 min después), el plan gratuito **bloquea TODO el acceso anónimo, incluida la data histórica**, devolviendo `401`:

```json
{"detail": "Live F1 session in progress. Global API access (including past sessions) is restricted to authenticated users until the session ends."}
```

Implicaciones prácticas:

- **No ejecutes la ingesta durante un fin de semana de carrera en una ventana de sesión activa**: fallará con `401`. Espera a que termine la sesión.
- El acceso **live real** durante la carrera solo está disponible en el plan de pago (sponsor tier).
- Por eso el modo "semi-en vivo" del proyecto se basa en **replay sobre datos históricos locales**, no en polling durante la carrera.

---

## Estructura del repositorio

```text
f1_engineering/
├── data/                 # Data lake local (no versionado)
│   ├── bronze/           #   crudo desde la API
│   ├── silver/           #   limpio y normalizado
│   ├── gold/             #   tablas analíticas
│   └── live/             #   estado semi-live
├── notebooks/            # Exploración y prototipos
│   └── conexion_api.ipynb#   prototipo capa Bronze (actual)
├── src/                  # Código de producción (en construcción)
│   ├── ingestion/        #   cliente OpenF1 + extractores
│   ├── transformations/  #   Bronze → Silver → Gold
│   ├── quality/          #   validaciones de datos
│   ├── features/         #   feature engineering
│   ├── models/           #   modelo predictivo
│   ├── dashboard/        #   dashboard local
│   └── utils/            #   rutas, logging, helpers
├── sql/                  # Consultas SQL (silver / gold)
├── tests/                # Pruebas
├── docs/                 # Documentación técnica
├── requirements.txt      # Dependencias
└── README.md
```

---

## Requisitos e instalación

- **Python 3.13+**

El proyecto usa [uv](https://docs.astral.sh/uv/) para gestionar el entorno y las dependencias.

```bash
# 1. Clonar
git clone <url-del-repo>
cd f1_engineering

# 2. Crear el entorno e instalar dependencias
uv sync
```

> **Alternativa** sin `uv sync` (usando el `requirements.txt`):
> ```bash
> uv venv
> uv pip install -r requirements.txt
> ```

---

## Uso

### Extracción de la capa Bronze

```bash
uv run main.py          # extrae la temporada 2024 (por defecto)
uv run main.py 2023     # extrae otra temporada
```

Descarga desde OpenF1 los catálogos (`meetings`, `drivers`, `sessions`, ...) y, por cada sesión, los endpoints de detalle (`laps`, `pit`, `stints`, `weather`, ...), guardándolos particionados en `data/bronze/`:

```text
data/bronze/laps/year=2024/session_key=9839/data.parquet
```

- **Idempotente:** si una sesión ya fue descargada, se salta. Puedes cortar con `Ctrl+C` y al re-ejecutar retoma donde quedó.
- **Rate limit:** el cliente respeta el límite de OpenF1 (~25 req/min), así que una temporada completa puede tardar varios minutos.
- Si hay una **sesión de F1 en vivo**, la API bloquea el acceso y el script lo informa sin fallar (ver la nota de bloqueo en [Fuente de datos](#fuente-de-datos-openf1)).

> **Meta a futuro:** que `main.py` orqueste todo el pipeline (Bronze → Silver → Gold). Hoy ejecuta solo la capa Bronze.

### Exploración

El notebook [`notebooks/conexion_api.ipynb`](notebooks/conexion_api.ipynb) queda como espacio de exploración rápida de la API:

```bash
uv run jupyter lab
```


---

## Stack tecnológico

| Capa | Herramienta |
|---|---|
| Lenguaje | Python |
| Entorno y dependencias | uv |
| Cliente API | httpx |
| DataFrames | pandas (→ Polars en fases siguientes) |
| Almacenamiento | Parquet (pyarrow) |
| SQL analítico | DuckDB *(planeado)* |
| Calidad | Pandera *(planeado)* |
| Orquestación | Prefect *(planeado)* |
| Dashboard | Panel + hvPlot / Streamlit *(planeado)* |
| Machine Learning | scikit-learn *(planeado)* |

---

Proyecto de aprendizaje. Sin fines comerciales.
