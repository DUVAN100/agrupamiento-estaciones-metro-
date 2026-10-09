# Pruebas realizadas al componente

## 1. Cómo ejecutarlas
```bash
pip install -r requirements.txt
python -m unittest discover -s tests -t . -v
```
Salida completa guardada en `resultados/salida_pruebas.txt`.

## 2. Resultado: **20 pruebas, 20 exitosas** (≈ 3 s)

### Pruebas del dataset (`tests/test_dataset.py`) — 7
| Prueba | Qué verifica |
|---|---|
| `test_numero_de_filas` | 35 × 3 × 18 = 1 890 filas |
| `test_sin_nulos` | No hay valores faltantes |
| `test_valores_no_negativos` | Abordajes y descensos ≥ 0 |
| `test_reproducible_con_misma_semilla` | Misma semilla → mismo dataset |
| `test_semillas_distintas_dan_datos_distintos` | Semillas distintas → datos distintos |
| `test_residencial_..._pico_manana_que_laboral` | Las estaciones residenciales concentran más abordajes en la mañana que las laborales |
| `test_turistico_domingo_supera_dia_laboral` | Estaciones de ocio: domingo > día laboral |

### Pruebas del modelo (`tests/test_modelo.py`) — 13
| Prueba | Qué verifica |
|---|---|
| `test_forma_matriz_caracteristicas` | Matriz de 35 × 7 |
| `test_caracteristicas_sin_nan_ni_inf` | Valores finitos |
| `test_porcentajes_de_franjas_razonables` | Franjas mañana+valle+tarde entre 60 % y 100 % |
| `test_escalado_media_cero_desviacion_uno` | Estandarización correcta |
| `test_cada_estacion_en_un_solo_cluster` | Toda estación queda asignada |
| `test_k_elegido_en_rango` | k automático dentro de 2–6 |
| `test_calidad_silueta_minima` | Silueta > 0.5 |
| `test_acuerdo_con_perfiles_sinteticos` | ARI > 0.8 frente a los perfiles de simulación |
| `test_kmeans_y_jerarquico_coinciden` | ARI K-Means vs Ward > 0.9 |
| `test_hubs_agrupados_juntos` | San Antonio, Acevedo y San Javier en el mismo grupo |
| `test_arvi_es_ocio_turistico` | Arví clasificado como ocio/turístico |
| `test_reproducibilidad_del_modelo` | Dos ejecuciones dan igual agrupación |
| `test_k_forzado` | `--k 3` produce exactamente 3 grupos |

## 3. Resultados del modelo (ejecución real)

| Métrica | Valor |
|---|---|
| k elegido (mayor silueta entre 2 y 6) | **4** |
| Silueta K-Means | 0.837 |
| Davies-Bouldin K-Means (menor es mejor) | 0.294 |
| ARI K-Means vs. perfiles sintéticos | 0.927 |
| ARI K-Means vs. jerárquico (Ward) | 1.000 |

Silueta por k: k=2 → 0.551, k=3 → 0.707, **k=4 → 0.837**, k=5 → 0.827, k=6 → 0.704.

### Grupos encontrados
| Cluster | Perfil | Estaciones |
|---|---|---|
| 0 | Laboral / comercial (destino) | Aguacatala, Alpujarra, Ayurá, Caribe, Cisneros, Exposiciones, Hospital, Industriales, Prado, Suárez, Universidad |
| 1 | Residencial (origen) | Andalucía, Bello, Envigado, Floresta, Itagüí, Juan XXIII, La Aurora, La Estrella, Madera, Niquía, Popular, Sabaneta, Santa Lucía, Simón Bolívar, Tricentenario, Vallejuelos |
| 2 | Ocio / turístico | Arví, Estadio, Parque Berrío, Poblado |
| 3 | Hub de trasbordo | Acevedo, San Antonio, San Javier, Santo Domingo Savio |

## 4. Análisis
- El ARI de 0.927 (no 1.0) se debe a **una sola estación**: Santo Domingo Savio se simuló como
  residencial, pero el modelo la agrupó con los hubs porque sirve dos líneas (K y L) y `n_lineas`
  pesa en la distancia. Es un caso interesante para discutir: el algoritmo agrupa por las
  características que recibe, no por la etiqueta con que se simuló.
- k=4 y k=5 tienen silueta similar (0.837 vs 0.827); se eligió k=4 por la mayor silueta y por ser más interpretable.
- K-Means y el método jerárquico coinciden totalmente, lo que da confianza en la estabilidad de los grupos.
- **Advertencia:** al ser datos sintéticos con 4 perfiles prediseñados, estas métricas altas son
  esperables y no garantizan igual desempeño con datos reales.

## 5. Gráficos generados (`resultados/`)
`01_codo_y_silueta.png`, `02_clusters_pca.png`, `03_perfil_horario_por_cluster.png`
