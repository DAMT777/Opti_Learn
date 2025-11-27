#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Debug del problema de cartera - verificar formulación de restricciones
"""

import sys
sys.path.insert(0, '.')

# Verificar que las restricciones estén bien formuladas
print("VERIFICACIÓN DE RESTRICCIONES")
print("=" * 80)

# El usuario envió desde la web:
# 0.10A + 0.05B + 0.08F ≥ 7.5

# Para scipy con 'ineq', la forma es: constraint(x) >= 0
# Es decir: (0.10A + 0.05B + 0.08F) - 7.5 >= 0

# Pero scipy.minimize con type='ineq' usa: constraint(x) >= 0
# Por lo tanto debemos formular: 0.10A + 0.05B + 0.08F - 7.5 >= 0

# VERIFICAR: La imagen muestra "(0.10A + 0.05B + 0.08*F) - (7.5) ≤ 0"
# Esto está MAL. Debería ser >= 0

print("Restricción original: 0.10A + 0.05B + 0.08F >= 7.5")
print("Formulación scipy 'ineq': (0.10A + 0.05B + 0.08F) - 7.5 >= 0")
print("")
print("Lo que la imagen muestra: (0.10A + 0.05B + 0.08*F) - (7.5) <= 0")
print("Esto es INCORRECTO - está invertido!")
print("")

# El problema es que el AI extractor puede estar invirtiendo las desigualdades

from opti_app.core.solver_qp_kkt import solve_qp

# Probar con formulación correcta
print("Probando con formulación CORRECTA...")
print("=" * 80)

result = solve_qp(
    '0.04*A**2 + 0.02*B**2 + 0.03*F**2 + 0.01*A*B + 0.015*A*F + 0.005*B*F',
    ['A', 'B', 'F'],
    [
        # IGUALDAD
        {'expr': 'A + B + F', 'kind': 'eq', 'rhs': 100.0},
        
        # DESIGUALDADES (scipy 'ineq' usa constraint >= 0)
        # 0.10A + 0.05B + 0.08F >= 7.5  →  0.10A + 0.05B + 0.08F - 7.5 >= 0
        {'expr': '0.10*A + 0.05*B + 0.08*F - 7.5', 'kind': 'ineq', 'rhs': 0.0},
        
        # A >= 20  →  A - 20 >= 0
        {'expr': 'A - 20', 'kind': 'ineq', 'rhs': 0.0},
        
        # B <= 50  →  50 - B >= 0
        {'expr': '50 - B', 'kind': 'ineq', 'rhs': 0.0},
        
        # F >= 10  →  F - 10 >= 0
        {'expr': 'F - 10', 'kind': 'ineq', 'rhs': 0.0},
        
        # F <= 40  →  40 - F >= 0
        {'expr': '40 - F', 'kind': 'ineq', 'rhs': 0.0},
        
        # B + F >= 45  →  B + F - 45 >= 0
        {'expr': 'B + F - 45', 'kind': 'ineq', 'rhs': 0.0},
    ]
)

print(f"Status: {result['status']}")
if result.get('x_star'):
    x = result['x_star']
    print(f"A = {x[0]:.2f}")
    print(f"B = {x[1]:.2f}")
    print(f"F = {x[2]:.2f}")
    print(f"Riesgo = {result.get('f_star', 0):.4f}")
else:
    print(f"Error: {result.get('message', '')}")
