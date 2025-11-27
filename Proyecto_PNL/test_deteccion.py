"""
Test completo de detección QP vs KKT vs Lagrange (v3.1.0)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'opti_learn'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opti_learn.settings')
import django
django.setup()

from opti_app.core import method_detector

def test_case(name, objective, constraints, expected_method):
    """Prueba un caso y verifica el resultado"""
    result = method_detector.explain_method_choice("", objective, constraints)
    success = result['method'] == expected_method
    
    status = "✅" if success else "❌"
    print(f"{status} {name}")
    print(f"   Esperado: {expected_method.upper()}")
    print(f"   Detectado: {result['method'].upper()}")
    if not success:
        print(f"   Razón: {result['reason']}")
    print()
    
    return success

print("\n" + "=" * 80)
print("TEST COMPLETO: Detección QP vs KKT vs Lagrange (v3.1.0)")
print("=" * 80 + "\n")

results = []

# CASO 1: QP - Tiene igualdad + desigualdades con función cuadrática
print("CASOS QP (función cuadrática + restricciones lineales + AL MENOS UNA IGUALDAD)")
print("-" * 80)

results.append(test_case(
    "Cartera con igualdad",
    "A**2 + B**2 + F**2",
    [
        {'expr': 'A + B + F - 100', 'kind': 'eq'},  # IGUALDAD
        {'expr': 'A - 20', 'kind': 'ge'},
        {'expr': '50 - B', 'kind': 'ge'},
    ],
    'qp'
))

results.append(test_case(
    "Problema con restricción de igualdad",
    "x**2 + y**2",
    [
        {'expr': 'x + y - 100', 'kind': 'eq'},  # IGUALDAD
        {'expr': 'x - 20', 'kind': 'ge'},
    ],
    'qp'
))

# CASO 2: KKT - Solo desigualdades con función cuadrática
print("\nCASOS KKT (función cuadrática + restricciones lineales + SOLO DESIGUALDADES)")
print("-" * 80)

results.append(test_case(
    "Logística solo desigualdades",
    "x**2 + 4*y**2 - 6*x - 8*y + 30",
    [
        {'expr': 'x + y - 20', 'kind': 'le'},  # SOLO DESIGUALDADES
        {'expr': 'x', 'kind': 'ge'},
        {'expr': 'y', 'kind': 'ge'},
    ],
    'kkt'
))

results.append(test_case(
    "Problema solo con cotas",
    "x**2 + y**2",
    [
        {'expr': '20 - x - y', 'kind': 'ge'},  # x + y ≤ 20
        {'expr': 'x', 'kind': 'ge'},           # x ≥ 0
        {'expr': 'y', 'kind': 'ge'},           # y ≥ 0
    ],
    'kkt'
))

# CASO 3: Lagrange - Solo igualdades
print("\nCASOS LAGRANGE (SOLO IGUALDADES)")
print("-" * 80)

results.append(test_case(
    "Solo restricción de igualdad",
    "x**2 + y**2",
    [
        {'expr': 'x + y - 100', 'kind': 'eq'},  # SOLO IGUALDAD
    ],
    'lagrange'
))

results.append(test_case(
    "Múltiples igualdades",
    "x**2 + y**2 + z**2",
    [
        {'expr': 'x + y + z - 100', 'kind': 'eq'},
        {'expr': '2*x + y - 50', 'kind': 'eq'},
    ],
    'lagrange'
))

# CASO 4: KKT - Restricciones NO lineales
print("\nCASOS KKT (RESTRICCIONES NO LINEALES)")
print("-" * 80)

results.append(test_case(
    "Restricción con x²",
    "x**2 + y**2",
    [
        {'expr': 'x**2 + y - 10', 'kind': 'le'},  # NO LINEAL
    ],
    'kkt'
))

# Resumen
print("=" * 80)
print("RESUMEN")
print("=" * 80)
total = len(results)
passed = sum(results)
failed = total - passed

print(f"Total: {total}")
print(f"✅ Pasados: {passed}")
print(f"❌ Fallidos: {failed}")
print()

if failed == 0:
    print("🎉 TODOS LOS TESTS PASARON")
    print("\nCriterios aplicados correctamente:")
    print("  • QP: cuadrática + lineal + AL MENOS UNA IGUALDAD")
    print("  • KKT: cuadrática + lineal + SOLO DESIGUALDADES")
    print("  • Lagrange: cuadrática + SOLO IGUALDADES")
else:
    print("⚠️  HAY TESTS FALLIDOS - Revisar lógica de detección")

print("=" * 80 + "\n")
