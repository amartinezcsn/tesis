from dataclasses import dataclass, asdict, fields
from pathlib import Path
import json


@dataclass(frozen=True)
class Config:
    source: str = 'datasets/xlsx/Compras.xlsx'
    source_sheet: str | int = 0
    source_sha256: str = ''
    source_approved: bool = False
    approved_duplicate_rows: tuple = ()
    synthetic_training_approved: bool = False
    coverage: str = 'input/hibrido/cobertura.csv'
    catalog: str = 'input/hibrido/catalogo.csv'
    exogenous: str | None = None
    sales: str | None = None
    start: str = ''
    end: str = ''
    window: int = 52
    holdout_weeks: int = 16
    tuning_origins: int = 8
    lags: tuple = (1, 2, 4, 8, 12)
    rolling: tuple = (4, 8, 12)
    horizons: tuple = (1, 2, 3, 4)
    weights: tuple = (0.25, 0.5, 0.75)
    alphas: tuple = (0.1, 0.3, 0.6)
    threshold: float = 0.8
    seed: int = 42
    bootstrap_samples: int = 2000
    bootstrap_block: int = 4
    min_inference_weeks: int = 12
    independent_holdout: bool = False
    protocol_approved: bool = False
    use_rf: bool = True
    use_arima: bool = True
    missing_policy: str = 'strict'
    min_training_observations: int = 24

    def validate(self):
        if self.missing_policy not in ('strict','calendar_gaps'):
            raise ValueError('missing_policy inválida.')
        if type(self.min_training_observations) is not int or self.min_training_observations < 8:
            raise ValueError('min_training_observations requiere entero >= 8.')
        if self.missing_policy == 'calendar_gaps' and (self.synthetic_training_approved or self.independent_holdout):
            raise ValueError('calendar_gaps excluye síntesis y confirmación independiente.')
        for key in ('source_approved','synthetic_training_approved','protocol_approved','independent_holdout','use_rf','use_arima'):
            if not isinstance(getattr(self,key),bool):
                raise ValueError(f'{key} requiere booleano JSON true/false, no texto.')
        duplicate_rows = self.approved_duplicate_rows
        if not isinstance(duplicate_rows, (list, tuple)) or any(
            type(row) is not int or row < 2 for row in duplicate_rows
        ) or len(set(duplicate_rows)) != len(duplicate_rows):
            raise ValueError('approved_duplicate_rows requiere filas Excel unicas, enteras y mayores o iguales a 2.')
        for key in ('window','holdout_weeks','tuning_origins','bootstrap_samples','bootstrap_block','min_inference_weeks','seed'):
            if type(getattr(self,key)) is not int or getattr(self,key)<1:
                raise ValueError(f'{key} requiere entero positivo.')
        if tuple(self.horizons) != (1, 2, 3, 4):
            raise ValueError('Esta versión implementa los cuatro horizontes 1..4.')
        if self.window < 8 or self.holdout_weeks < 4 or self.tuning_origins < 2:
            raise ValueError('Ventana o partición insuficiente.')
        if not 0 < self.threshold <= 1 or any(not 0 < w < 1 for w in self.weights):
            raise ValueError('Umbral/pesos inválidos; un híbrido requiere dos componentes.')
        if not self.weights or not self.alphas or any(not 0 < a <= 1 for a in self.alphas):
            raise ValueError('Pesos y parámetros de composición obligatorios.')
        if min(self.lags) < 1 or min(self.rolling) < 2:
            raise ValueError('Rezagos y ventanas deben ser positivos.')
        if self.bootstrap_samples < 100 or self.bootstrap_block < 1:
            raise ValueError('Configuración de remuestreo insuficiente.')
        return self

    @property
    def lookback(self):
        if self.missing_policy == 'calendar_gaps': return 4
        return max(*self.lags, *self.rolling)

    def dictionary(self):
        return asdict(self)


def load_config(path):
    values = json.loads(Path(path).read_text(encoding='utf-8'))
    unknown = set(values) - {f.name for f in fields(Config)}
    if unknown:
        raise ValueError(f'Claves desconocidas: {sorted(unknown)}')
    return Config(**values).validate()
