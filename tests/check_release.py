"""Audit the release allowlist and optionally write its exact contents to a ZIP."""

import argparse
from pathlib import Path
import re
import struct
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
import zlib

ROOT = Path(__file__).resolve().parents[1]
FILES = frozenset({
    ".agents/plugins/marketplace.json", ".claude-plugin/marketplace.json", ".claude-plugin/plugin.json", ".gitignore",
    ".github/ISSUE_TEMPLATE/config.yml", ".github/ISSUE_TEMPLATE/error.yml", ".github/ISSUE_TEMPLATE/mejora.yml",
    "AVISOS.md", "CONTRIBUTING.md", "LICENSE", "PRIVACIDAD.md", "README.md", "SECURITY.md", "plugin.json",
    "skills/falta-un-papel/SKILL.md",
    "skills/falta-un-papel/references/editor-pdf.md",
    "skills/falta-un-papel/references/fuentes-y-datos.md",
    "skills/falta-un-papel/references/profiles/valdemoro-instancia-general.json",
    "skills/falta-un-papel/scripts/pdf_form.py",
    "skills/falta-un-papel/scripts/requirements.txt",
    "skills/revisar-solicitud/SKILL.md",
    "skills/revisar-solicitud/agents/openai.yaml",
    "tests/verification.md", "tests/check_release.py", "tests/test_pdf_form.py",
})
ARTWORK = frozenset({"assets/flujo.png", "assets/icon.png"})

CHECKS = {
    "ruta local": re.compile(r"""(?i)(?:\b[a-z]:[\\/](?:users|stuff|projects)[\\/]|/(?:home|users|mnt/data)/[^/\s]+/)"""),
    "referencia interna": re.compile(r"(?i)(?:thread://|file://|codex://|work-os/feedback)"),
    "credencial potencial": re.compile(r"(?i)\b(?:gh[pousr]_[a-z0-9]{25,}|github_pat_[a-z0-9_]{25,}|sk-[a-z0-9_-]{25,}|AKIA[A-Z0-9]{16})\b"),
}


def clean_png(raw):
    """Require an ordinary PNG with image data and no ancillary metadata."""
    if not raw.startswith(b"\x89PNG\r\n\x1a\n") or len(raw) > 2_000_000:
        return False
    cursor = 8
    chunks = []
    while cursor + 12 <= len(raw):
        length, chunk = struct.unpack_from(">I4s", raw, cursor)
        end = cursor + 12 + length
        if end > len(raw) or chunk not in {b"IHDR", b"IDAT", b"IEND"}:
            return False
        stored_crc, = struct.unpack_from(">I", raw, end - 4)
        if zlib.crc32(raw[cursor + 4:end - 4]) != stored_crc:
            return False
        chunks.append(chunk)
        if chunk == b"IEND":
            return (end == len(raw) and length == 0 and chunks[0] == b"IHDR"
                    and all(item == b"IDAT" for item in chunks[1:-1]) and len(chunks) >= 3)
        cursor = end
    return False


def audit(root, terms=()):
    actual = set()
    data = {}
    warnings = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if relative.parts[0] == ".git":
            continue
        name = relative.as_posix()
        if path.is_symlink():
            warnings.append(f"{name} — enlace simbólico")
        if path.is_file():
            actual.add(name)
    allowed = FILES | ARTWORK
    warnings.extend(f"{name} — archivo ausente" for name in sorted(allowed - actual))
    warnings.extend(f"{name} — archivo fuera de la lista" for name in sorted(actual - allowed))
    for name in sorted(allowed & actual):
        path = root / name
        if not path.resolve().is_relative_to(root) or path.is_symlink():
            warnings.append(f"{name} — ruta fuera del árbol")
            continue
        try:
            raw = path.read_bytes()
            if name in ARTWORK:
                if not clean_png(raw):
                    warnings.append(f"{name} — PNG con metadatos o estructura inesperada")
                data[name] = raw
                continue
            text = raw.decode("utf-8")
            if any(ord(char) < 32 and char not in "\t\r\n" for char in text):
                raise UnicodeError
        except (OSError, UnicodeError):
            warnings.append(f"{name} — no es texto UTF-8 comprobable")
            continue
        if name != "tests/check_release.py":
            warnings.extend(f"{name} — {kind}" for kind, pattern in CHECKS.items() if pattern.search(text))
        folded = (name + "\n" + text).casefold()
        if any(term.casefold() in folded for term in terms if term):
            warnings.append(f"{name} — término privado")
        data[name] = raw
    return warnings, data


def create_archive(path, data):
    with ZipFile(path, "x", compression=ZIP_DEFLATED) as archive:
        for name, content in sorted(data.items()):
            info = ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content, compress_type=ZIP_DEFLATED)
    with ZipFile(path) as archive:
        if archive.namelist() != sorted(data) or any(archive.read(name) != data[name] for name in data):
            raise RuntimeError("El ZIP difiere del árbol comprobado.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--deny-file", type=Path, help="Lista privada de términos, uno por línea")
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    terms = [line.strip() for line in args.deny_file.read_text(encoding="utf-8").splitlines()] if args.deny_file else []
    warnings, data = audit(ROOT, terms)
    if warnings:
        print("\n".join(warnings))
        return 1
    if args.archive:
        if args.archive.resolve().is_relative_to(ROOT):
            parser.error("Elige un destino para el ZIP fuera del árbol.")
        create_archive(args.archive, data)
    print(f"{len(data)} archivos verificados, {len(ARTWORK)} de ellos imágenes PNG sin metadatos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
