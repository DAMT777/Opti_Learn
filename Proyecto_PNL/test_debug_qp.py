"""
Debug: Por qué el problema de cartera se detecta como KKT en lugar de QP
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'opti_learn'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opti_learn.settings')
import django
django.setup()

from opti_app.core import method_detector

# Problema de cartera
objective = "0.04*A**2 + 0.02*B**2 + 0.03*F**2 + 0.01*A*B + 0.015*A*F + 0.005*B*F"

constraints = [
    {'expr': 'A + B + F - 100', 'kind': 'eq'},           # A + B + F = 100
    {'expr': '0.10*A + 0.05*B + 0.08*F - 7.5', 'kind': 'ge'},  # retorno ≥ 7.5
    {'expr': 'A - 20', 'kind': 'ge'},                    # A ≥ 20
    {'expr': '50 - B', 'kind': 'ge'},                    # B ≤ 50
    {'expr': 'F - 10', 'kind': 'ge'},                    # F ≥ 10
    {'expr': '40 - F', 'kind': 'ge'},                    # F ≤ 40
    {'expr': 'B + F - 45', 'kind': 'ge'},                # B + F ≥ 45
]

print("\n" + "=" * 80)
print("DEBUG: Detección del Problema de Cartera de Inversión")
print("=" * 80 + "\n")

# Paso 1: Verificar si es cuadrática
print("1️⃣ ¿La función objetivo es cuadrática?")
is_quadratic = method_detector._is_quadratic_objective(objective)
print(f"   Resultado: {is_quadratic}")
print(f"   Función: {objective}")
print()

# Paso 2: Verificar cada restricción
print("2️⃣ ¿Todas las restricciones son lineales?")
for i, c in enumerate(constraints, 1):
    is_nonlinear = method_detector._is_nonlinear_expression(c['expr'])
    status = "❌ NO LINEAL" if is_nonlinear else "✅ LINEAL"
    print(f"   {i}. {c['expr']:<40} → {status}")

all_linear = method_detector._has_only_linear_constraints(constraints)
print(f"\n   Todas lineales: {all_linear}")
print()

# Paso 3: ¿Es problema QP?
print("3️⃣ ¿Cumple criterios de QP?")
is_qp = method_detector._is_qp_problem(objective, constraints)
print(f"   Resultado: {is_qp}")
print()

# Paso 4: Flujo de decisión completo
print("4️⃣ Flujo de detección (en orden):")
print()

# Regla 1
iterative = method_detector._detect_iterative_process("")
print(f"   Regla 1 - ¿Iterativo? {iterative}")
if iterative:
    print("   → GRADIENTE")
    print()

# Regla 2
has_nonlinear = method_detector._has_nonlinear_constraints(constraints)
print(f"   Regla 2 - ¿Restricciones no lineales? {has_nonlinear}")
if has_nonlinear:
    print("   → KKT ⚠️ AQUÍ ESTÁ EL PROBLEMA!")
    print()
    # Identificar cuál restricción se detectó como no lineal
    print("   Restricciones detectadas como NO LINEALES:")
    for i, c in enumerate(constraints, 1):
        if method_detector._is_nonlinear_expression(c['expr']):
            print(f"      - Restricción {i}: {c['expr']}")
    print()

# Regla 3
only_eq = method_detector._has_only_equality_constraints(constraints)
print(f"   Regla 3 - ¿Solo igualdades? {only_eq}")
if only_eq:
    print("   → LAGRANGE")

# Regla 4
is_explicit_qp = method_detector._is_explicit_qp("", objective, constraints)
print(f"   Regla 4 - ¿Es QP (estructura)? {is_explicit_qp}")
if is_explicit_qp:
    print("   → QP ✅ DEBERÍA LLEGAR AQUÍ!")

# Regla 5
has_ineq = method_detector._has_any_inequalities(constraints)
print(f"   Regla 5 - ¿Hay desigualdades? {has_ineq}")
if has_ineq:
    print("   → KKT")
print()

# Resultado final
print("=" * 80)
result = method_detector.explain_method_choice("", objective, constraints)
print(f"🎯 MÉTODO FINAL DETECTADO: {result['method'].upper()}")
print(f"📝 Razón: {result['reason']}")
print(f"📏 Regla aplicada: {result['rule_applied']}")
print("=" * 80)

if result['method'] != 'qp':
    print("\n❌ ERROR: Debería ser QP pero se detectó como", result['method'].upper())
else:
    print("\n✅ CORRECTO: Se detectó como QP")

print()
