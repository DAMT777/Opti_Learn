"""
Test para verificar que el recommender_ai ahora detecta QP correctamente
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'opti_learn'))

from opti_app.core import recommender_ai

print("="*80)
print("TEST: Recommender AI con reglas v3.2.0")
print("="*80)

# Caso 1: Problema QP (cuadrática + lineal + igualdades Y desigualdades)
print("\n1. PROBLEMA QP (como cartera de inversiones)")
meta_qp = {
    'has_equalities': True,
    'has_inequalities': True,
    'is_quadratic': True,
    'constraints_are_linear': True,
    'has_constraints': True,
    'iterative_process': False,
    'derivative_only': False
}

result = recommender_ai.recommend(meta_qp)
print(f"   Método: {result['method']}")
print(f"   Razón: {result['rationale']}")
if result['method'] == 'qp':
    print("   ✓ CORRECTO")
else:
    print(f"   ✗ ERROR: Esperaba 'qp', obtuvo '{result['method']}'")

# Caso 2: Solo igualdades (sin desigualdades) → Lagrange
print("\n2. SOLO IGUALDADES (sin desigualdades)")
meta_lagrange = {
    'has_equalities': True,
    'has_inequalities': False,
    'is_quadratic': False,
    'constraints_are_linear': True,
    'has_constraints': True,
    'iterative_process': False,
    'derivative_only': False
}

result = recommender_ai.recommend(meta_lagrange)
print(f"   Método: {result['method']}")
print(f"   Razón: {result['rationale']}")
if result['method'] == 'lagrange':
    print("   ✓ CORRECTO")
else:
    print(f"   ✗ ERROR: Esperaba 'lagrange', obtuvo '{result['method']}'")

# Caso 3: Solo desigualdades (sin igualdades) → KKT
print("\n3. SOLO DESIGUALDADES (sin igualdades)")
meta_kkt = {
    'has_equalities': False,
    'has_inequalities': True,
    'is_quadratic': True,
    'constraints_are_linear': True,
    'has_constraints': True,
    'iterative_process': False,
    'derivative_only': False
}

result = recommender_ai.recommend(meta_kkt)
print(f"   Método: {result['method']}")
print(f"   Razón: {result['rationale']}")
if result['method'] == 'kkt':
    print("   ✓ CORRECTO")
else:
    print(f"   ✗ ERROR: Esperaba 'kkt', obtuvo '{result['method']}'")

# Caso 4: Restricciones no lineales → KKT
print("\n4. RESTRICCIONES NO LINEALES")
meta_kkt_nl = {
    'has_equalities': True,
    'has_inequalities': True,
    'is_quadratic': False,
    'constraints_are_linear': False,
    'has_constraints': True,
    'iterative_process': False,
    'derivative_only': False
}

result = recommender_ai.recommend(meta_kkt_nl)
print(f"   Método: {result['method']}")
print(f"   Razón: {result['rationale']}")
if result['method'] == 'kkt':
    print("   ✓ CORRECTO")
else:
    print(f"   ✗ ERROR: Esperaba 'kkt', obtuvo '{result['method']}'")

# Caso 5: Proceso iterativo → Gradient
print("\n5. PROCESO ITERATIVO")
meta_gradient = {
    'has_equalities': False,
    'has_inequalities': False,
    'is_quadratic': False,
    'constraints_are_linear': True,
    'has_constraints': False,
    'iterative_process': True,
    'derivative_only': False
}

result = recommender_ai.recommend(meta_gradient)
print(f"   Método: {result['method']}")
print(f"   Razón: {result['rationale']}")
if result['method'] == 'gradient':
    print("   ✓ CORRECTO")
else:
    print(f"   ✗ ERROR: Esperaba 'gradient', obtuvo '{result['method']}'")

print("\n" + "="*80)
print("RESUMEN")
print("="*80)
print("Si todos los tests pasaron, el recommender_ai está funcionando correctamente.")
print("Ahora prueba el problema de cartera en la interfaz web.")
print("="*80)
