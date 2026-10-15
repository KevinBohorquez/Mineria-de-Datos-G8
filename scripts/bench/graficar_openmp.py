"""T18: agrega mediciones T14/T16 y genera tres figuras SVG sin datos inventados."""

from __future__ import annotations

import argparse
from collections import defaultdict
import csv
import hashlib
from html import escape
import math
from pathlib import Path
import statistics
import sys


COLUMNS = {"modelo", "hilos", "repeticion", "tiempo_s", "n", "semilla", "cpu",
           "nucleos_fisicos", "afinidad", "schedule", "commit", "calentamiento"}
THREADS = (2, 4, 8, 16)
COLORS = ("#2448B5", "#7027B0", "#D68A00", "#00847B", "#B63E55")


def read_csv(path: Path, model: str) -> list[dict[str, object]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = COLUMNS - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path}: faltan columnas {', '.join(sorted(missing))}")
        rows = []
        for line, source in enumerate(reader, 2):
            row = {key: (source[key] or "").strip() for key in COLUMNS}
            if row["modelo"].lower() != model:
                raise ValueError(f"{path}:{line}: modelo debe ser {model}")
            if not all(row[key] for key in ("semilla", "cpu", "afinidad", "schedule", "commit")):
                raise ValueError(f"{path}:{line}: faltan metadatos de ejecución")
            try:
                row["hilos"] = int(row["hilos"])
                row["repeticion"] = int(row["repeticion"])
                row["n"] = int(row["n"])
                row["nucleos_fisicos"] = int(row["nucleos_fisicos"])
                row["tiempo_s"] = float(row["tiempo_s"])
            except ValueError as exc:
                raise ValueError(f"{path}:{line}: número inválido") from exc
            if row["n"] <= 0 or row["nucleos_fisicos"] <= 0 or not math.isfinite(row["tiempo_s"]) or row["tiempo_s"] <= 0:
                raise ValueError(f"{path}:{line}: N, núcleos y tiempo deben ser positivos")
            if (model == "secuencial" and row["hilos"] != 1) or (model == "openmp" and row["hilos"] not in THREADS):
                raise ValueError(f"{path}:{line}: número de hilos fuera del barrido")
            flag = row["calentamiento"].lower()
            if flag not in {"0", "1", "si", "sí", "no", "true", "false"}:
                raise ValueError(f"{path}:{line}: calentamiento debe ser 0 o 1")
            row["calentamiento"] = flag in {"1", "si", "sí", "true"}
            if row["calentamiento"] != (row["repeticion"] == 0):
                raise ValueError(f"{path}:{line}: repeticion=0 corresponde al calentamiento")
            rows.append(row)
    if not rows:
        raise ValueError(f"{path}: CSV sin mediciones")
    return rows


def summarize(serial: list[dict[str, object]], parallel: list[dict[str, object]]) -> list[dict[str, object]]:
    all_rows = serial + parallel
    identity = ("n", "semilla", "cpu", "nucleos_fisicos", "commit")
    if any(tuple(row[key] for key in identity) != tuple(serial[0][key] for key in identity) for row in all_rows):
        raise ValueError("N, semilla, CPU, núcleos físicos y commit deben coincidir en T14 y T16")
    groups: dict[tuple[str, str, int], list[dict[str, object]]] = defaultdict(list)
    for row in all_rows:
        groups[(str(row["schedule"]), str(row["afinidad"]), int(row["hilos"]))].append(row)
    serial_keys = {(str(row["schedule"]), str(row["afinidad"]), 1) for row in serial}
    if len(serial_keys) != 1:
        raise ValueError("T14 debe tener una sola configuración secuencial")
    for schedule, affinity in {(str(row["schedule"]), str(row["afinidad"])) for row in parallel}:
        found = {threads for s, a, threads in groups if (s, a) == (schedule, affinity)}
        if found != set(THREADS):
            raise ValueError(f"{schedule}/{affinity}: faltan puntos de 2, 4, 8 o 16 hilos")
    stats = {}
    for key, rows in groups.items():
        warmups = [row for row in rows if row["calentamiento"]]
        measured = [row for row in rows if not row["calentamiento"]]
        if len(warmups) != 1 or sorted(int(row["repeticion"]) for row in measured) != [1, 2, 3, 4, 5]:
            raise ValueError(f"{key}: se requiere un calentamiento y cinco repeticiones únicas")
        times = [float(row["tiempo_s"]) for row in measured]
        stats[key] = statistics.mean(times), statistics.stdev(times)
    baseline = stats[next(iter(serial_keys))][0]
    result = []
    for key in sorted(groups, key=lambda item: (item[2] != 1, item[0], item[1], item[2])):
        source = groups[key][0]
        mean, deviation = stats[key]
        speedup = baseline / mean
        result.append({"modelo": source["modelo"], "schedule": key[0], "afinidad": key[1],
                       "hilos": key[2], "sobresuscrito": int(key[2] > int(source["nucleos_fisicos"])),
                       "n": source["n"], "semilla": source["semilla"], "cpu": source["cpu"],
                       "nucleos_fisicos": source["nucleos_fisicos"], "commit": source["commit"],
                       "muestras": 5, "tiempo_medio_s": mean, "desviacion_estandar_s": deviation,
                       "speedup": speedup, "eficiencia": speedup / key[2]})
    return result


def chart(rows: list[dict[str, object]], metric: str, title: str, ylabel: str) -> str:
    width, height, left, top, plot_w, plot_h = 920, 590, 92, 105, 780, 330
    parallel = [row for row in rows if row["modelo"] == "openmp"]
    series: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in parallel:
        series[(str(row["schedule"]), str(row["afinidad"]))].append(row)
    ceiling = max(float(row[metric]) + (float(row["desviacion_estandar_s"]) if metric == "tiempo_medio_s" else 0)
                  for row in rows)
    ceiling = max(ceiling, 16 if metric == "speedup" else 1 if metric == "eficiencia" else 0) * 1.18
    xp = lambda p: left + (THREADS.index(p) + 0.5) * plot_w / 4
    yp = lambda v: top + plot_h * (1 - float(v) / ceiling)
    first = rows[0]
    subtitle_one = f"N={first['n']} · semilla={first['semilla']} · commit={first['commit']}"
    subtitle_two = f"CPU={first['cpu']} · {first['nucleos_fisicos']} núcleos físicos"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">',
             '<rect width="100%" height="100%" fill="white"/>',
             f'<text x="{left}" y="45" font-family="Arial,sans-serif" font-size="26" font-weight="700" fill="#171B35">{escape(title)}</text>',
             f'<text x="{left}" y="68" font-family="Arial,sans-serif" font-size="12" fill="#39415E">{escape(subtitle_one)}</text>',
             f'<text x="{left}" y="87" font-family="Arial,sans-serif" font-size="12" fill="#39415E">{escape(subtitle_two)}</text>']
    for tick in range(6):
        value = ceiling * tick / 5
        y = yp(value)
        parts += [f'<line x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" stroke="#E5E8F0"/>',
                  f'<text x="{left-12}" y="{y+4:.1f}" text-anchor="end" font-family="Arial,sans-serif" font-size="12" fill="#39415E">{value:.2g}</text>']
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="#39415E"/>')
    for p in THREADS:
        parts.append(f'<text x="{xp(p):.1f}" y="{top+plot_h+24}" text-anchor="middle" font-family="Arial,sans-serif" font-size="13">{p}</text>')
    parts += [f'<text x="{left+plot_w/2}" y="{top+plot_h+52}" text-anchor="middle" font-family="Arial,sans-serif" font-size="14">Hilos OpenMP</text>',
              f'<text transform="translate(23,{top+plot_h/2}) rotate(-90)" text-anchor="middle" font-family="Arial,sans-serif" font-size="14">{escape(ylabel)}</text>']
    if metric == "tiempo_medio_s":
        reference = f'{left},{yp(first[metric]):.1f} {left+plot_w},{yp(first[metric]):.1f}'
        reference_label = "Línea discontinua: secuencial (T1)"
    elif metric == "speedup":
        reference = " ".join(f"{xp(p):.1f},{yp(p):.1f}" for p in THREADS)
        reference_label = "Línea discontinua: escalado ideal"
    else:
        reference = f'{left},{yp(1):.1f} {left+plot_w},{yp(1):.1f}'
        reference_label = "Línea discontinua: eficiencia ideal"
    parts.append(f'<polyline points="{reference}" fill="none" stroke="#8991A5" stroke-width="2" stroke-dasharray="7 5"/>')
    for index, (configuration, points) in enumerate(sorted(series.items())):
        color = COLORS[index % len(COLORS)]
        points.sort(key=lambda row: int(row["hilos"]))
        coordinates = " ".join(f"{xp(int(row['hilos'])):.1f},{yp(row[metric]):.1f}" for row in points)
        parts.append(f'<polyline points="{coordinates}" fill="none" stroke="{color}" stroke-width="3"/>')
        for row in points:
            x, y = xp(int(row["hilos"])), yp(row[metric])
            if metric == "tiempo_medio_s":
                delta = float(row["desviacion_estandar_s"])
                parts.append(f'<line x1="{x:.1f}" y1="{yp(float(row[metric])-delta):.1f}" x2="{x:.1f}" y2="{yp(float(row[metric])+delta):.1f}" stroke="{color}" stroke-width="2"/>')
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{color}" stroke="white" stroke-width="2"/>')
            if row["sobresuscrito"]:
                parts.append(f'<text x="{x+9:.1f}" y="{y-8:.1f}" font-family="Arial,sans-serif" font-size="16">†</text>')
        legend_x, legend_y = left + (index % 3) * 250, height - 42 + (index // 3) * 22
        legend_label = escape(configuration[0] + " · " + configuration[1])
        parts += [f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x+22}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>',
                  f'<text x="{legend_x+30}" y="{legend_y+4}" font-family="Arial,sans-serif" font-size="12">{legend_label}</text>']
    note = reference_label + " · 5 repeticiones · † sobresuscrito"
    if metric == "tiempo_medio_s":
        note += " · barras ±1 desviación estándar"
    parts += [f'<text x="{left}" y="{height-80}" font-family="Arial,sans-serif" font-size="11" fill="#59627C">{escape(note)}</text>', '</svg>']
    return "\n".join(parts) + "\n"


def write_outputs(rows: list[dict[str, object]], out: Path, serial_path: Path, parallel_path: Path) -> None:
    processed, figures = out / "processed", out / "figures"
    processed.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    provenance = {"fuente_t14": str(serial_path), "sha256_t14": hashlib.sha256(serial_path.read_bytes()).hexdigest(),
                  "fuente_t16": str(parallel_path), "sha256_t16": hashlib.sha256(parallel_path.read_bytes()).hexdigest()}
    with (processed / "openmp_resumen.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) + list(provenance))
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, **provenance})
    for metric, name, title, ylabel in (
        ("tiempo_medio_s", "openmp_tiempo.svg", "Tiempo medio por número de hilos", "Tiempo (s)"),
        ("speedup", "openmp_speedup.svg", "Aceleración frente al secuencial", "Speedup (T1/Tp)"),
        ("eficiencia", "openmp_eficiencia.svg", "Eficiencia por número de hilos", "Eficiencia (speedup/p)"),
    ):
        (figures / name).write_text(chart(rows, metric, title, ylabel), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--secuencial", required=True, type=Path, help="CSV T14")
    parser.add_argument("--openmp", required=True, type=Path, help="CSV T16")
    parser.add_argument("--salida", type=Path, default=Path("results"))
    args = parser.parse_args()
    try:
        serial = read_csv(args.secuencial, "secuencial")
        parallel = read_csv(args.openmp, "openmp")
        rows = summarize(serial, parallel)
        write_outputs(rows, args.salida, args.secuencial, args.openmp)
    except (OSError, ValueError) as exc:
        print(f"T18: {exc}", file=sys.stderr)
        return 1
    print(f"T18: {len(rows)} filas agregadas y tres figuras SVG en {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
