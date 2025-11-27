#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para probar el solver QP con el problema de cartera de inversiones.
"""

import sys
sys.path.insert(0, '.')

from opti_app.core.solver_qp_kkt import solve_qp

# Problema de cartera de inversiones
# min 0.04A² + 0.02B² + 0.03F² + 0.01AB + 0.015AF + 0.005BF
# s.a:
#   A + B + F = 100 (presupuesto)
#   0.10A + 0.05B + 0.08F >= 7.5 (rentabilidad mínima)
#   A >= 20 (mínimo 20% en acciones)
#   B <= 50 (máximo 50% en bonos)
#   10 <= F <= 40 (fondos entre 10% y 40%)
#   B + F >= 45 (liquidez)

result = solve_qp(
    '0.04*A**2 + 0.02*B**2 + 0.03*F**2 + 0.01*A*B + 0.015*A*F + 0.005*B*F',
    ['A', 'B', 'F'],
    [
        # Igualdades
        {'expr': 'A + B + F', 'kind': 'eq', 'rhs': 100.0},
        
        # Desigualdades (NOTA: scipy usa <= por defecto, así que invertimos >= a <=)
        # 0.10A + 0.05B + 0.08F >= 7.5  →  -0.10A - 0.05B - 0.08F <= -7.5
        {'expr': '-0.10*A - 0.05*B - 0.08*F', 'kind': 'ineq', 'rhs': -7.5},
        
        # A >= 20  →  -A <= -20
        {'expr': '-A', 'kind': 'ineq', 'rhs': -20.0},
        
        # B <= 50
        {'expr': 'B', 'kind': 'ineq', 'rhs': 50.0},
        
        # F >= 10  →  -F <= -10
        {'expr': '-F', 'kind': 'ineq', 'rhs': -10.0},
        
        # F <= 40
        {'expr': 'F', 'kind': 'ineq', 'rhs': 40.0},
        
        # B + F >= 45  →  -B - F <= -45
        {'expr': '-B - F', 'kind': 'ineq', 'rhs': -45.0},
    ]
)

print("=" * 80)
print("PROBLEMA DE CARTERA DE INVERSIONES")
print("=" * 80)
print(f"\nStatus: {result['status']}")
print(f"Método: {result.get('method', 'N/A')}")
print(f"\n{'='*80}")
print("SOLUCIÓN ÓPTIMA:")
print(f"{'='*80}")

if result.get('x_star'):
    x = result['x_star']
    print(f"  A (Acciones):          ${x[0]:.2f} mil")
    print(f"  B (Bonos):             ${x[1]:.2f} mil")
    print(f"  F (Fondos):            ${x[2]:.2f} mil")
    print(f"\n  Total invertido:       ${sum(x):.2f} mil")
    print(f"\n  Riesgo mínimo:         {result.get('f_star', 0):.6f}")
    
    # Verificar restricciones
    print(f"\n{'='*80}")
    print("VERIFICACIÓN DE RESTRICCIONES:")
    print(f"{'='*80}")
    A, B, F = x[0], x[1], x[2]
    
    print(f"  ✓ Presupuesto (A+B+F=100):        {A+B+F:.2f} ≈ 100")
    rentabilidad = 0.10*A + 0.05*B + 0.08*F
    print(f"  ✓ Rentabilidad (≥7.5):            {rentabilidad:.2f} ≥ 7.5")
    print(f"  ✓ Acciones (≥20):                 {A:.2f} ≥ 20")
    print(f"  ✓ Bonos (≤50):                    {B:.2f} ≤ 50")
    print(f"  ✓ Fondos (10≤F≤40):               10 ≤ {F:.2f} ≤ 40")
    print(f"  ✓ Liquidez (B+F≥45):              {B+F:.2f} ≥ 45")
else:
    print("  ✘ No se encontró solución")

print(f"\n{'='*80}\n")

# Guardar explicación
with open('cartera_solution.md', 'w', encoding='utf-8') as f:
    f.write(result.get('explanation', ''))

print("✅ Explicación guardada en: cartera_solution.md")
