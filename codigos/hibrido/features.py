"""Nombres públicos de las funciones temporales implementadas en ``gaps``.

No hay dos algoritmos de características: estos alias mantienen una sola
implementación verificable del calendario incompleto.
"""
from .gaps import gap_features, gap_partitions, gap_samples


row_features = gap_features
samples = gap_samples
partitions = gap_partitions
