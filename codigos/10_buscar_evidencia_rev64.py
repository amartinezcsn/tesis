from pathlib import Path
import re


ROOT = Path(r"C:\Python\tesis\tmp\inventario_rev64")
SOURCES = {
    "REV62": ROOT / "TESIS_SEP2026_Rev62_(ZUJ)_Final_text.txt",
    "REV63": ROOT / "TESIS_OCT2026_Rev63_(ZUJ)_Revision_Comite_text.txt",
}
GROUPS = {
    "estructura": [r"cap[ií]tulo", r"[ií]ndice de figuras", r"[ií]ndice de im[aá]genes", r"agradecimientos"],
    "pregunta_objetivo": [r"pregunta de investigaci[oó]n", r"determinar la precisi[oó]n", r"registros disponibles", r"5 de diciembre"],
    "modelo_configuracion": [r"hiperpar[aá]metr", r"configuraci[oó]n", r"selecci[oó]n.*horizonte", r"modelo h[ií]brido"],
    "entrenamiento_validacion": [r"entrenamiento", r"ventana.*52", r"rolling", r"or[ií]genes", r"fuera de muestra"],
    "aportacion": [r"aportaci[oó]n", r"contribuci[oó]n", r"original"],
    "h1_signo": [r"H1", r"1[,.]39", r"signo negativo", r"favorece.*hist[oó]ric", r"no.*confirm"],
    "sensibilidad": [r"sensibilidad", r"imputad", r"sin par[aá]metros de imputaci[oó]n"],
    "categorias": [r"RESTO_ELEGIBLE", r"15 categor", r"11 insumos", r"elegibles"],
    "inferencia": [r"nivel de confianza", r"comparaciones m[uú]ltiples", r"m[ií]nimo inferencial", r"intervalos"],
    "etica": [r"consideraciones [eé]ticas", r"anonimiz", r"confidencial", r"autorizaci[oó]n"],
}


for label, path in SOURCES.items():
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"\n===== {label} =====")
    for group, patterns in GROUPS.items():
        hits = []
        for i, line in enumerate(lines):
            if any(re.search(pattern, line, flags=re.IGNORECASE) for pattern in patterns):
                hits.append((i + 1, line))
        print(f"\n[{group}] {len(hits)} coincidencias")
        for number, text in hits[:18]:
            safe = text.encode("cp1252", "replace").decode("cp1252")
            print(f"{number}: {safe[:700]}")
