"""Verificación independiente de comprobantes diarios de la Empresa A.
No calcula productividad en pedidos, porque el origen sólo contiene comprobantes.
"""
from csv import DictReader
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


class DatosIncompatibles(ValueError):
    pass


def auditar(path):
    """Lee sólo campos agregados y comprueba coherencia, sin datos personales."""
    archivo = Path(path)
    if not archivo.exists():
        raise DatosIncompatibles("No se encontró el CSV de comprobantes reales.")
    with archivo.open(encoding="utf-8-sig", newline="") as f:
        datos = list(DictReader(f))
    columnas = {"fecha", "dia", "comprobantes_activos", "venta_total_soles",
                "venta_rapida", "venta_salon", "trabajadores_activos"}
    if not datos or not columnas.issubset(datos[0]):
        raise DatosIncompatibles("CSV vacío o faltan campos de comprobantes.")
    vistos = set()
    comprobantes = 0
    importe = Decimal("0")
    comp_lun_vie = 0
    dotacion_lun_vie = 0
    dias_lun_vie = 0
    sabados = 0
    comp_sabados = 0
    registros = []
    for fila in datos:
        try:
            fecha = date.fromisoformat(fila["fecha"])
            n = int(fila["comprobantes_activos"])
            a = int(fila["venta_rapida"])
            b = int(fila["venta_salon"])
            monto = Decimal(fila["venta_total_soles"])
        except (ValueError, KeyError, InvalidOperation, TypeError) as e:
            raise DatosIncompatibles("Fecha o valor inválido en CSV agregado.") from e
        if fecha in vistos or fecha.year != 2026 or fecha.month != 10:
            raise DatosIncompatibles("Hay fechas repetidas o ajenas a octubre de 2026.")
        vistos.add(fecha)
        if n < 0 or a < 0 or b < 0 or monto < 0 or a + b != n:
            raise DatosIncompatibles("La suma de los dos canales no coincide con el total.")
        trabajadores_texto = (fila.get("trabajadores_activos") or "").strip()
        if fecha.weekday() < 5:
            if not trabajadores_texto:
                raise DatosIncompatibles("Falta dotación del día laborable registrado.")
            trabajadores = int(trabajadores_texto)
            if trabajadores <= 0:
                raise DatosIncompatibles("Dotación inválida.")
            comp_lun_vie += n
            dotacion_lun_vie += trabajadores
            dias_lun_vie += 1
        elif fecha.weekday() == 5:
            sabados += 1
            comp_sabados += n
            if trabajadores_texto:
                raise DatosIncompatibles("No se deben completar trabajadores de sábado sin evidencia.")
        else:
            raise DatosIncompatibles("Hay ventas en domingo: verificar clasificación.")
        comprobantes += n
        importe += monto
        registros.append({"fecha": fecha.isoformat(), "dia": fila["dia"],
                          "comprobantes_activos": n, "venta_total_soles": float(monto),
                          "venta_rapida": a, "venta_salon": b,
                          "trabajadores_activos": int(trabajadores_texto) if trabajadores_texto else None,
                          "es_sabado": fecha.weekday() == 5})
    if dotacion_lun_vie == 0:
        raise DatosIncompatibles("No hay días laborables con dotación acreditada.")
    resumen = {"comprobantes_total": comprobantes,
               "venta_total_soles": float(importe),
               "dias_con_ventas": len(registros),
               "dias_lun_vie": dias_lun_vie,
               "comprobantes_lun_vie": comp_lun_vie,
               "trabajador_dias_lun_vie": dotacion_lun_vie,
               "comprobantes_sabados": comp_sabados,
               "sabados_con_ventas": sabados,
               "comprobantes_por_trabajador_dia": comp_lun_vie / dotacion_lun_vie}
    return resumen, registros
