#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test del solver QP con salida de explicación completa
"""

import sys
sys.path.insert(0, 'opti_learn')

from opti_app.core.solver_qp_kkt import solve_qp

result = solve_qp(
    '0.04*A**2 + 0.02*B**2 + 0.03*F**2 + 0.01*A*B + 0.015*A*F + 0.005*B*F',
    ['A', 'B', 'F'],
    [
        {'expr': 'A + B + F - 100', 'kind': 'eq', 'rhs': 0.0},
        {'expr': '0.10*A + 0.05*B + 0.08*F - 7.5', 'kind': 'ge', 'rhs': 0.0},
        {'expr': 'A - 20', 'kind': 'ge', 'rhs': 0.0},
        {'expr': 'B - 50', 'kind': 'le', 'rhs': 0.0},
        {'expr': 'F - 10', 'kind': 'ge', 'rhs': 0.0},
        {'expr': 'F - 40', 'kind': 'le', 'rhs': 0.0},
        {'expr': 'B + F - 45', 'kind': 'ge', 'rhs': 0.0},
    ]
)

# Guardar explicación completa
with open('solucion_cartera_mejorada.md', 'w', encoding='utf-8') as f:
    f.write(result.get('explanation', ''))

print("Explicación guardada en: solucion_cartera_mejorada.md")
print(f"Status: {result['status']}")
if result.get('x_star'):
    x = result['x_star']
    print(f"A = {x[0]:.4f}, B = {x[1]:.4f}, F = {x[2]:.4f}")
    print(f"Riesgo = {result.get('f_star', 0):.4f}")
