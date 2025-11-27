"""Análisis detallado del problema de alimentos balanceados"""

import sys
sys.path.insert(0, 'opti_learn')

from opti_app.core import message_parser

# El problema menciona:
# - "costo energético crece de manera no lineal... depende del cuadrado de la cantidad empleada"
# - Esto sugiere f(x,y) = x² + y² (o similar)
# - x + y = 100 (restricción de igualdad)
# - 20 ≤ x ≤ 70
# - y ≤ 60 (y además y = 100 - x, entonces y ≥ 30)
# - 0.25x + 0.35y ≥ 28 (proteína)
# - x ≤ 65 (65% de 100)
# - y ≤ 65

# Pero el problema NO especifica explícitamente la función objetivo
# Solo dice "minimicen el costo total" donde el costo "depende del cuadrado"

problema_reformulado = """
Minimizar f(x,y) = x² + y²
sujeto a:
x + y = 100
20 ≤ x ≤ 70
y ≤ 60
0.25*x + 0.35*y ≥ 28
x ≤ 65
y ≤ 65
x ≥ 0
y ≥ 0
"""

print("PROBLEMA REFORMULADO CON FUNCIÓN EXPLÍCITA:")
print("="*80)
resultado = message_parser.parse_structured_payload(problema_reformulado, allow_partial=True)
if resultado:
    print(f"Función: {resultado.get('objective_expr')}")
    print(f"Variables: {resultado.get('variables')}")
    print(f"Restricciones: {resultado.get('constraints')}")
    print(f"Num restricciones: {len(resultado.get('constraints', []))}")
else:
    print("No se pudo parsear")
