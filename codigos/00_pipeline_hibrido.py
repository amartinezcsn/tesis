"""00: entrada operativa del pipeline híbrido Rev44."""


def main(argv=None):
    from hibrido.cli import main as hybrid_main

    return hybrid_main(argv)

if __name__ == '__main__':
    raise SystemExit(main())
