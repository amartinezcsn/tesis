# Experimentos no incorporados al pipeline

Esta carpeta contiene pruebas de modelos candidatos. No modifica la selección,
el entrenamiento ni los artefactos del pipeline híbrido de la tesis.

## Prophet y LSTM

La comparación reutiliza el panel, las particiones y las fechas de una corrida
oficial terminada. Los resultados se escriben en una carpeta nueva bajo
`output/experimental_prophet_lstm_*`.

```powershell
codigos/.venv/Scripts/python.exe codigos/experimentos/evaluar_prophet_lstm.py `
  --baseline-dir output/run_20260924T195600Z_86a6f5
```

Prophet y TensorFlow son dependencias exclusivamente experimentales y no se
añaden a `requirements_hibrido.txt` hasta que se decida incorporarlos.
