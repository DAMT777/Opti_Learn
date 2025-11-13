from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover - dependencia opcional
    A4 = None
    canvas = None


def construir_reporte_pdf(problema: Dict[str, Any], solucion: Dict[str, Any], iteraciones: List[Dict[str, Any]]):
    if canvas is None:
        # Fallback: PDF no disponible; devolver bytes de texto
        data = (
            f"Problema: {problema.get('title','')}\n" 
            f"Objetivo: {problema.get('objective_expr','')}\n" 
            f"Solución: {solucion.get('x_star','')} f*: {solucion.get('f_star','')}\n"
        )
        return data.encode('utf-8')

    buff = BytesIO()
    c = canvas.Canvas(buff, pagesize=A4)
    textobject = c.beginText(40, 800)
    textobject.textLine("OptiLearn Reporte — Resultado")
    textobject.textLine("")
    textobject.textLine(f"Título: {problema.get('title','')}")
    textobject.textLine(f"Objetivo: {problema.get('objective_expr','')}")
    textobject.textLine(f"Método: {solucion.get('method','')}")
    textobject.textLine(f"f*: {solucion.get('f_star','')}  x*: {solucion.get('x_star','')}")
    textobject.textLine("")
    textobject.textLine("Iteraciones (resumen):")
    for it in iteraciones[:20]:
        textobject.textLine(f"k={it.get('k')} f_k={it.get('f_k')} ||g||={it.get('grad_norm')}")
    c.drawText(textobject)
    c.showPage()
    c.save()
    return buff.getvalue()


# Alias de compatibilidad
def build_report(problem: Dict[str, Any], solution: Dict[str, Any], iterations: List[Dict[str, Any]]):
    return construir_reporte_pdf(problem, solution, iterations)
