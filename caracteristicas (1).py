# -*- coding: utf-8 -*-
"""
caracteristicas.py
------------------
Convierte la afluencia horaria (1890 filas) en una matriz de características
con UNA fila por estación (35 x 7), lista para agrupamiento.

Franjas: pico mañana 05-08 | valle 09-15 | pico tarde 16-19 | noche 20-22
"""
import numpy as np
import pandas as pd

FRANJAS = {
    "manana": range(5, 9),
    "valle": range(9, 16),
    "tarde": range(16, 20),
    "noche": range(20, 23),
}

COLUMNAS_MODELO = [
    "log_abordajes_laboral",     # tamaño de la estación (escala log)
    "pct_manana",                # % abordajes en pico mañana (día laboral)
    "pct_valle",                 # % abordajes en valle
    "pct_tarde",                 # % abordajes en pico tarde
    "log_ratio_manana",          # log(abordajes / descensos) en pico mañana
    "indice_fin_semana",         # abordajes domingo / abordajes laboral
    "n_lineas",                  # número de líneas que sirven la estación
]


def construir_caracteristicas(df):
    """Retorna DataFrame indexado por estacion_id con COLUMNAS_MODELO."""
    lab = df[df.tipo_dia == "laboral"]
    filas = {}
    for eid, g in lab.groupby("estacion_id"):
        total_ab = g.abordajes.sum()
        franja = {
            nombre: g[g.hora.isin(horas)].abordajes.sum() / total_ab
            for nombre, horas in FRANJAS.items()
        }
        m = g[g.hora.isin(FRANJAS["manana"])]
        ratio = m.abordajes.sum() / max(m.descensos.sum(), 1)
        dom = df[(df.estacion_id == eid) & (df.tipo_dia == "domingo")].abordajes.sum()
        filas[eid] = {
            "log_abordajes_laboral": np.log10(total_ab),
            "pct_manana": 100 * franja["manana"],
            "pct_valle": 100 * franja["valle"],
            "pct_tarde": 100 * franja["tarde"],
            "log_ratio_manana": np.log(ratio),
            "indice_fin_semana": dom / total_ab,
            "n_lineas": int(g.n_lineas.iloc[0]),
        }
    X = pd.DataFrame.from_dict(filas, orient="index")[COLUMNAS_MODELO]
    X.index.name = "estacion_id"
    return X
