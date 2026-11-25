import importlib.util
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DictionaryObject, NameObject
from reportlab.pdfgen.canvas import Canvas


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/falta-un-papel/scripts/pdf_form.py"
SPEC = importlib.util.spec_from_file_location("pdf_form", SCRIPT)
PDF = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PDF
SPEC.loader.exec_module(PDF)


def editable():
    result = BytesIO()
    canvas = Canvas(result)
    canvas.drawString(50, 812, "Formulario ficticio de uso de sala")
    canvas.acroForm.textfield(name="solicitante", tooltip="Nombre", x=50, y=710, fieldFlags="required")
    canvas.acroForm.textfield(name="direccion", tooltip="Dirección", x=50, y=665, fieldFlags="required")
    canvas.acroForm.textfield(name="sello", tooltip="Reservado al Registro", x=350, y=710)
    canvas.acroForm.textfield(name="firma", tooltip="Firma", x=350, y=665)
    canvas.acroForm.checkbox(name="asistencia", x=50, y=610, fieldFlags="")
    canvas.acroForm.textfield(name="expone", tooltip="Expone", x=50, y=490, width=160, height=100,
                              fontSize=12, fieldFlags="multiline")
    canvas.showPage()
    canvas.drawString(50, 710, "Instrucciones del impreso de prueba")
    canvas.showPage()
    canvas.save()
    return result.getvalue()


def flat():
    result = BytesIO()
    canvas = Canvas(result)
    canvas.drawString(50, 730, "Nombre")
    canvas.rect(50, 692, 240, 24)
    canvas.showPage()
    canvas.save()
    return result.getvalue()


class EditorTests(unittest.TestCase):
    def test_generic_inspection_reports_fields_and_hides_reserved_ones(self):
        raw = editable()
        _, digest, kind, fields, profile = PDF.inspect_pdf(raw)
        self.assertEqual((digest, kind, profile), (sha256(raw).hexdigest(), "acroform", None))
        self.assertEqual(set(fields), {"solicitante", "direccion", "asistencia", "expone"})
        field = fields["solicitante"].public()
        self.assertEqual((field["label"], field["label_source"]), ("Nombre", "tooltip"))
        self.assertTrue(field["required"])
        self.assertEqual(field["positions"][0]["page"], 1)
        self.assertIn("/Yes", [option["value"] for option in fields["asistencia"].options])

    def test_partial_draft_verifies_values_widgets_and_both_page_labels(self):
        raw = editable()
        output, info = PDF.fill_pdf(raw, {
            "fingerprint": sha256(raw).hexdigest(),
            "values": {"solicitante": "Inés Ficticia", "asistencia": "/Yes", "firma": "rechazada"},
        }, sample=True)
        self.assertEqual(info["filled"], ["solicitante", "asistencia"])
        self.assertEqual(info["missing"], [{"id": "direccion", "label": "Dirección"}])
        self.assertEqual(info["unresolved"], [{"id": None, "reason": "unknown_or_protected"}])
        reader = PdfReader(BytesIO(output))
        fields = reader.get_fields()
        self.assertEqual(fields["solicitante"]["/V"], "Inés Ficticia")
        self.assertEqual(fields["asistencia"]["/V"], "/Yes")
        self.assertEqual(fields["firma"]["/V"], "")
        self.assertEqual(fields["sello"]["/V"], "")
        self.assertTrue(all(PDF.SAMPLE_MARK in page.extract_text() for page in reader.pages))
        self.assertTrue(PdfReader(BytesIO(raw)).get_fields()["solicitante"]["/V"] == "")

    def test_existing_confirmed_values_survive_follow_up(self):
        raw = editable()
        first, _ = PDF.fill_pdf(raw, {"fingerprint": sha256(raw).hexdigest(), "values": {"solicitante": "Inés"}})
        second, state = PDF.fill_pdf(first, {
            "fingerprint": sha256(first).hexdigest(), "values": {"direccion": "Vía de Ejemplo"},
        })
        self.assertEqual(state["missing"], [])
        self.assertEqual(PdfReader(BytesIO(second)).get_fields()["solicitante"]["/V"], "Inés")

    def test_fixed_size_multiline_wraps_without_clipping(self):
        raw = editable()
        value = "Solicito información acerca de la disponibilidad de una sala para una reunión vecinal."
        output, _ = PDF.fill_pdf(raw, {"fingerprint": sha256(raw).hexdigest(), "values": {"expone": value}})
        reader = PdfReader(BytesIO(output))
        annotation = next(ref.get_object() for ref in reader.pages[0].annotations
                          if ref.get_object().get("/T") == "expone")
        self.assertEqual(reader.get_fields()["expone"]["/V"], value)
        self.assertGreater(annotation["/AP"]["/N"].get_data().count(b" Tj"), 1)

    def test_revision_mismatch_stops_before_output(self):
        raw = editable()
        with self.assertRaisesRegex(PDF.FormError, "ha cambiado"):
            PDF.fill_pdf(raw, {"fingerprint": "0" * 64, "values": {"solicitante": "Ignorado"}})

    def test_reviewed_flat_map_and_unknown_flat_fallback(self):
        raw = flat()
        digest = sha256(raw).hexdigest()
        self.assertEqual(PDF.inspect_pdf(raw, [])[2], "unmapped")
        profile = {
            "id": "es-municipio-ficticio", "sha256": digest, "kind": "flat",
            "fields": {"solicitante": {"label": "Nombre", "kind": "text", "page": 1, "rect": [50, 692, 290, 716]}},
        }
        data, result = PDF.fill_pdf(raw, {
            "fingerprint": digest, "values": {"solicitante": "Nombre de ejemplo"},
        }, profiles=[profile])
        self.assertIn("Nombre de ejemplo", PdfReader(BytesIO(data)).pages[0].extract_text())
        self.assertEqual(result["filled"], ["solicitante"])

    def test_active_form_actions_removed(self):
        writer = PdfWriter(clone_from=PdfReader(BytesIO(editable())))
        writer.root_object[NameObject("/OpenAction")] = DictionaryObject({NameObject("/S"): NameObject("/Named")})
        writer.pages[0].annotations[0].get_object()[NameObject("/AA")] = DictionaryObject()
        source = BytesIO()
        writer.write(source)
        raw = source.getvalue()
        output, _ = PDF.fill_pdf(raw, {
            "fingerprint": sha256(raw).hexdigest(), "values": {"solicitante": "Solo un ejemplo"},
        })
        draft = PdfReader(BytesIO(output))
        self.assertNotIn("/OpenAction", draft.root_object)
        self.assertNotIn("/AA", draft.pages[0].annotations[0].get_object())

    def test_cli_leaves_existing_file_intact_and_returns_no_values(self):
        with TemporaryDirectory() as temp:
            source = Path(temp) / "original.pdf"
            destination = Path(temp) / "borrador.pdf"
            raw = editable()
            source.write_bytes(raw)
            request = json.dumps({"fingerprint": sha256(raw).hexdigest(), "values": {"solicitante": "Ficticia Secreta"}})
            argv = [sys.executable, "-B", str(SCRIPT), "fill", str(source), str(destination)]
            run = subprocess.run(argv, capture_output=True, input=request.encode("utf-8"), check=True)
            self.assertNotIn(b"Ficticia Secreta", run.stdout)
            self.assertEqual(json.loads(run.stdout)["filled"], ["solicitante"])
            before = destination.read_bytes()
            duplicate = subprocess.run(argv, capture_output=True, input=request.encode("utf-8"))
            self.assertEqual(json.loads(duplicate.stdout)["error"], "output_exists")
            self.assertEqual(destination.read_bytes(), before)
            self.assertEqual(source.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
