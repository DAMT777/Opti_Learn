"""
Test visual rápido - Generar solo un problema para ver la visualización 3D
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'opti_learn'))

from opti_app.core.solver_lagrange import solve_with_lagrange_method

print("\n" + "="*70)
print("🌐 GENERANDO VISUALIZACIÓN 3D - Problema del Servidor")
print("="*70)

result = solve_with_lagrange_method(
    objective_expression="-t**2 - k**2 + 12*t + 8*k",
    variable_names=['t', 'k'],
    equality_constraints=["2*t + k - 18"]
)

# Guardar resultado
with open("ejemplo_lagrange_3d.md", "w", encoding="utf-8") as f:
    f.write(result['explanation'])

print("\n✅ Archivo guardado en: ejemplo_lagrange_3d.md")
print("\n📊 Imágenes generadas:")
print("   - 2D (curvas de nivel): lagrange_2d_*.png")
print("   - 3D (superficie): lagrange_3d_*.png")
print("\n🔍 Abre el archivo .md para ver el resultado completo")
