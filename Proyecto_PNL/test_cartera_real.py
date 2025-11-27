"""
Test con el problema EXACTO de la imagen de cartera
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'opti_learn'))

from opti_app.core.method_detector import determine_method, explain_method_choice

# Problema EXACTO de la imagen
problema_cartera = """
Una gestora de inversiones desea construir una cartera óptima combinando 
tres activos financieros: Acciones (A), Bonos (B) y Fondos de Inversión (F). El 
objetivo es minimizar el riesgo total de la cartera, medido por la varianza del 
portafolio, que depende de manera cuadrática de las proporciones 
invertidas en cada activo. Modelo de Riesgo La función de riesgo (varianza) 
de la cartera se ha modelado como: Riesgo = 0.04A² + 0.02B² + 0.03F² + 
0.01AB + 0.015AF + 0.005BF Donde A, B y F representan las cantidades (en 
miles de dólares) invertidas en cada activo. Restricciones operativas: 
Presupuesto total: La inversión total debe ser exactamente de $100,000 (100 
mil). A + B + F = 100 Rentabilidad mínima: La cartera debe generar 
un retorno esperado de al menos 7.5 unidades. Los retornos unitarios son: 
Acciones: 0.10, Bonos: 0.05, Fondos (0.08). 0.10A + 0.05B + 0.08F ≥ 7.5 
Límites de diversificación: Las acciones deben representar al menos el 20% 
de la cartera. Los bonos no pueden superar el 50% de la cartera. B ≤ 50 Los 
Los fondos deben estar entre 10% y 40%: 10 ≤ F ≤ 40 Restricción de 
liquidez: Para mantener fluidez, la suma de bonos y fondos debe ser al 
menos 45 B + F ≥ 45 Pregunta: Determine las cantidades óptimas a invertir 
en cada activo (A, B, F) que minimicen el riesgo total de la cartera, 
cumpliendo todas las restricciones anteriores.
"""

# Simular lo que el AI parser extrae
constraints = [
    {'kind': 'eq', 'expr': 'A + B + F - 100'},  # A + B + F = 100
    {'kind': 'ge', 'expr': '0.10*A + 0.05*B + 0.08*F - 7.5'},  # rentabilidad >= 7.5
    {'kind': 'ge', 'expr': 'A - 20'},  # A >= 20
    {'kind': 'le', 'expr': 'B - 50'},  # B <= 50
    {'kind': 'ge', 'expr': 'F - 10'},  # F >= 10
    {'kind': 'le', 'expr': 'F - 40'},  # F <= 40
    {'kind': 'ge', 'expr': 'B + F - 45'},  # B + F >= 45
]

objective = '0.04*A**2 + 0.02*B**2 + 0.03*F**2 + 0.01*A*B + 0.015*A*F + 0.005*B*F'

print("="*80)
print("PROBLEMA DE CARTERA DE INVERSIONES")
print("="*80)
print(f"\nObjetivo: {objective}")
print(f"\nRestricciones:")
for i, c in enumerate(constraints, 1):
    print(f"  {i}. {c['expr']} {c['kind']}")

# Test detección
method = determine_method(problema_cartera, objective, constraints)
explanation = explain_method_choice(problema_cartera, objective, constraints)

print("\n" + "="*80)
print("RESULTADO DE DETECCIÓN")
print("="*80)
print(f"Método detectado: {method.upper()}")
print(f"Razón: {explanation['reason']}")
print(f"Regla aplicada: {explanation['rule_applied']}")

# Análisis de restricciones
print("\n" + "="*80)
print("ANÁLISIS DE RESTRICCIONES")
print("="*80)
has_eq = any(c['kind'] == 'eq' for c in constraints)
has_ge = any(c['kind'] == 'ge' for c in constraints)
has_le = any(c['kind'] == 'le' for c in constraints)

print(f"Tiene igualdades (eq): {has_eq}")
print(f"Tiene desigualdades >= (ge): {has_ge}")
print(f"Tiene desigualdades <= (le): {has_le}")
print(f"Total restricciones: {len(constraints)}")

print("\n" + "="*80)
print("VERIFICACIÓN")
print("="*80)
expected = "qp"
if method == expected:
    print(f"✅ CORRECTO: Se detectó {expected.upper()}")
else:
    print(f"❌ ERROR: Se esperaba {expected.upper()} pero se detectó {method.upper()}")
    print("\nEste es un problema QP porque:")
    print("  - Función objetivo CUADRÁTICA: 0.04A² + 0.02B² + ...")
    print("  - Restricciones LINEALES: A+B+F=100, 0.10A+0.05B+0.08F≥7.5, etc.")
    print("  - Tiene 1 igualdad Y 6 desigualdades")
