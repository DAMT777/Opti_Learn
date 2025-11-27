"""
Test que simula el parsing completo desde texto del usuario
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'opti_learn'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opti_learn.settings')
import django
django.setup()

from opti_app.core import message_parser, method_detector

# El texto EXACTO que el usuario ingresó en la interfaz
user_text = """
Una gestora de inversiones desea construir una cartera óptima combinando tres activos financieros: Acciones (A), Bonos (B) y Fondos de Inversión (F). El objetivo es minimizar el riesgo total de la cartera, medido por la varianza del portafolio, que depende de manera cuadrática de las proporciones invertidas en cada activo.

Modelo de Riesgo: La función de riesgo (varianza) de la cartera se ha modelado como: 

Riesgo = 0.04A² + 0.02B² + 0.03F² + 0.01AB + 0.015AF + 0.005BF 

Donde A, B y F representan las cantidades (en miles de dólares) invertidas en cada activo.

Restricciones operativas: 

Presupuesto total: La inversión total debe ser exactamente de $100,000 (100 mil dólares) 
A + B + F = 100

Rentabilidad mínima: La cartera debe generar un retorno esperado de al menos 7.5 unidades. Los retornos unitarios son: Acciones (0.10), Bonos (0.05), Fondos (0.08) 
0.10A + 0.05B + 0.08F ≥ 7.5

Límites de diversificación: 
Las acciones deben representar al menos el 20% de la cartera: A ≥ 20 
Los bonos no pueden superar el 50% de la cartera: B ≤ 50 
Los fondos deben estar entre 10% y 40%: 10 ≤ F ≤ 40

Restricción de liquidez: Para mantener liquidez, la suma de bonos y fondos debe ser al menos 45 
B + F ≥ 45

Pregunta: Determine las cantidades óptimas a invertir en cada activo (A, B, F) que minimicen el riesgo total de la cartera, cumpliendo todas las restricciones anteriores.
"""

print("\n" + "=" * 80)
print("TEST: Parsing completo del problema de cartera desde texto del usuario")
print("=" * 80 + "\n")

# Parsear el problema
parsed = message_parser.parse_structured_payload(user_text, allow_partial=True)

print("📝 DATOS PARSEADOS:")
print("-" * 80)
print(f"Función objetivo: {parsed.get('objective_expr', 'NO DETECTADA')}")
print(f"Variables: {parsed.get('variables', [])}")
print()
print(f"Restricciones ({len(parsed.get('constraints', []))}):")
for i, c in enumerate(parsed.get('constraints', []), 1):
    raw = c.get('raw', c.get('expr', ''))
    print(f"   {i}. {raw:<50} kind={c['kind']}")
print()

# Analizar con el detector de método
if parsed:
    objective = parsed.get('objective_expr')
    constraints = parsed.get('constraints', [])
    
    print("=" * 80)
    print("ANÁLISIS DE DETECCIÓN DE MÉTODO")
    print("=" * 80 + "\n")
    
    # Verificar estructura
    if objective:
        is_quadratic = method_detector._is_quadratic_objective(objective)
        print(f"¿Función cuadrática? {is_quadratic}")
        print(f"   {objective}")
        print()
    
    if constraints:
        print("¿Restricciones lineales?")
        all_linear = True
        for i, c in enumerate(constraints, 1):
            is_nl = method_detector._is_nonlinear_expression(c['expr'])
            status = "❌ NO LINEAL" if is_nl else "✅ LINEAL"
            if is_nl:
                all_linear = False
            print(f"   {i}. {status}: {c['expr']}")
        print()
        print(f"Todas lineales: {all_linear}")
        print()
    
    # Detectar método
    result = method_detector.explain_method_choice(user_text, objective, constraints)
    
    print("=" * 80)
    print(f"🎯 MÉTODO DETECTADO: {result['method'].upper()}")
    print("=" * 80)
    print(f"📝 Razón: {result['reason']}")
    print(f"📏 Regla: {result['rule_applied']}")
    print()
    
    if result['method'] == 'qp':
        print("✅ CORRECTO: Se detectó como QP")
    else:
        print(f"❌ ERROR: Se esperaba 'qp' pero se obtuvo '{result['method']}'")
        print()
        print("DIAGNÓSTICO:")
        if not objective:
            print("   - No se detectó función objetivo")
        elif not method_detector._is_quadratic_objective(objective):
            print("   - La función objetivo no se reconoció como cuadrática")
        
        if not constraints:
            print("   - No se detectaron restricciones")
        elif method_detector._has_nonlinear_constraints(constraints):
            print("   - Se detectaron restricciones no lineales (falso positivo)")
        elif not method_detector._has_only_linear_constraints(constraints):
            print("   - No todas las restricciones son lineales")

else:
    print("❌ ERROR: No se pudo parsear el problema")

print("\n" + "=" * 80 + "\n")
