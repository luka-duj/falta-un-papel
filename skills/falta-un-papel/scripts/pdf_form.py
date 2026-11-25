"""Inspect or fill a local municipal PDF. No network, execution of PDF actions, or submission."""

import argparse
from dataclasses import dataclass, field
from getpass import GetPassWarning, getpass
from hashlib import sha256
from io import BytesIO
import json
import logging
import math
import os
from pathlib import Path
import re
import sys
import unicodedata
import warnings

from PIL import ImageChops
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ContentStream, FloatObject, NameObject, NullObject, TextStringObject
from pypdfium2 import PdfDocument
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen.canvas import Canvas

PROFILES = Path(__file__).resolve().parents[1] / "references" / "profiles"
SAMPLE_MARK = "EJEMPLO FICTICIO - NO PRESENTAR"
PAGE_LIMIT = 30
FILE_LIMIT = 25 * 1024 * 1024
PROTECTED = re.compile(r"firm[ae]|\b(?:registro|expediente|sello|funcionario)\b|uso interno|reservad[oa]|administracion")
FONT_SIZE = re.compile(r"(/[^\s/]+\s+)[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?=\s+Tf\b)")


class FormError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


@dataclass
class Widget:
    page: int
    rect: tuple[float, float, float, float]
    obj: object
    states: tuple[str, ...] = ()


@dataclass
class FormField:
    identifier: str
    label: str
    kind: str
    required: bool
    multiline: bool = False
    options: list[dict[str, str]] = field(default_factory=list)
    widgets: list[Widget] = field(default_factory=list)
    max_length: int = 0
    label_source: str = "id"
    line_step: float | None = None

    def public(self):
        return {
            "id": self.identifier, "label": self.label, "label_source": self.label_source, "kind": self.kind,
            "required": self.required, "multiline": self.multiline, "options": self.options,
            "positions": [{"page": w.page, "rect": w.rect} for w in self.widgets],
        }


def ancestors(obj):
    seen = set()
    while obj is not None and id(obj) not in seen:
        seen.add(id(obj))
        yield obj
        ref = obj.get("/Parent")
        obj = ref.get_object() if ref is not None else None


def inherited(obj, key, default=None):
    return next((node[key] for node in ancestors(obj) if key in node), default)


def qualified_name(obj):
    return ".".join(str(node["/T"]) for node in reversed(list(ancestors(obj))) if "/T" in node)


def safe_label(text):
    return "".join(c for c in str(text) if c.isprintable()).strip()[:200]


def reserved(text):
    plain = unicodedata.normalize("NFKD", str(text).casefold())
    return bool(PROTECTED.search("".join(c for c in plain if not unicodedata.combining(c))))


def rect_tuple(rect):
    if rect is None or len(rect) != 4:
        raise FormError("invalid_geometry", "El campo tiene una posición ilegible.")
    x0, y0, x1, y1 = (float(n) for n in rect)
    if not all(math.isfinite(n) for n in (x0, y0, x1, y1)) or x0 >= x1 or y0 >= y1:
        raise FormError("invalid_geometry", "El campo tiene una posición ilegible.")
    return x0, y0, x1, y1


def annotations(page):
    # pypdf may store the Annots array itself as an indirect object.
    return (page["/Annots"] if "/Annots" in page else ())


def button_states(widget):
    appearance = widget.get("/AP")
    normal = appearance.get_object().get("/N") if appearance else None
    state_map = normal.get_object() if normal is not None else {}
    return tuple(str(key) for key in state_map if key != "/Off" and str(key).startswith("/"))


def acro_fields(reader, profile):
    values = reader.get_fields() or {}
    if any(f.get("/FT") == "/Sig" and not isinstance(f.get("/V"), (type(None), NullObject)) for f in values.values()):
        raise FormError("signed_pdf", "Usa el impreso en blanco. El PDF facilitado contiene una firma.")
    widgets_by_name = {}
    for index, page in enumerate(reader.pages, 1):
        for ref in annotations(page):
            widget = ref.get_object()
            if widget.get("/Subtype") != "/Widget":
                continue
            name = qualified_name(widget)
            if not name:
                continue
            canonical = next((part for part in ancestors(widget) if "/T" in part), None)
            reference = getattr(canonical, "indirect_reference", None)
            flags = int(widget.get("/F", 0))
            rect = rect_tuple(widget.get("/Rect"))
            states = button_states(widget) if inherited(widget, "/FT") == "/Btn" else ()
            widgets_by_name.setdefault(name, []).append((Widget(index, rect, widget, states), reference, flags))

    allowed = profile.get("fields") if profile else None
    results = {}
    for name, entry in values.items():
        if allowed is not None and name not in allowed:
            continue
        kind = entry.get("/FT")
        candidates = widgets_by_name.get(name, [])
        flag_bits = int(inherited(entry, "/Ff", 0))
        tooltip = inherited(entry, "/TU")
        label = safe_label(allowed[name]["label"] if allowed is not None else tooltip or name)
        label_source = "profile" if allowed is not None else "tooltip" if tooltip else "id"
        refs = {getattr(ref, "idnum", None) for _, ref, _ in candidates}
        if (kind not in {"/Tx", "/Btn", "/Ch"} or flag_bits & 1 or reserved(f"{name} {label}")
                or len(refs) != 1 or None in refs
                or any(flags & (1 | 2 | 32) for _, _, flags in candidates)):
            continue
        widgets = [widget for widget, _, _ in candidates]
        display_type = "text"
        options = []
        if kind == "/Btn":
            states = sorted({state for widget in widgets for state in widget.states})
            if flag_bits & (1 << 16) or not states:
                continue
            display_type = "radio" if flag_bits & (1 << 15) else "checkbox"
            if display_type == "checkbox" and len(states) != 1:
                continue
            options = [{"value": state, "label": state.lstrip("/")} for state in (*states, "/Off")]
        if kind == "/Ch":
            if flag_bits & (1 << 21):
                continue
            display_type = "choice"
            for option in inherited(entry, "/Opt", []):
                export, display = option if isinstance(option, list) and len(option) == 2 else (option, option)
                options.append({"value": str(export), "label": safe_label(display)})
            if not options:
                continue
        required = allowed[name].get("required", False) if allowed is not None else bool(flag_bits & 2)
        results[name] = FormField(
            name, label, display_type, required,
            multiline=kind == "/Tx" and bool(flag_bits & 4096),
            options=options, widgets=widgets, max_length=int(inherited(entry, "/MaxLen", 0)), label_source=label_source,
            line_step=allowed[name].get("line_step") if allowed is not None else None,
        )
    return results


def flat_fields(reader, profile):
    fields = {}
    for identifier, item in profile.get("fields", {}).items():
        if reserved(f"{identifier} {item['label']}") or item["kind"] not in {"text", "checkbox"}:
            raise FormError("invalid_profile", "La ficha contiene un campo fuera de su alcance.")
        index = item["page"]
        if not 1 <= index <= len(reader.pages):
            raise FormError("invalid_profile", "La página indicada en la ficha no existe.")
        page = reader.pages[index - 1]
        box = rect_tuple(item["rect"])
        if (page.rotation or tuple(page.cropbox) != tuple(page.mediabox)
                or tuple(page.mediabox)[:2] != (0, 0)
                or box[0] < 0 or box[1] < 0 or box[2] > page.mediabox.width or box[3] > page.mediabox.height):
            raise FormError("invalid_profile", "La ficha no coincide con la geometría del PDF.")
        for other in fields.values():
            widget = other.widgets[0]
            if (widget.page == index and max(box[0], widget.rect[0]) < min(box[2], widget.rect[2])
                    and max(box[1], widget.rect[1]) < min(box[3], widget.rect[3])):
                raise FormError("invalid_profile", "La ficha contiene campos superpuestos.")
        options = [{"value": option, "label": option} for option in ("sí", "no")] if item["kind"] == "checkbox" else []
        fields[identifier] = FormField(
            identifier, item["label"], item["kind"], item.get("required", False),
            multiline=item.get("multiline", False), options=options, widgets=[Widget(index, box, None)],
            label_source="profile",
        )
    return fields


def get_profiles():
    for filename in sorted(PROFILES.glob("*.json")):
        yield json.loads(filename.read_text(encoding="utf-8"))


def inspect_pdf(raw, profiles=None):
    fingerprint = sha256(raw).hexdigest()
    reader = PdfReader(BytesIO(raw))
    if reader.is_encrypted:
        raise FormError("encrypted_pdf", "Abre o descarga el impreso oficial en blanco sin contraseña.")
    if not 1 <= len(reader.pages) <= PAGE_LIMIT:
        raise FormError("page_limit", "El PDF supera el límite de páginas de este editor.")
    root = reader.root_object
    if root.get("/Perms"):
        raise FormError("restricted_pdf", "Usa el impreso oficial en blanco sin restricciones de edición.")
    acroform = root.get("/AcroForm")
    if acroform and acroform.get_object().get("/XFA") is not None:
        raise FormError("xfa_pdf", "El impreso usa un formato de formulario que requiere su lector oficial.")
    profiles = get_profiles() if profiles is None else profiles
    profile = next((item for item in profiles if item["sha256"] == fingerprint), None)
    fields = acro_fields(reader, profile if profile and profile["kind"] == "acroform" else None)
    kind = "acroform" if acroform and acroform.get_object().get("/Fields") else "unmapped"
    if kind == "unmapped" and profile and profile["kind"] == "flat":
        kind, fields = "flat", flat_fields(reader, profile)
    return reader, fingerprint, kind, fields, profile


def check_value(spec, value):
    if not isinstance(value, str):
        return None
    clean = unicodedata.normalize("NFC", value.strip())
    if not clean or len(clean) > 8000 or len(clean) > (spec.max_length or 8000):
        return None
    if any(not char.isprintable() and (char != "\n" or not spec.multiline) for char in clean):
        return None
    if spec.options and clean not in {choice["value"] for choice in spec.options}:
        return None
    if spec.kind == "text":
        for widget in spec.widgets:
            x0, y0, x1, y1 = widget.rect
            width = x1 - x0 - 4
            if spec.multiline:
                lines = [line for part in clean.split("\n") for line in (simpleSplit(part, "Helvetica", 7, width) or [""])]
                if len(lines) * 9 > y1 - y0 or any(stringWidth(line, "Helvetica", 7) > width for line in lines):
                    return None
            elif stringWidth(clean, "Helvetica", 7) > width:
                return None
    return clean


def clear_actions(writer):
    root = writer.root_object
    for name in ("/OpenAction", "/AA"):
        root.pop(NameObject(name), None)
    names = root.get("/Names")
    if names:
        for name in ("/JavaScript", "/EmbeddedFiles"):
            names.get_object().pop(NameObject(name), None)
    for entry in (writer.get_fields() or {}).values():
        for ref in ancestors(entry):
            ref.pop(NameObject("/AA"), None)
            ref.pop(NameObject("/A"), None)
    for page in writer.pages:
        page.pop(NameObject("/AA"), None)
        for annotation in annotations(page):
            annot = annotation.get_object()
            for node in ancestors(annot):
                node.pop(NameObject("/AA"), None)
                node.pop(NameObject("/A"), None)


def draw_flat(layer, widget, spec, value):
    x0, y0, x1, y1 = widget.rect
    if spec.kind == "checkbox":
        if value == "sí":
            layer.line(x0 + 1, y0 + 1, x1 - 1, y1 - 1)
            layer.line(x0 + 1, y1 - 1, x1 - 1, y0 + 1)
        return True
    try:
        value.encode("cp1252")
    except UnicodeEncodeError:
        return False
    for size in (11, 10, 9, 8, 7):
        lines = [line for part in value.split("\n") for line in simpleSplit(part, "Helvetica", size, x1 - x0 - 4)]
        if (spec.multiline or len(lines) == 1) and len(lines) * (size + 2) <= y1 - y0:
            # simpleSplit can return words wider than the available line.
            if any(stringWidth(line, "Helvetica", size) > x1 - x0 - 4 for line in lines):
                continue
            layer.setFont("Helvetica", size)
            for index, line in enumerate(lines):
                layer.drawString(x0 + 2, y1 - size - 1 - index * (size + 2), line)
            return True
    return False


def add_layers(writer, fields, values, flat, sample):
    failed = set()
    for index, page in enumerate(writer.pages, 1):
        field_ids = [name for name in values if flat and fields[name].widgets[0].page == index]
        if not (field_ids or sample):
            continue
        layer_bytes = BytesIO()
        width, height = float(page.mediabox.width), float(page.mediabox.height)
        layer = Canvas(layer_bytes, pagesize=(width, height))
        for name in field_ids:
            spec = fields[name]
            if not draw_flat(layer, spec.widgets[0], spec, values[name]):
                failed.add(name)
        if sample:
            # Use the standard review margin, and confirm its visibility on every page.
            x = float(page.mediabox.left) + width / 2
            y = float(page.mediabox.top) - 15
            layer.setFillColorRGB(.62, .12, .09)
            layer.setFont("Helvetica-Bold", 9)
            layer.drawCentredString(x, y, SAMPLE_MARK)
        layer.showPage()
        layer.save()
        layer_bytes.seek(0)
        page.merge_page(PdfReader(layer_bytes).pages[0])
    return failed


def valid_appearances(reader, fields, values):
    active = reader.get_fields() or {}
    found = set()
    failed = set()
    for name, value in values.items():
        if active.get(name, {}).get("/V") != value:
            failed.add(name)
    for index, page in enumerate(reader.pages, 1):
        for ref in annotations(page):
            widget = ref.get_object()
            if widget.get("/Subtype") != "/Widget":
                continue
            name = qualified_name(widget)
            if name not in values:
                continue
            found.add((name, index, rect_tuple(widget.get("/Rect"))))
            appearance = widget.get("/AP")
            normal = appearance.get_object().get("/N") if appearance else None
            if normal is None or inherited(widget, "/V") != values[name]:
                failed.add(name)
                continue
            normal = normal.get_object()
            if fields[name].kind in {"checkbox", "radio"}:
                expected = values[name] if values[name] in normal else "/Off"
                if widget.get("/AS") != expected or expected not in normal:
                    failed.add(name)
                    continue
                normal = normal[expected].get_object()
            if not hasattr(normal, "get_data") or not normal.get_data().strip():
                failed.add(name)
    for name in values:
        if any((name, w.page, w.rect) not in found for w in fields[name].widgets):
            failed.add(name)
    return failed


def review_pdf(official, submitted_draft):
    """Compare editable fields without returning their values or changing either PDF."""
    source, _, source_kind, expected, _ = inspect_pdf(official)
    draft, _, draft_kind, actual, _ = inspect_pdf(submitted_draft)
    if source_kind != "acroform" or draft_kind != "acroform" or len(source.pages) != len(draft.pages):
        raise FormError("unmatched_form", "No se pueden comparar estos PDF como formularios editables. Revisa sus etiquetas visibles.")

    stored = draft.get_fields() or {}
    statuses = {}
    values = {}
    for name, field in expected.items():
        candidate = actual.get(name)
        # Compare the field kind and visible anchor on every copy of that field.
        anchors = sorted((widget.page, *widget.rect) for widget in field.widgets)
        seen = sorted((widget.page, *widget.rect) for widget in candidate.widgets) if candidate else []
        if (candidate is None or field.kind != candidate.kind or field.multiline != candidate.multiline
                or field.options != candidate.options or len(anchors) != len(seen)
                or any(page != other_page or any(abs(a - b) > 0.5 for a, b in zip(rect, other_rect))
                       for (page, *rect), (other_page, *other_rect) in zip(anchors, seen))):
            statuses[name] = "unmatched"
            continue
        value = stored[name].get("/V")
        if (isinstance(value, (type(None), NullObject)) or not str(value).strip()
                or (field.kind in {"checkbox", "radio"} and value == "/Off")):
            statuses[name] = "empty"
        else:
            statuses[name] = "present"
            values[name] = value
    if not any(status != "unmatched" for status in statuses.values()):
        raise FormError("unmatched_form", "Los campos editables no coinciden con el impreso oficial facilitado.")
    # The draft positions may differ slightly from the official blank.
    for name in valid_appearances(draft, actual, values):
        statuses[name] = "appearance_unverified"
    return {"fields": [{"id": name, "label": field.label, "required": field.required, "status": statuses[name]}
                       for name, field in expected.items()]}


def invisible_fields(before, after, page, coordinates):
    # PDFium coordinates account for the visible crop box and page rotation.
    before_page = before[page - 1]
    after_page = after[page - 1]
    scale = min(1.5, 1800 / max(after_page.get_size()))
    original = before_page.render(scale=scale)
    revised = after_page.render(scale=scale)
    try:
        diff = ImageChops.difference(original.to_pil().convert("RGB"), revised.to_pil().convert("RGB"))
        converter = revised.get_posconv(after_page)
        for name, (left, bottom, right, top) in coordinates:
            x1, y1 = converter.to_bitmap(left, bottom)
            x2, y2 = converter.to_bitmap(right, top)
            bounds = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
            if diff.crop(bounds).getbbox() is None:
                yield name
    finally:
        original.close()
        revised.close()
        before_page.close()
        after_page.close()


def visible_fields(original, output, fields, values, baseline):
    failures = set()
    by_page = {}
    for name, value in values.items():
        for widget in fields[name].widgets:
            if fields[name].kind in {"checkbox", "radio"} and value in {"/Off", "no"}:
                continue
            if fields[name].kind == "radio" and value not in widget.states:
                continue
            if name in baseline and baseline[name].get("/V") == value:
                continue
            by_page.setdefault(widget.page, []).append((name, widget.rect))
    with PdfDocument(original) as before, PdfDocument(output) as after:
        before.init_forms()
        after.init_forms()
        for page, coordinates in by_page.items():
            failures.update(invisible_fields(before, after, page, coordinates))
    return failures


def align_lined_fields(writer, fields, values):
    rejected = set()
    for page in writer.pages:
        for ref in annotations(page):
            widget = ref.get_object()
            if widget.get("/Subtype") != "/Widget":
                continue
            name = qualified_name(widget)
            if name not in values or not fields[name].line_step:
                continue
            appearance = widget["/AP"]["/N"]
            stream = ContentStream(appearance, writer)
            moves = [operands for operands, operator in stream.operations if operator == b"Td"]
            step = fields[name].line_step
            if not moves or float(moves[0][1]) - step * (len(moves) - 1) < 2:
                rejected.add(name)
                continue
            for move in moves[1:]:
                move[1] = FloatObject(-step)
            appearance.set_data(stream.get_data())
    return rejected


def write_pdf(reader, fields, values, flat, sample=False):
    writer = PdfWriter(clone_from=reader)
    clear_actions(writer)
    rejected = set()
    if not flat:
        # A fixed font size generates a clipped appearance for long Expone
        # fields. Zero enables pypdf's field fitting and multiline wrapping.
        acroform = writer.root_object["/AcroForm"]
        for page in writer.pages:
            for ref in annotations(page):
                widget = ref.get_object()
                if widget.get("/Subtype") != "/Widget":
                    continue
                name = qualified_name(widget)
                if name in values and fields[name].kind == "text":
                    appearance = str(inherited(widget, "/DA", acroform.get("/DA", "/Helv 0 Tf 0 g")))
                    sized, replacements = FONT_SIZE.subn(r"\g<1>0", appearance, count=1)
                    if replacements:
                        widget[NameObject("/DA")] = TextStringObject(sized)
        writer.update_page_form_field_values(None, values, auto_regenerate=False)
        if any(fields[name].line_step for name in values):
            rejected.update(align_lined_fields(writer, fields, values))
    rejected.update(add_layers(writer, fields, values, flat, sample))
    stream = BytesIO()
    writer.write(stream)
    return stream.getvalue(), rejected


def protected_values(reader):
    return {name: str(value.get("/V") or "") for name, value in (reader.get_fields() or {}).items()}


def fill_pdf(original, request, sample=False, profiles=None):
    reader, fingerprint, kind, fields, _ = inspect_pdf(original, profiles)
    if request.get("fingerprint") != fingerprint:
        raise FormError("changed_form", "El PDF ha cambiado. Vuelve a inspeccionar el impreso antes de usar el mapa.")
    if not fields:
        raise FormError("unmapped_form", "La revisión no tiene campos editables verificados.")
    answers = request.get("values")
    extra_required = request.get("required", [])
    if (not isinstance(answers, dict) or not isinstance(extra_required, list)
            or any(not isinstance(name, str) or name not in fields for name in extra_required)):
        raise FormError("invalid_input", "Usa los identificadores de campos devueltos por inspect.")
    unresolved = []
    accepted = {}
    for name, value in answers.items():
        if name not in fields:
            unresolved.append({"id": None, "reason": "unknown_or_protected"})
            continue
        clean = check_value(fields[name], value)
        if clean is None:
            unresolved.append({"id": name, "reason": "invalid_or_too_long"})
        else:
            accepted[name] = clean
    if not accepted:
        raise FormError("empty_draft", "Falta al menos un valor confirmado para preparar una copia útil.")

    flat = kind == "flat"
    baseline = reader.get_fields() or {}
    before_values = protected_values(reader)
    result, rejected = write_pdf(reader, fields, accepted, flat)
    reopened = PdfReader(BytesIO(result))
    if not flat:
        rejected |= valid_appearances(reopened, fields, accepted)
    rejected |= visible_fields(original, result, fields, {k: v for k, v in accepted.items() if k not in rejected}, baseline)
    for name in sorted(rejected):
        unresolved.append({"id": name, "reason": "appearance_unverified"})
        del accepted[name]
    if not accepted:
        raise FormError("verification_failed", "No se pudo comprobar el resultado en pantalla.")

    if rejected or sample:
        result, unexpected = write_pdf(reader, fields, accepted, flat, sample)
        if unexpected:
            raise FormError("verification_failed", "No se pudo reconstruir la copia verificada.")
        reopened = PdfReader(BytesIO(result))
    after_values = protected_values(reopened)
    if (len(reopened.pages) != len(reader.pages)
            or {key: value for key, value in before_values.items() if key not in accepted}
            != {key: value for key, value in after_values.items() if key not in accepted}
            or (not flat and valid_appearances(reopened, fields, accepted))):
        raise FormError("verification_failed", "El borrador no conservó el resto del formulario.")
    if sample:
        with PdfDocument(result) as rendered:
            if any(SAMPLE_MARK not in rendered[index].get_textpage().get_text_range() for index in range(len(rendered))):
                raise FormError("example_mark_failed", "La marca de práctica debe aparecer en todas las páginas.")
    required = set(extra_required) | {name for name, spec in fields.items() if spec.required}
    pending = [{"id": name, "label": fields[name].label} for name in fields
               if name in required and name not in accepted and baseline.get(name, {}).get("/V") in (None, "", "/Off")]
    return result, {"filled": list(accepted), "missing": pending, "unresolved": unresolved}


def private_request(raw, requested):
    if not sys.stdin.isatty():
        raise FormError("private_terminal_required", "Abre una terminal local propia para introducir los datos en privado.")
    reader, fingerprint, _, fields, _ = inspect_pdf(raw)
    selected = set(requested or (name for name, spec in fields.items() if spec.required))
    if not selected or not selected <= fields.keys():
        raise FormError("select_fields", "Selecciona campos comprobados mediante --field después de inspect.")
    previous = reader.get_fields() or {}
    answers = {}
    with warnings.catch_warnings():
        warnings.simplefilter("error", GetPassWarning)
        for name, spec in fields.items():
            if name not in selected or previous.get(name, {}).get("/V") not in (None, "", "/Off"):
                continue
            options = " / ".join(item["value"] for item in spec.options)
            suffix = f" ({options})" if options else ""
            value = getpass(f"{spec.label}{suffix} (Intro para omitir) ")
            if value.strip():
                answers[name] = value
    return {"fingerprint": fingerprint, "values": answers}


def read_pdf(path):
    with path.open("rb") as stream:
        data = stream.read(FILE_LIMIT + 1)
    if len(data) > FILE_LIMIT or not data.startswith(b"%PDF-"):
        raise FormError("invalid_pdf", "Usa un archivo PDF de hasta 25 MiB.")
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inspect").add_argument("source", type=Path)
    review = commands.add_parser("review")
    review.add_argument("source", type=Path, help="Impreso oficial vigente en blanco")
    review.add_argument("draft", type=Path, help="Borrador que quieres comprobar")
    fill = commands.add_parser("fill")
    fill.add_argument("source", type=Path)
    fill.add_argument("output", type=Path)
    mode = fill.add_mutually_exclusive_group()
    mode.add_argument("--private", action="store_true")
    mode.add_argument("--sample", action="store_true")
    fill.add_argument("--field", action="append", help="Identificador comprobado para entrada privada")
    args = parser.parse_args()
    logging.getLogger("pypdf").setLevel(logging.CRITICAL)
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    try:
        raw = read_pdf(args.source)
        if args.command == "inspect":
            reader, fingerprint, kind, fields, profile = inspect_pdf(raw)
            result = {
                "fingerprint": fingerprint, "kind": kind, "pages": len(reader.pages),
                "profile": profile["id"] if profile else None,
                "fields": [spec.public() for spec in fields.values()],
            }
        elif args.command == "review":
            result = review_pdf(raw, read_pdf(args.draft))
        else:
            if args.output.suffix.lower() != ".pdf" or args.output.exists():
                raise FormError("output_exists", "Elige una ruta nueva para el borrador PDF.")
            if args.field and not args.private:
                raise FormError("invalid_input", "Usa --field con --private.")
            request = private_request(raw, args.field) if args.private else json.load(sys.stdin)
            if not isinstance(request, dict):
                raise FormError("invalid_input", "El editor espera un objeto JSON.")
            data, result = fill_pdf(raw, request, args.sample)
            descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data)
            result["draft"] = str(args.output.resolve())
        print(json.dumps({"ok": True, **result}, ensure_ascii=False))
        return 0
    except FormError as exc:
        code, message = exc.code, str(exc)
    except (KeyboardInterrupt, EOFError, GetPassWarning):
        code, message = "interrupted", "La entrada se interrumpió. El borrador queda pendiente."
    except json.JSONDecodeError:
        code, message = "invalid_input", "El editor espera un objeto JSON válido."
    except Exception:
        code, message = "cannot_process", "No se pudo verificar el PDF. Usa el impreso oficial y las respuestas preparadas."
    print(json.dumps({"ok": False, "error": code, "message": message}, ensure_ascii=False))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
