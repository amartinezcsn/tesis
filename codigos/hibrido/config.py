"""Parámetros congelados que hacen reproducible una corrida.

El archivo JSON define fuentes, periodos y candidatos. Aquí se rechazan
parámetros inválidos antes de leer o entrenar con los datos.
"""
from dataclasses import dataclass, asdict, fields
from pathlib import Path
import json


@dataclass(frozen=True)
class Config:
    """Contrato completo del experimento; una instancia no cambia al ejecutarse."""
    # Fuentes auditadas y decisiones documentales sobre su uso.
    source: str = 'datasets/xlsx/Compras.xlsx'
    source_sheet: str | int = 0
    source_sha256: str = ''
    source_approved: bool = False
    approved_duplicate_rows: tuple = ()
    coverage: str = 'input/hibrido/cobertura.csv'
    coverage_sheet: str | int = 0
    catalog: str = 'input/hibrido/catalogo.csv'
    catalog_sheet: str | int = 0
    exogenous: str | None = None
    sales: str | None = None
    # Periodo y separación temporal: desarrollo, validación interna y prueba.
    start: str = ''
    end: str = ''
    imputation_start: str | None = None
    imputation_end: str | None = None
    holdout_weeks: int = 16
    tuning_origins: int = 8
    # Rolling real: None/1 conserva el contrato de fixtures legacy.
    training_window_weeks: int | None = None
    rolling_step_weeks: int = 1
    rolling_origin_start: int | None = None
    horizons: tuple = (1, 2, 3, 4)
    weights: tuple = (0.25, 0.5, 0.75)
    alphas: tuple = (0.1, 0.3, 0.6)
    threshold: float = 0.8
    # Semilla, remuestreo y familias de modelos candidatas.
    seed: int = 42
    bootstrap_samples: int = 2000
    bootstrap_block: int = 4
    min_inference_weeks: int = 12
    use_rf: bool = True
    use_arima: bool = True
    min_training_observations: int = 24
    zero_targets_valid: bool = True

    def validate(self):
        """Fallar temprano si un parámetro contradice el protocolo."""
        if type(self.min_training_observations) is not int or self.min_training_observations < 8:
            raise ValueError('min_training_observations requiere entero >= 8.')
        for key in ('source_approved','use_rf','use_arima','zero_targets_valid'):
            if not isinstance(getattr(self,key),bool):
                raise ValueError(f'{key} requiere booleano JSON true/false, no texto.')
        duplicate_rows = self.approved_duplicate_rows
        if not isinstance(duplicate_rows, (list, tuple)) or any(
            type(row) is not int or row < 2 for row in duplicate_rows
        ) or len(set(duplicate_rows)) != len(duplicate_rows):
            raise ValueError('approved_duplicate_rows requiere filas Excel unicas, enteras y mayores o iguales a 2.')
        for key in ('holdout_weeks','tuning_origins','rolling_step_weeks','bootstrap_samples','bootstrap_block','min_inference_weeks','seed'):
            if type(getattr(self,key)) is not int or getattr(self,key)<1:
                raise ValueError(f'{key} requiere entero positivo.')
        if self.training_window_weeks is not None and (
            type(self.training_window_weeks) is not int or self.training_window_weeks < self.lookback
        ):
            raise ValueError('training_window_weeks requiere entero >= lookback o null.')
        if self.rolling_origin_start is not None and (
            type(self.rolling_origin_start) is not int or self.rolling_origin_start < self.lookback
        ):
            raise ValueError('rolling_origin_start requiere entero >= lookback o null.')
        if tuple(self.horizons) != (1, 2, 3, 4):
            raise ValueError('Esta versión implementa los cuatro horizontes 1..4.')
        if self.holdout_weeks < 4 or self.tuning_origins < 2:
            raise ValueError('Partición insuficiente.')
        if (self.imputation_start is None) != (self.imputation_end is None):
            raise ValueError('imputation_start e imputation_end deben definirse juntos.')
        if self.imputation_start is not None:
            import pandas as pd
            imp_start=pd.Timestamp(self.imputation_start);imp_end=pd.Timestamp(self.imputation_end)
            if imp_start.dayofweek or imp_end.dayofweek or imp_end < imp_start:
                raise ValueError('El periodo de imputación debe ser lunes a lunes en orden.')
            if self.start and self.end and (imp_start < pd.Timestamp(self.start) or imp_end > pd.Timestamp(self.end)):
                raise ValueError('El periodo de imputación debe estar dentro del periodo general.')
        if not 0 < self.threshold <= 1 or any(not 0 < w < 1 for w in self.weights):
            raise ValueError('Umbral/pesos inválidos; un híbrido requiere dos componentes.')
        if not self.weights or not self.alphas or any(not 0 < a <= 1 for a in self.alphas):
            raise ValueError('Pesos y parámetros de composición obligatorios.')
        if self.bootstrap_samples < 100 or self.bootstrap_block < 1:
            raise ValueError('Configuración de remuestreo insuficiente.')
        return self

    @property
    def lookback(self):
        """Historia mínima de cuatro semanas para construir predictores."""
        return 4

    def dictionary(self):
        """Convertir los parámetros a un diccionario para el manifiesto."""
        return asdict(self)


def load_config(path):
    """Leer el JSON sin admitir claves desconocidas ni valores fuera de contrato."""
    values = json.loads(Path(path).read_text(encoding='utf-8'))
    unknown = set(values) - {f.name for f in fields(Config)}
    if unknown:
        raise ValueError(f'Claves desconocidas: {sorted(unknown)}')
    return Config(**values).validate()
