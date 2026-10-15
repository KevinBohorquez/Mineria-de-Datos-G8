"""Comprueba los cálculos y rechazos de T18 con datos sintéticos temporales."""

import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "bench" / "graficar_openmp.py"
FIELDS = ["modelo", "hilos", "repeticion", "tiempo_s", "n", "semilla", "cpu",
          "nucleos_fisicos", "afinidad", "schedule", "commit", "calentamiento"]


def samples(model, threads, seconds):
    return [dict(modelo=model, hilos=threads, repeticion=index, tiempo_s=value,
                 n=1000, semilla=42, cpu="CPU de prueba", nucleos_fisicos=8,
                 afinidad="compact", schedule="none" if model == "secuencial" else "static",
                 commit="prueba", calentamiento=int(index == 0))
            for index, value in enumerate([seconds[0], *seconds], 0)]


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


class GraficarOpenMPTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT / "_build"
        scratch.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.serial = self.root / "serial.csv"
        self.parallel = self.root / "parallel.csv"
        self.output = self.root / "output"
        self.serial_rows = samples("secuencial", 1, [10.0] * 5)
        self.parallel_rows = []
        for threads, seconds in ((2, [4, 5, 6, 5, 5]), (4, [2.5] * 5),
                                 (8, [1.5] * 5), (16, [1.2] * 5)):
            self.parallel_rows.extend(samples("openmp", threads, seconds))

    def run_generator(self):
        write_csv(self.serial, self.serial_rows)
        write_csv(self.parallel, self.parallel_rows)
        return subprocess.run([sys.executable, str(SCRIPT), "--secuencial", str(self.serial),
                               "--openmp", str(self.parallel), "--salida", str(self.output)],
                              capture_output=True, text=True, check=False)

    def test_agrega_y_grafica_cinco_repeticiones(self):
        run = self.run_generator()
        self.assertEqual(run.returncode, 0, run.stderr)
        with (self.output / "processed" / "openmp_resumen.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 5)
        p2 = next(row for row in rows if row["hilos"] == "2")
        self.assertAlmostEqual(float(p2["tiempo_medio_s"]), 5.0)
        self.assertAlmostEqual(float(p2["speedup"]), 2.0)
        self.assertAlmostEqual(float(p2["eficiencia"]), 1.0)
        self.assertGreater(float(p2["desviacion_estandar_s"]), 0)
        p16 = next(row for row in rows if row["hilos"] == "16")
        self.assertEqual(p16["sobresuscrito"], "1")
        for name in ("openmp_tiempo.svg", "openmp_speedup.svg", "openmp_eficiencia.svg"):
            self.assertEqual(ElementTree.parse(self.output / "figures" / name).getroot().tag,
                             "{http://www.w3.org/2000/svg}svg")

    def test_rechaza_repeticion_faltante(self):
        self.parallel_rows = [row for row in self.parallel_rows
                              if not (row["hilos"] == 4 and row["repeticion"] == 5)]
        run = self.run_generator()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("cinco repeticiones", run.stderr)

    def test_rechaza_carga_distinta(self):
        self.parallel_rows[0]["semilla"] = 99
        run = self.run_generator()
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("deben coincidir", run.stderr)


if __name__ == "__main__":
    unittest.main()
