    # Ingeniería de Características

    ## Salida generada
    - Archivo: `dataset_modelado_diario.xlsx`
    - Filas: 1584
    - Columnas: 276
    - Rango: 2022-01-29 a 2026-05-31

    ## Objetivos
    - `target_ventas_importe_real_2026_05`
    - `target_compras_total_real_2026_05`

    ## Estrategia de modelado
    - Variables de calendario y estacionalidad
    - Codificación cíclica de mes, día de semana y día del año
    - Proximidad a festivos y fechas de pago
    - Rezagos de 1, 2, 3, 7, 14 y 28 días
    - Ventanas móviles de 7, 14 y 28 días
    - Rezagos por categorías de ventas y compras
    - Variables de estabilidad y tendencia

    ## Nota metodológica
    - Se eliminaron los primeros 28 días para garantizar que los rezagos y ventanas móviles estuvieran completos.