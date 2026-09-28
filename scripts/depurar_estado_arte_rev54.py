from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile

from lxml import etree


SOURCE = Path("documentacion/TESIS_AGO2026_Rev53_(ZUJ)_ResumenAbstract.docx")
OUTPUT = Path("documentacion/TESIS_AGO2026_Rev54_(ZUJ)_EstadoArteDepurado.docx")

HEADING = "Agregación temporal y horizonte de planeación"
BODY_START = "La elección del horizonte debe responder a la frecuencia efectiva de decisión."


def main() -> None:
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

    with ZipFile(SOURCE, "r") as source_zip:
        document_xml = source_zip.read("word/document.xml")
        root = etree.fromstring(document_xml)
        removed = {"heading": 0, "body": 0}

        for paragraph in root.xpath(".//w:p", namespaces=namespace):
            text = "".join(paragraph.xpath(".//w:t/text()", namespaces=namespace)).strip()
            kind = None
            if text == HEADING:
                kind = "heading"
            elif text.startswith(BODY_START):
                kind = "body"
            if kind is not None:
                paragraph.getparent().remove(paragraph)
                removed[kind] += 1

        if removed != {"heading": 1, "body": 1}:
            raise RuntimeError(f"Coincidencias inesperadas: {removed}")

        patched_xml = etree.tostring(
            root,
            xml_declaration=True,
            encoding="UTF-8",
            standalone=True,
        )

        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=OUTPUT.parent, suffix=".docx", delete=False) as handle:
            temporary = Path(handle.name)

        try:
            with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as output_zip:
                for item in source_zip.infolist():
                    data = patched_xml if item.filename == "word/document.xml" else source_zip.read(item.filename)
                    output_zip.writestr(item, data)
            temporary.replace(OUTPUT)
        finally:
            if temporary.exists():
                temporary.unlink()

    print(OUTPUT.resolve())


if __name__ == "__main__":
    main()
