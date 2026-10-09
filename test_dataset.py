# -*- coding: utf-8 -*-
import unittest

import pandas as pd

from generar_dataset import ESTACIONES, HORAS, TIPOS_DIA, generar


class TestDataset(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = generar(42)

    def test_numero_de_filas(self):
        esperado = len(ESTACIONES) * len(TIPOS_DIA) * len(HORAS)
        self.assertEqual(len(self.df), esperado)          # 35*3*18 = 1890

    def test_sin_nulos(self):
        self.assertEqual(int(self.df.isnull().sum().sum()), 0)

    def test_valores_no_negativos(self):
        self.assertTrue((self.df.abordajes >= 0).all())
        self.assertTrue((self.df.descensos >= 0).all())

    def test_reproducible_con_misma_semilla(self):
        pd.testing.assert_frame_equal(generar(42), generar(42))

    def test_semillas_distintas_dan_datos_distintos(self):
        self.assertFalse(generar(1).abordajes.equals(generar(2).abordajes))

    def test_residencial_tiene_mas_abordajes_en_pico_manana_que_laboral(self):
        lab = self.df[(self.df.tipo_dia == "laboral") & (self.df.hora.between(5, 8))]
        frac = lab.groupby("perfil_sintetico").apply(
            lambda g: g.abordajes.sum() /
            self.df[(self.df.tipo_dia == "laboral") &
                    (self.df.perfil_sintetico == g.name)].abordajes.sum(),
            include_groups=False)
        self.assertGreater(frac["R"], frac["L"])

    def test_turistico_domingo_supera_dia_laboral(self):
        t = self.df[self.df.perfil_sintetico == "T"]
        lab = t[t.tipo_dia == "laboral"].abordajes.sum()
        dom = t[t.tipo_dia == "domingo"].abordajes.sum()
        self.assertGreater(dom, lab)


if __name__ == "__main__":
    unittest.main()
