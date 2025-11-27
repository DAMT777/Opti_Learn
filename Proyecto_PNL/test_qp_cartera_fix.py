#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test del solver QP con formulación correcta de restricciones
"""

import sys
sys.path.insert(0, 'opti_learn')

from opti_app.core.solver_qp_kkt import solve_qp

print("PROBLEMA DE CARTERA - Test de formulación correcta")
print("=" * 80)

# Problema:
# min 0.04A² + 0.02B² + 0.03F² + 0.01AB + 0.015AF + 0.005BF
# s.a:
#   A + B + F = 100              (eq)
#   0.10A + 0.05B + 0.08F >= 7.5 (ge)
#   A >= 20                       (ge)
#   B <= 50                       (le)
#   F >= 10                       (ge)
#   F <= 40                       (le)
#   B + F >= 45                   (ge)
#   A, B, F >= 0

result = solve_qp(
    '0.04*A**2 + 0.02*B**2 + 0.03*F**2 + 0.01*A*B + 0.015*A*F + 0.005*B*F',
    ['A', 'B', 'F'],
    [
        {'expr': 'A + B + F - 100', 'kind': 'eq', 'rhs': 0.0},
        {'expr': '0.10*A + 0.05*B + 0.08*F - 7.5', 'kind': 'ge', 'rhs': 0.0},
        {'expr': 'A - 20', 'kind': 'ge', 'rhs': 0.0},
        {'expr': '50 - B', 'kind': 'ge', 'rhs': 0.0},  # B <= 50  →  -B >= -50  →  50-B >= 0
        {'expr': 'F - 10', 'kind': 'ge', 'rhs': 0.0},
        {'expr': '40 - F', 'kind': 'ge', 'rhs': 0.0},  # F <= 40  →  -F >= -40  →  40-F >= 0
        {'expr': 'B + F - 45', 'kind': 'ge', 'rhs': 0.0},
    ]
)

print(f"\nStatus: {result['status']}")
if result.get('x_star'):
    x = result['x_star']
    print(f"\nSOLUCION:")
    print(f"  A = {x[0]:.4f} (esperado ~29.23)")
    print(f"  B = {x[1]:.4f} (esperado ~36.15)")
    print(f"  F = {x[2]:.4f} (esperado ~34.62)")
    print(f"  Riesgo = {result.get('f_star', 0):.4f} (esperado ~128.27)")
    
    # Verificar restricciones
    print(f"\nVERIFICACION:")
    A, B, F = x
    print(f"  A + B + F = {A+B+F:.4f} (= 100)")
    print(f"  0.10A + 0.05B + 0.08F = {0.10*A + 0.05*B + 0.08*F:.4f} (>= 7.5)")
    print(f"  A = {A:.4f} (>= 20)")
    print(f"  B = {B:.4f} (<= 50)")
    print(f"  F = {F:.4f} (>= 10, <= 40)")
    print(f"  B + F = {B+F:.4f} (>= 45)")
else:
    print(f"\nERROR: {result.get('message', '')}")

# Ahora probar con 'le' directamente
print("\n\n" + "=" * 80)
print("TEST ALTERNATIVO CON 'le' DIRECTO")
print("=" * 80)

result2 = solve_qp(
    '0.04*A**2 + 0.02*B**2 + 0.03*F**2 + 0.01*A*B + 0.015*A*F + 0.005*B*F',
    ['A', 'B', 'F'],
    [
        {'expr': 'A + B + F - 100', 'kind': 'eq', 'rhs': 0.0},
        {'expr': '0.10*A + 0.05*B + 0.08*F - 7.5', 'kind': 'ge', 'rhs': 0.0},
        {'expr': 'A - 20', 'kind': 'ge', 'rhs': 0.0},
        {'expr': 'B - 50', 'kind': 'le', 'rhs': 0.0},  # B <= 50
        {'expr': 'F - 10', 'kind': 'ge', 'rhs': 0.0},
        {'expr': 'F - 40', 'kind': 'le', 'rhs': 0.0},  # F <= 40
        {'expr': 'B + F - 45', 'kind': 'ge', 'rhs': 0.0},
    ]
)

print(f"\nStatus: {result2['status']}")
if result2.get('x_star'):
    x = result2['x_star']
    print(f"\nSOLUCION:")
    print(f"  A = {x[0]:.4f}")
    print(f"  B = {x[1]:.4f}")
    print(f"  F = {x[2]:.4f}")
    print(f"  Riesgo = {result2.get('f_star', 0):.4f}")
else:
    print(f"\nERROR: {result2.get('message', '')}")
