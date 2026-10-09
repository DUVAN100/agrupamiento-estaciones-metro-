# -*- coding: utf-8 -*-
"""
generar_dataset.py
------------------
Genera un dataset SINTÉTICO de afluencia horaria por estación para el modelo
esquemático del sistema Metro/Metrocable de Medellín (mismo modelo de la
Actividad 3).

¿Por qué sintético? Los datos abiertos públicos encontrados (datos.gov.co,
portal de datos abiertos del Metro) reportan afluencia por LÍNEA, día y hora,
no por estación. Para agrupar estaciones necesitamos granularidad por estación,
así que se simula una muestra con patrones realistas y semilla fija
(reproducible). Ver docs/DESCRIPCION_DATOS.md.

Salida: data/afluencia_horaria_estaciones.csv
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

SEMILLA = 42
HORAS = list(range(5, 23))            # 05:00 a 22:00 (18 franjas)
TIPOS_DIA = ["laboral", "sabado", "domingo"]

# id: (nombre, lineas, perfil_generador)
#   R = residencial (origen) | L = laboral/comercial (destino)
#   H = hub de trasbordo     | T = turístico/ocio
ESTACIONES = {
    "niquia": ("Niquía", "A", "R"), "bello": ("Bello", "A", "R"),
    "madera": ("Madera", "A", "R"), "acevedo": ("Acevedo", "A;K", "H"),
    "tricentenario": ("Tricentenario", "A", "R"), "caribe": ("Caribe", "A", "L"),
    "universidad": ("Universidad", "A", "L"), "hospital": ("Hospital", "A", "L"),
    "prado": ("Prado", "A", "L"), "parque_berrio": ("Parque Berrío", "A", "T"),
    "san_antonio": ("San Antonio", "A;B", "H"), "alpujarra": ("Alpujarra", "A", "L"),
    "exposiciones": ("Exposiciones", "A", "L"), "industriales": ("Industriales", "A", "L"),
    "poblado": ("Poblado", "A", "T"), "aguacatala": ("Aguacatala", "A", "L"),
    "ayura": ("Ayurá", "A", "L"), "envigado": ("Envigado", "A", "R"),
    "itagui": ("Itagüí", "A", "R"), "sabaneta": ("Sabaneta", "A", "R"),
    "la_estrella": ("La Estrella", "A", "R"),
    "cisneros": ("Cisneros", "B", "L"), "suarez": ("Suárez", "B", "L"),
    "estadio": ("Estadio", "B", "T"), "floresta": ("Floresta", "B", "R"),
    "santa_lucia": ("Santa Lucía", "B", "R"), "simon_bolivar": ("Simón Bolívar", "B", "R"),
    "san_javier": ("San Javier", "B;J", "H"),
    "andalucia": ("Andalucía", "K", "R"), "popular": ("Popular", "K", "R"),
    "santo_domingo": ("Santo Domingo Savio", "K;L", "R"),
    "arvi": ("Arví", "L", "T"),
    "juan_xxiii": ("Juan XXIII", "J", "R"), "vallejuelos": ("Vallejuelos", "J", "R"),
    "la_aurora": ("La Aurora", "J", "R"),
}

# Pesos (mañana, valle, tarde, noche) de abordajes y descensos en día laboral
PESOS = {
    "R": {"ab": (0.40, 0.25, 0.25, 0.10), "de": (0.12, 0.25, 0.50, 0.13)},
    "L": {"ab": (0.12, 0.28, 0.45, 0.15), "de": (0.50, 0.25, 0.18, 0.07)},
    "H": {"ab": (0.28, 0.30, 0.32, 0.10), "de": (0.28, 0.30, 0.32, 0.10)},
    "T": {"ab": (0.05, 0.60, 0.27, 0.08), "de": (0.05, 0.60, 0.27, 0.08)},
}
PESO_FIN_SEMANA = np.array([0.08, 0.55, 0.27, 0.10])
# Factor de volumen por tipo de día (laboral, sábado, domingo)
FACTOR_DIA = {
    "R": (1.0, 0.65, 0.45), "L": (1.0, 0.60, 0.35),
    "H": (1.0, 0.70, 0.50), "T": (0.45, 1.30, 1.70),
}
RANGO_VOLUMEN = {"R": (9000, 22000), "L": (14000, 34000),
                 "H": (55000, 85000), "T": (5000, 12000)}


def _curva(pesos):
    """Curva horaria (18 valores que suman 1) a partir de 4 pesos por franja."""
    h = np.array(HORAS, dtype=float)

    def bump(mu, sd):
        b = np.exp(-0.5 * ((h - mu) / sd) ** 2)
        return b / b.sum()

    c = (pesos[0] * bump(6.5, 1.2) + pesos[1] * bump(12.0, 3.0)
         + pesos[2] * bump(17.5, 1.5) + pesos[3] * bump(20.5, 1.2))
    return c / c.sum()


def generar(semilla=SEMILLA):
    rng = np.random.default_rng(semilla)
    filas = []
    for eid, (nombre, lineas, perfil) in ESTACIONES.items():
        n_lineas = len(lineas.split(";"))
        base = rng.uniform(*RANGO_VOLUMEN[perfil])
        for i, tipo in enumerate(TIPOS_DIA):
            vol = base * FACTOR_DIA[perfil][i]
            pesos_ab = np.array(PESOS[perfil]["ab"])
            pesos_de = np.array(PESOS[perfil]["de"])
            if tipo != "laboral":   # el fin de semana los picos se aplanan
                pesos_ab = 0.4 * pesos_ab + 0.6 * PESO_FIN_SEMANA
                pesos_de = 0.4 * pesos_de + 0.6 * PESO_FIN_SEMANA
            c_ab, c_de = _curva(pesos_ab), _curva(pesos_de)
            ab = np.round(vol * c_ab * rng.lognormal(0, 0.08, len(HORAS))).astype(int)
            de = np.round(vol * c_de * rng.lognormal(0, 0.08, len(HORAS))).astype(int)
            for k, hora in enumerate(HORAS):
                filas.append((eid, nombre, lineas, n_lineas, tipo, hora,
                              int(ab[k]), int(de[k]), perfil))
    cols = ["estacion_id", "estacion", "lineas", "n_lineas", "tipo_dia",
            "hora", "abordajes", "descensos", "perfil_sintetico"]
    return pd.DataFrame(filas, columns=cols)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default="data/afluencia_horaria_estaciones.csv")
    ap.add_argument("--semilla", type=int, default=SEMILLA)
    a = ap.parse_args()
    df = generar(a.semilla)
    Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.salida, index=False, encoding="utf-8")
    print(f"Dataset generado: {a.salida} ({len(df)} filas, "
          f"{df.estacion_id.nunique()} estaciones)")
