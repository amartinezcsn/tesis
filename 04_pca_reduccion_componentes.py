from __future__ import annotations

"""
Codigo 04: reduccion dimensional por PCA.

Objetivo:
- Transformar muchas variables correlacionadas en componentes principales.
- Mantener una proporcion definida de varianza explicada.
- Generar un dataset alternativo para comparar contra:
  1) dataset completo,
  2) dataset reducido por seleccion de variables.

Nota metodologica:
PCA mejora compacidad numerica, pero reduce interpretabilidad. Por eso se
recomienda usarlo como dataset comparativo, no como unica explicacion de tesis.
"""

import numpy as np
import pandas as pd

from config_metodologia import (
    DATE_COLUMN,
    TARGET_COLUMNS,
    ensure_output_dir,
    load_model_dataset,
    numeric_predictors,
    temporal_split,
)


VARIANCE_TO_KEEP = 0.95


def pca_with_sklearn_or_numpy(train_x: pd.DataFrame, full_x: pd.DataFrame):
    try:
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler

        scaler = StandardScaler()
        train_scaled = scaler.fit_transform(train_x)
        full_scaled = scaler.transform(full_x)

        pca = PCA(n_components=VARIANCE_TO_KEEP, random_state=42)
        train_components = pca.fit_transform(train_scaled)
        full_components = pca.transform(full_scaled)
        explained = pca.explained_variance_ratio_
        loadings = pca.components_.T
        return full_components, explained, loadings

    except ImportError:
        # Alternativa sin scikit-learn usando SVD de numpy.
        mean = train_x.mean(axis=0)
        std = train_x.std(axis=0).replace(0, 1)
        train_scaled = ((train_x - mean) / std).to_numpy(dtype=float)
        full_scaled = ((full_x - mean) / std).to_numpy(dtype=float)

        _, singular_values, vt = np.linalg.svd(train_scaled, full_matrices=False)
        explained = (singular_values**2) / np.sum(singular_values**2)
        n_components = int(np.searchsorted(np.cumsum(explained), VARIANCE_TO_KEEP) + 1)
        components = vt[:n_components]
        full_components = full_scaled @ components.T
        loadings = components.T
        return full_components, explained[:n_components], loadings


def main() -> None:
    out_dir = ensure_output_dir()
    df = load_model_dataset()
    train, _ = temporal_split(df)
    predictors = numeric_predictors(df)

    train_x = train[predictors].replace([np.inf, -np.inf], np.nan).fillna(0)
    full_x = df[predictors].replace([np.inf, -np.inf], np.nan).fillna(0)

    components, explained, loadings = pca_with_sklearn_or_numpy(train_x, full_x)
    component_names = [f"pca_{idx + 1:02d}" for idx in range(components.shape[1])]

    pca_dataset = pd.concat(
        [
            df[[DATE_COLUMN]].reset_index(drop=True),
            pd.DataFrame(components, columns=component_names),
            df[TARGET_COLUMNS].reset_index(drop=True),
        ],
        axis=1,
    )

    variance = pd.DataFrame(
        {
            "componente": component_names,
            "varianza_explicada": explained[: len(component_names)],
            "varianza_acumulada": np.cumsum(explained[: len(component_names)]),
        }
    )

    loadings_df = pd.DataFrame(loadings[:, : len(component_names)], index=predictors, columns=component_names)
    loadings_df = loadings_df.reset_index().rename(columns={"index": "variable"})

    output_xlsx = out_dir / "04_dataset_pca_componentes.xlsx"
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        pca_dataset.to_excel(writer, sheet_name="dataset_pca", index=False)
        variance.to_excel(writer, sheet_name="varianza_explicada", index=False)
        loadings_df.to_excel(writer, sheet_name="cargas_componentes", index=False)

    print(f"Archivo generado: {output_xlsx}")
    print(f"Componentes conservados: {len(component_names)}")


if __name__ == "__main__":
    main()
