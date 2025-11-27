"""
Test específico para verificar que el problema de alimentos balanceados 
se detecta correctamente como QP después de la corrección v3.0.0
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'opti_learn'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opti_learn.settings')
import django
django.setup()

from opti_app.core import method_detector

def test_alimentos_balanceados():
    """
    Test del problema de alimentos balanceados.
    
    Debe detectarse como QP porque:
    - Función objetivo: x² + y² (cuadrática)
    - Restricciones: todas lineales
    """
    
    objective = "x**2 + y**2"
    
    constraints = [
        {'expr': 'x + y - 100', 'kind': 'eq'},           # x + y = 100
        {'expr': 'x - 20', 'kind': 'ge'},                # x ≥ 20
        {'expr': '70 - x', 'kind': 'ge'},                # x ≤ 70
        {'expr': '60 - y', 'kind': 'ge'},                # y ≤ 60
        {'expr': '0.25*x + 0.35*y - 28', 'kind': 'ge'},  # proteína ≥ 28
        {'expr': '65 - x', 'kind': 'ge'},                # x ≤ 65%
        {'expr': '65 - y', 'kind': 'ge'},                # y ≤ 65%
    ]
    
    result = method_detector.explain_method_choice("", objective, constraints)
    
    print("\n" + "=" * 80)
    print("TEST: Problema de Alimentos Balanceados (v3.0.0)")
    print("=" * 80 + "\n")
    
    print("📊 Estructura del problema:")
    print(f"   Función objetivo: {objective}")
    print(f"   Número de restricciones: {len(constraints)}")
    print()
    
    # Verificar que función es cuadrática
    is_quadratic = method_detector._is_quadratic_objective(objective)
    print(f"   ¿Función cuadrática? {'✅ SÍ' if is_quadratic else '❌ NO'}")
    
    # Verificar que restricciones son lineales
    all_linear = method_detector._has_only_linear_constraints(constraints)
    print(f"   ¿Todas restricciones lineales? {'✅ SÍ' if all_linear else '❌ NO'}")
    print()
    
    print("=" * 80)
    print(f"🎯 MÉTODO DETECTADO: {result['method'].upper()}")
    print("=" * 80)
    print()
    print(f"📝 Razón: {result['reason']}")
    print(f"📏 Regla aplicada: {result['rule_applied']}")
    print()
    
    # Verificar resultado
    expected = 'qp'
    success = result['method'] == expected
    
    if success:
        print("✅ TEST PASADO: El problema se detectó correctamente como QP")
        print()
        print("   Esto confirma que la corrección v3.0.0 funciona:")
        print("   - Detecta QP por estructura matemática")
        print("   - No requiere mención explícita de 'QP'")
        print("   - Captura problemas cuadráticos lineales correctamente")
    else:
        print(f"❌ TEST FALLIDO: Se esperaba '{expected}' pero se obtuvo '{result['method']}'")
    
    print("\n" + "=" * 80 + "\n")
    
    return success


def test_problema_no_lineal():
    """
    Test de control: problema con restricción no lineal debe ser KKT.
    """
    
    objective = "x**2 + y**2"
    constraints = [
        {'expr': 'x**2 + y - 10', 'kind': 'le'},  # Restricción NO lineal
    ]
    
    result = method_detector.explain_method_choice("", objective, constraints)
    
    print("TEST DE CONTROL: Restricción No Lineal")
    print("-" * 80)
    print(f"   Función: {objective}")
    print(f"   Restricción: x² + y ≤ 10 (NO LINEAL)")
    print()
    print(f"   Método detectado: {result['method'].upper()}")
    print(f"   Esperado: KKT")
    
    success = result['method'] == 'kkt'
    status = "✅ CORRECTO" if success else "❌ ERROR"
    print(f"   {status}")
    print()
    
    return success


if __name__ == '__main__':
    print("\n" + "🧪 EJECUTANDO TESTS DE DETECCIÓN QP v3.0.0" + "\n")
    
    test1 = test_alimentos_balanceados()
    test2 = test_problema_no_lineal()
    
    print("\n" + "=" * 80)
    print("RESUMEN DE TESTS")
    print("=" * 80)
    print(f"   Test 1 (Alimentos → QP):  {'✅ PASADO' if test1 else '❌ FALLIDO'}")
    print(f"   Test 2 (No lineal → KKT): {'✅ PASADO' if test2 else '❌ FALLIDO'}")
    print()
    
    if test1 and test2:
        print("🎉 TODOS LOS TESTS PASARON")
        print("   La corrección v3.0.0 funciona correctamente.")
    else:
        print("⚠️  ALGUNOS TESTS FALLARON")
        print("   Revisar la implementación.")
    
    print("=" * 80 + "\n")
