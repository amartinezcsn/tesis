"""Entrada única del pipeline de la tesis.

Este archivo no entrena modelos por sí mismo: entrega los argumentos a
``hibrido.cli``. Así, ``audit``, ``demo``, ``run`` y ``forecast`` comparten
exactamente las mismas reglas de ejecución y de salida.
"""


def main(argv=None):
    """Delegar la ejecución a la interfaz de comandos del paquete híbrido."""
    from hibrido.cli import main as hybrid_main

    return hybrid_main(argv)

if __name__ == '__main__':
    raise SystemExit(main())
