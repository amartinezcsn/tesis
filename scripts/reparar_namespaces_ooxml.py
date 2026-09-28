from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile


NAMESPACES = {
    "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
    "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
    "w16se": "http://schemas.microsoft.com/office/word/2015/wordml/symex",
    "w16cid": "http://schemas.microsoft.com/office/word/2016/wordml/cid",
    "w16": "http://schemas.microsoft.com/office/word/2018/wordml",
    "w16cex": "http://schemas.microsoft.com/office/word/2018/wordml/cex",
    "w16sdtdh": "http://schemas.microsoft.com/office/word/2020/wordml/sdtdatahash",
    "w16sdtfl": "http://schemas.microsoft.com/office/word/2024/wordml/sdtformatlock",
    "w16du": "http://schemas.microsoft.com/office/word/2023/wordml/word16du",
    "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
}


def patch_xml(payload: bytes) -> tuple[bytes, int]:
    text = payload.decode("utf-8")
    ignorable = re.search(r'(?:\w+:)?Ignorable="([^"]+)"', text)
    if not ignorable:
        return payload, 0
    prefixes = ignorable.group(1).split()
    missing = [p for p in prefixes if p in NAMESPACES and not re.search(rf'xmlns:{re.escape(p)}=', text[: text.find(">") + 1])]
    if not missing:
        return payload, 0
    root = re.search(r"<([A-Za-z_][\w.-]*:)?[A-Za-z_][\w.-]*\b", text)
    if root is None:
        raise RuntimeError("No se localizó el elemento raíz")
    declarations = "".join(f' xmlns:{p}="{NAMESPACES[p]}"' for p in missing)
    insert_at = root.end()
    text = text[:insert_at] + declarations + text[insert_at:]
    return text.encode("utf-8"), len(missing)


def repair(path: Path) -> None:
    patched = 0
    with NamedTemporaryFile(delete=False, suffix=".docx", dir=path.parent) as handle:
        tmp = Path(handle.name)
    try:
        with ZipFile(path, "r") as source, ZipFile(tmp, "w", ZIP_DEFLATED) as target:
            for info in source.infolist():
                payload = source.read(info.filename)
                if info.filename.endswith((".xml", ".rels")):
                    payload, count = patch_xml(payload)
                    patched += count
                target.writestr(info, payload)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()
    print(f"repaired={path} declarations={patched}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Uso: reparar_namespaces_ooxml.py archivo.docx [archivo2.docx ...]")
    for arg in sys.argv[1:]:
        repair(Path(arg))
