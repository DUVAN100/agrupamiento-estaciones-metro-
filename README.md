# Actividad 4 — Aprendizaje no supervisado: agrupamiento de estaciones de transporte masivo

Continuación del proyecto de rutas en el sistema Metro/Metrocable (modelo esquemático de Medellín).
Se agrupan las estaciones según su patrón de afluencia usando **K-Means** (modelo principal) y
**agrupamiento jerárquico (Ward)** (contraste), con PCA para visualizar.
Referencia: cap. 16 (Técnicas de agrupamiento), Palma Méndez (2008).

## Estructura
```
data/afluencia_horaria_estaciones.csv   # fuente de datos (sintética)
generar_dataset.py                       # genera el dataset (semilla 42)
caracteristicas.py                       # ingeniería de características
clustering.py                            # modelo no supervisado + gráficos
tests/                                   # 20 pruebas unitarias
docs/DESCRIPCION_DATOS.md                # fuentes y descripción de los datos
docs/PRUEBAS.md                          # pruebas y resultados
resultados/                              # clusters, métricas y gráficos
```

## Ejecución
```bash
pip install -r requirements.txt
python generar_dataset.py        # opcional: el CSV ya viene incluido
python clustering.py             # k automático (silueta)
python clustering.py --k 3       # forzar k
python -m unittest discover -s tests -t . -v
```

## Resultado principal
4 grupos: Laboral/comercial (11), Residencial (16), Ocio/turístico (4) y Hub de trasbordo (4);
silueta 0.84. Detalle en `docs/PRUEBAS.md`.

## Aplicación al proyecto de rutas
Los perfiles permiten, por ejemplo, ponderar el costo de espera/trasbordo según el tipo de estación
y hora (trabajo futuro).

## Lista de entrega
- [ ] Repo en GitHub/GitLab con **commits de cada integrante** (el log debe mostrarlo)
- [ ] **Tutor agregado como colaborador** del repo
- [ ] Video ≤ 10 min con todos los integrantes
- [ ] PDF con los enlaces: datos, código, descripción de datos, pruebas y video
