# Descripción de los datos

## 1. Fuentes de datos identificadas (reales)

| Fuente | Contenido | Granularidad | Observación |
|---|---|---|---|
| [datos.gov.co – Pasajeros Movilizados (Afluencia)](https://www.datos.gov.co/Transporte/Pasajeros-Movilizados-Afluencia/9dbb-kbnv) | Pasajeros del Metro de Medellín | Por **línea**, día y hora | No distingue estaciones |
| [Portal de datos abiertos del Metro de Medellín (ArcGIS)](https://datosabiertos-metrodemedellin.opendata.arcgis.com/) | Estaciones del sistema (datos geográficos) | Por estación | Ubicación, no afluencia |
| [MEData – Alcaldía de Medellín](https://www.medellin.gov.co/es/transparencia/medata/) | ~600 conjuntos de datos (movilidad, seguridad, etc.) | Variable | Fuente complementaria |

**Conclusión:** en las fuentes revisadas no encontramos afluencia **por estación y hora**, que es lo
que necesita el modelo para agrupar estaciones. Por eso, siguiendo la guía de la actividad,
se construyó un **dataset sintético** (una muestra simulada). Si en el futuro se consigue el dato real
por estación, basta reemplazar el CSV con el mismo esquema de columnas.

> Antes de entregar, verifiquen que los enlaces sigan activos y ajusten esta tabla si encuentran otra fuente.

## 2. Dataset sintético: `data/afluencia_horaria_estaciones.csv`

- Generado con `generar_dataset.py` (semilla fija 42 → reproducible).
- **1 890 filas** = 35 estaciones × 3 tipos de día × 18 horas (05:00–22:00).
- Red: modelo esquemático Metro/Metrocable de Medellín de la Actividad 3 (líneas A, B, K, L, J).

| Columna | Tipo | Descripción |
|---|---|---|
| `estacion_id` | texto | Identificador de la estación (ej. `san_antonio`) |
| `estacion` | texto | Nombre visible |
| `lineas` | texto | Líneas que sirven la estación, separadas por `;` |
| `n_lineas` | entero | Número de líneas (1 o 2) |
| `tipo_dia` | texto | `laboral`, `sabado`, `domingo` |
| `hora` | entero | Hora de inicio de la franja (5–22) |
| `abordajes` | entero | Pasajeros que entran en esa hora |
| `descensos` | entero | Pasajeros que salen en esa hora |
| `perfil_sintetico` | texto | Perfil con el que se simuló la estación (R, L, H, T). **No se usa para entrenar**; solo para validar el modelo |

### Cómo se simuló
Cada estación recibe un perfil (Residencial, Laboral/comercial, Hub, Turístico/ocio) que define
la forma de su curva horaria (picos de mañana/tarde), el volumen diario y cómo cambia en fin de semana.
Sobre la curva se aplica ruido log-normal (σ = 0.08) para que no sea determinista.
**Los valores son ilustrativos; no representan cifras oficiales del Metro.**

## 3. Características para el modelo (35 filas × 7 columnas)

Calculadas en `caracteristicas.py` a partir del día laboral (excepto el índice de fin de semana):

| Característica | Significado |
|---|---|
| `log_abordajes_laboral` | Tamaño de la estación (log10 de abordajes diarios) |
| `pct_manana` | % de abordajes en pico de mañana (05–08 h) |
| `pct_valle` | % de abordajes en valle (09–15 h) |
| `pct_tarde` | % de abordajes en pico de tarde (16–19 h) |
| `log_ratio_manana` | log(abordajes / descensos) en el pico de mañana (>0: origen, <0: destino) |
| `indice_fin_semana` | Abordajes de domingo / abordajes de día laboral |
| `n_lineas` | Número de líneas que sirven la estación |

Las variables se estandarizan (media 0, desviación 1) con `StandardScaler` antes de agrupar.

## 4. Limitaciones
- Datos simulados con 4 perfiles definidos de antemano: las métricas de calidad altas son esperables
  y **no prueban** el desempeño con datos reales.
- Solo 35 estaciones; no se modelan eventos especiales, clima ni festivos.
