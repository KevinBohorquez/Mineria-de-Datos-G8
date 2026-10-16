"""T06/T08/T09 | Utilidades compartidas para leer y auditar las series diarias SENAMHI.

Reglas de procesamiento (docs/definicion-proyecto.docx §7.5–7.7; detalle en docs/auditoria-datos.md):

- Temporada: 1 de enero a 30 de abril. Se excluye el 29 de febrero para que toda temporada
  tenga D = 120 días; el 28 de febrero y el 1 de marzo se tratan como días consecutivos.
- Día lluvioso: precipitación >= 0.1 mm. Los valores en (0, 0.1) son trazas y cuentan como días
  secos (no son faltantes).
- Faltante: fecha sin fila, valor vacío, valor no numérico o valor negativo.
- Fecha duplicada: se conserva la primera aparición y se marca en la auditoría.
- Atípico: > 150 mm/día; se marca y se conserva.
- Temporada elegible: menos del 10 % de días faltantes. Estación calificada: >= 20 temporadas
  elegibles. Se seleccionan hasta 5 calificadas con menor % faltante enero–abril.

Solo usa la biblioteca estándar para poder ejecutarse en la imagen pp-g8 sin pandas.
"""
import csv
from datetime import date, timedelta
from pathlib import Path

UMBRAL_LLUVIA_MM = 0.1
UMBRAL_ATIPICO_MM = 150.0
DIAS_TEMPORADA = 120
MAX_PCT_FALTANTE = 10.0
MIN_TEMPORADAS_ELEGIBLES = 20
MAX_ESTACIONES = 5

RAIZ = Path(__file__).resolve().parents[2]
DIR_RAW = RAIZ / "data" / "raw"
DIR_PROCESADOS = RAIZ / "data" / "processed"
DIR_METADATOS = RAIZ / "data" / "metadata"


# ---------------------------------------------------------------- lectura

def leer_serie(ruta):
    """Lee un CSV `fecha,precipitacion_mm` y devuelve [(date, float | None)] en orden de archivo.

    Conserva duplicados y negativos tal como vienen (la auditoría los cuenta); un valor vacío o
    no numérico se devuelve como None. Acepta finales de línea LF o CRLF.
    """
    filas = []
    with open(ruta, newline="", encoding="utf-8") as f:
        for registro in csv.DictReader(f):
            fecha = date.fromisoformat(registro["fecha"].strip())
            filas.append((fecha, a_valor(registro.get("precipitacion_mm"))))
    return filas


def a_valor(texto):
    """Convierte el texto del CSV en mm; vacío o no numérico -> None."""
    texto = (texto or "").strip()
    if not texto:
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def valor_valido(mm):
    """True si el valor es un dato utilizable (no faltante ni negativo)."""
    return mm is not None and mm >= 0.0


def es_lluvioso(mm):
    """Día lluvioso: precipitación >= 0.1 mm. Trazas, ceros y faltantes no lo son."""
    return mm is not None and mm >= UMBRAL_LLUVIA_MM


def es_traza(mm):
    """Traza: 0 < mm < 0.1. Cuenta como día seco."""
    return mm is not None and 0.0 < mm < UMBRAL_LLUVIA_MM


def primera_aparicion(serie):
    """Diccionario fecha -> valor quedándose con la primera fila de cada fecha."""
    indice = {}
    for fecha, mm in serie:
        indice.setdefault(fecha, mm)
    return indice


# ---------------------------------------------------------------- temporada enero–abril

def fechas_temporada(anio):
    """Las 120 fechas de la temporada enero–abril de `anio`, sin el 29 de febrero."""
    dia, fin = date(anio, 1, 1), date(anio, 4, 30)
    fechas = []
    while dia <= fin:
        if not (dia.month == 2 and dia.day == 29):
            fechas.append(dia)
        dia += timedelta(days=1)
    return fechas


def temporada_ene_abr(serie, anio, indice=None):
    """Devuelve [(date, float | None)] con los 120 días de la temporada de `anio`.

    Un día sin fila, vacío o negativo vale None (faltante). Con fechas duplicadas manda la
    primera fila. `indice` (de `primera_aparicion`) evita reconstruirlo en bucles por año.
    """
    if indice is None:
        indice = primera_aparicion(serie)
    salida = []
    for fecha in fechas_temporada(anio):
        mm = indice.get(fecha)
        salida.append((fecha, mm if valor_valido(mm) else None))
    return salida


def anios_temporada_completos(serie):
    """Años cuya temporada enero–abril cae completa dentro del rango [primera, última] fecha."""
    if not serie:
        return []
    inicio = min(f for f, _ in serie)
    fin = max(f for f, _ in serie)
    return [a for a in range(inicio.year, fin.year + 1)
            if date(a, 1, 1) >= inicio and date(a, 4, 30) <= fin]


def faltantes(temporada):
    return sum(1 for _, mm in temporada if mm is None)


def pct_faltante(temporada):
    return 100.0 * faltantes(temporada) / len(temporada) if temporada else 100.0


def temporada_elegible(temporada):
    """Elegible si el porcentaje de días faltantes es menor que 10 %."""
    return pct_faltante(temporada) < MAX_PCT_FALTANTE


# ---------------------------------------------------------------- estación y selección

def region_de(estacion):
    """Departamento a partir del prefijo del archivo (p. ej. piura_bernal -> Piura)."""
    return estacion.split("_", 1)[0].capitalize()


def seleccionar_estaciones(candidatas, max_estaciones=MAX_ESTACIONES,
                           min_temporadas=MIN_TEMPORADAS_ELEGIBLES):
    """Selecciona estaciones calificadas.

    `candidatas`: lista de dicts con estacion, region, pct_faltante_ene_abr y
    temporadas_elegibles. Regla: califica quien tiene >= `min_temporadas` temporadas elegibles;
    se ordena por % faltante enero–abril (empate: nombre) y se toman hasta `max_estaciones`.
    Si ninguna de Lima entra pero alguna de Lima califica, la mejor de Lima reemplaza a la
    última plaza para cubrir costa norte + Lima. Devuelve [(dict, motivo)].
    """
    calificadas = sorted(
        (c for c in candidatas if c["temporadas_elegibles"] >= min_temporadas),
        key=lambda c: (c["pct_faltante_ene_abr"], c["estacion"]))
    elegidas = [(c, "menor % faltante ene-abr entre calificadas")
                for c in calificadas[:max_estaciones]]
    hay_lima = any(c["region"] == "Lima" for c, _ in elegidas)
    lima = [c for c in calificadas if c["region"] == "Lima"]
    if not hay_lima and lima and elegidas:
        elegidas[-1] = (lima[0], "mejor estación de Lima calificada (cobertura Lima)")
    return elegidas


def escribir_csv(ruta, columnas, filas):
    """Escribe un CSV UTF-8 con LF y la cabecera dada."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columnas, lineterminator="\n")
        w.writeheader()
        for fila in filas:
            w.writerow(fila)


def leer_csv(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- regímenes (T09)

def temporada_de_evento(evento):
    """Temporada enero–abril afectada por un evento El Niño.

    Un evento que abarca Y–Y+1 ('1982-1983' o '1982-83') afecta la temporada de Y+1; un evento
    de un solo año ('2017') afecta la temporada de ese año.
    """
    partes = evento.strip().split("-")
    inicio = int(partes[0])
    if len(partes) == 1:
        return inicio
    fin = partes[-1].strip()
    if len(fin) == 2:
        fin = str(inicio)[:2] + fin
    return int(fin)


def clasificar_temporada(anio, temporadas_el_nino):
    return "el_nino" if anio in temporadas_el_nino else "normal"
