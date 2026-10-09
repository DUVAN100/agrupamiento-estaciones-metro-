# -*- coding: utf-8 -*-
"""
clustering.py
-------------
Aprendizaje NO supervisado sobre estaciones del sistema de transporte masivo
(Actividad 4). Técnicas de agrupamiento (cap. 16, Palma Méndez, 2008):

  1. K-Means (modelo principal), con k elegido por coeficiente de silueta
  2. Agrupamiento jerárquico aglomerativo (Ward) como modelo de contraste
  3. PCA solo para visualizar en 2D

Uso:
    python clustering.py                # elige k automáticamente (2..6)
    python clustering.py --k 4          # fuerza k
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (adjusted_rand_score, davies_bouldin_score,
                             silhouette_score)
from sklearn.preprocessing import StandardScaler

from caracteristicas import COLUMNAS_MODELO, construir_caracteristicas

SEMILLA = 42
RUTA_DATOS = "data/afluencia_horaria_estaciones.csv"


def evaluar_k(X_esc, k_min=2, k_max=8):
    """Inercia, silueta y Davies-Bouldin para cada k de K-Means."""
    filas = []
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=SEMILLA).fit(X_esc)
        filas.append({
            "k": k,
            "inercia": float(km.inertia_),
            "silueta": float(silhouette_score(X_esc, km.labels_)),
            "davies_bouldin": float(davies_bouldin_score(X_esc, km.labels_)),
        })
    return pd.DataFrame(filas)


def elegir_k(metricas, k_max_busqueda=6):
    """k con mayor silueta dentro de 2..k_max_busqueda."""
    sub = metricas[metricas.k <= k_max_busqueda]
    return int(sub.loc[sub.silueta.idxmax(), "k"])


def nombrar_cluster(perfil):
    """Etiqueta interpretable según el centroide (en unidades originales)."""
    if perfil["n_lineas"] > 1.5:
        return "Hub de trasbordo"
    if perfil["indice_fin_semana"] > 0.9:
        return "Ocio / turístico"
    if perfil["log_ratio_manana"] > 0:
        return "Residencial (origen)"
    return "Laboral / comercial (destino)"


def ejecutar(ruta_datos=RUTA_DATOS, k=None, salida="resultados"):
    out = Path(salida)
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(ruta_datos)
    X = construir_caracteristicas(df)
    X_esc = StandardScaler().fit_transform(X.values)

    metricas = evaluar_k(X_esc)
    metricas.to_csv(out / "metricas_por_k.csv", index=False)
    k_usado = k if k else elegir_k(metricas)

    km = KMeans(n_clusters=k_usado, n_init=10, random_state=SEMILLA).fit(X_esc)
    jer = AgglomerativeClustering(n_clusters=k_usado, linkage="ward").fit(X_esc)

    nombres = df.drop_duplicates("estacion_id").set_index("estacion_id")["estacion"]
    res = X.copy()
    res.insert(0, "estacion", nombres.loc[X.index].values)
    res["cluster_kmeans"] = km.labels_
    res["cluster_jerarquico"] = jer.labels_

    perfiles = res.groupby("cluster_kmeans")[COLUMNAS_MODELO].mean()
    perfiles["perfil"] = perfiles.apply(nombrar_cluster, axis=1)
    perfiles["n_estaciones"] = res.groupby("cluster_kmeans").size()
    res["perfil"] = res.cluster_kmeans.map(perfiles["perfil"])

    # Validación externa (posible solo porque el dataset es sintético)
    verdad = df.drop_duplicates("estacion_id").set_index("estacion_id")["perfil_sintetico"]
    ari_vs_verdad = adjusted_rand_score(verdad.loc[X.index], km.labels_)
    ari_kmeans_vs_jer = adjusted_rand_score(km.labels_, jer.labels_)

    resumen = {
        "k_usado": k_usado,
        "silueta_kmeans": float(silhouette_score(X_esc, km.labels_)),
        "silueta_jerarquico": float(silhouette_score(X_esc, jer.labels_)),
        "davies_bouldin_kmeans": float(davies_bouldin_score(X_esc, km.labels_)),
        "ari_kmeans_vs_perfil_sintetico": float(ari_vs_verdad),
        "ari_kmeans_vs_jerarquico": float(ari_kmeans_vs_jer),
    }

    res.to_csv(out / "clusters_estaciones.csv", encoding="utf-8")
    perfiles.round(3).to_csv(out / "perfiles_cluster.csv", encoding="utf-8")
    (out / "resumen_metricas.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")

    _graficar(metricas, k_usado, X_esc, res, out)
    return res, perfiles, metricas, resumen


def _graficar(metricas, k_usado, X_esc, res, out):
    # 1) Codo + silueta
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].plot(metricas.k, metricas.inercia, "o-")
    ax[0].set(title="Método del codo", xlabel="k", ylabel="Inercia")
    ax[1].plot(metricas.k, metricas.silueta, "o-", color="tab:green")
    ax[1].axvline(k_usado, ls="--", color="gray")
    ax[1].set(title="Coeficiente de silueta", xlabel="k", ylabel="Silueta")
    fig.tight_layout()
    fig.savefig(out / "01_codo_y_silueta.png", dpi=130)
    plt.close(fig)

    # 2) PCA 2D con etiquetas de estación
    pca = PCA(n_components=2, random_state=SEMILLA)
    P = pca.fit_transform(X_esc)
    fig, ax = plt.subplots(figsize=(9, 6.5))
    for c in sorted(res.cluster_kmeans.unique()):
        m = (res.cluster_kmeans == c).values
        ax.scatter(P[m, 0], P[m, 1], s=70, label=f"{c}: {res.perfil[m].iloc[0]}")
    for i, nombre in enumerate(res.estacion):
        ax.annotate(nombre, (P[i, 0], P[i, 1]), fontsize=7,
                    xytext=(3, 3), textcoords="offset points")
    var = pca.explained_variance_ratio_ * 100
    ax.set(title="Estaciones agrupadas con K-Means (proyección PCA)",
           xlabel=f"PC1 ({var[0]:.0f}% var.)", ylabel=f"PC2 ({var[1]:.0f}% var.)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "02_clusters_pca.png", dpi=130)
    plt.close(fig)

    # 3) Perfil horario laboral promedio por cluster
    df = pd.read_csv(RUTA_DATOS)
    df = df[df.tipo_dia == "laboral"].merge(
        res[["cluster_kmeans", "perfil"]], left_on="estacion_id", right_index=True)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for (c, perfil), g in df.groupby(["cluster_kmeans", "perfil"]):
        curva = g.groupby("hora").abordajes.sum()
        ax.plot(curva.index, 100 * curva / curva.sum(), "o-", label=f"{c}: {perfil}")
    ax.set(title="Perfil horario de abordajes (día laboral)",
           xlabel="Hora", ylabel="% de abordajes del día")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "03_perfil_horario_por_cluster.png", dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=None, help="número de clusters")
    ap.add_argument("--datos", default=RUTA_DATOS)
    ap.add_argument("--salida", default="resultados")
    a = ap.parse_args()

    res, perfiles, metricas, resumen = ejecutar(a.datos, a.k, a.salida)
    print("\n== Métricas por k ==")
    print(metricas.round(3).to_string(index=False))
    print(f"\n== k elegido: {resumen['k_usado']} ==")
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    print("\n== Perfiles de cluster ==")
    print(perfiles.round(2).to_string())
    print("\n== Estaciones por cluster ==")
    for c, g in res.groupby("cluster_kmeans"):
        print(f"[{c}] {g.perfil.iloc[0]}: {', '.join(g.estacion)}")
    print(f"\nResultados guardados en '{a.salida}/'")
