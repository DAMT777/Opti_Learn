#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para probar el solver QP y guardar su salida."""

import sys
sys.path.insert(0, '.')

from opti_app.core.solver_qp_simplex_real import solve_qp

# Problema de prueba: min x^2 + y^2 sujeto a x + y = 1
result = solve_qp(
    'A**2 + B**2',
    ['A', 'B'],
    [{'expr': 'A + B', 'kind': 'eq', 'rhs': 1.0}]
)

# Guardar explicación completa
with open('test_output.md', 'w', encoding='utf-8') as f:
    f.write(result['explanation'])

print("✅ Archivo generado: test_output.md")
print(f"Status: {result['status']}")
print(f"Pasos: {len(result.get('steps', []))}")
print(f"Solución: {result.get('x_star')}")
print(f"Valor objetivo: {result.get('f_star')}")
