# -*- coding: utf-8 -*-
import tempfile
import unittest

import numpy as np
from sklearn.preprocessing import StandardScaler

from caracteristicas import COLUMNAS_MODELO, construir_caracteristicas
from clustering import ejecutar, elegir_k, evaluar_k
from generar_dataset import ESTACIONES, generar


class TestModelo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = generar(42)
        cls.X = construir_caracteristicas(cls.df)
        cls.tmp = tempfile.mkdtemp()
        csv = f"{cls.tmp}/datos.csv"
        cls.df.to_csv(csv, index=False)
        cls.res, cls.perfiles, cls.metricas, cls.resumen = ejecutar(csv, None, cls.tmp)

    def test_forma_matriz_caracteristicas(self):
        self.assertEqual(self.X.shape, (len(ESTACIONES), len(COLUMNAS_MODELO)))

    def test_caracteristicas_sin_nan_ni_inf(self):
        self.assertTrue(np.isfinite(self.X.values).all())

    def test_porcentajes_de_franjas_razonables(self):
        suma = self.X[["pct_manana", "pct_valle", "pct_tarde"]].sum(axis=1)
        self.assertTrue(((suma > 60) & (suma < 100)).all())  # falta la franja noche

    def test_escalado_media_cero_desviacion_uno(self):
        Z = StandardScaler().fit_transform(self.X.values)
        self.assertTrue(np.allclose(Z.mean(axis=0), 0, atol=1e-9))
        self.assertTrue(np.allclose(Z.std(axis=0), 1, atol=1e-9))

    def test_cada_estacion_en_un_solo_cluster(self):
        self.assertEqual(len(self.res), len(ESTACIONES))
        self.assertTrue(self.res.cluster_kmeans.notna().all())

    def test_k_elegido_en_rango(self):
        self.assertIn(self.resumen["k_usado"], range(2, 7))

    def test_calidad_silueta_minima(self):
        self.assertGreater(self.resumen["silueta_kmeans"], 0.5)

    def test_acuerdo_con_perfiles_sinteticos(self):
        self.assertGreater(self.resumen["ari_kmeans_vs_perfil_sintetico"], 0.8)

    def test_kmeans_y_jerarquico_coinciden(self):
        self.assertGreater(self.resumen["ari_kmeans_vs_jerarquico"], 0.9)

    def test_hubs_agrupados_juntos(self):
        hubs = self.res.loc[["san_antonio", "acevedo", "san_javier"], "cluster_kmeans"]
        self.assertEqual(hubs.nunique(), 1)

    def test_arvi_es_ocio_turistico(self):
        self.assertEqual(self.res.loc["arvi", "perfil"], "Ocio / turístico")

    def test_reproducibilidad_del_modelo(self):
        r2 = ejecutar(f"{self.tmp}/datos.csv", None, self.tmp)[0]
        self.assertTrue((r2.cluster_kmeans.values == self.res.cluster_kmeans.values).all())

    def test_k_forzado(self):
        r = ejecutar(f"{self.tmp}/datos.csv", 3, self.tmp)[0]
        self.assertEqual(r.cluster_kmeans.nunique(), 3)


if __name__ == "__main__":
    unittest.main()
