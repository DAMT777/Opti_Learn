"""Test con problemas QP explícitos"""

import sys
sys.path.insert(0, 'opti_learn')

from opti_app.core.message_parser import parse_and_determine_method

# Test 1: Problema que menciona QP explícitamente
problema_qp_explicito = """
Resolver el siguiente problema de Programación Cuadrática (QP):

Minimizar f(x,y) = x² + y²
sujeto a:
x + y = 100
20 ≤ x ≤ 70
y ≤ 60
0.25*x + 0.35*y ≥ 28
x ≤ 65
y ≤ 65
"""

# Test 2: Mismo problema SIN mencionar QP (debería ser KKT)
problema_sin_mencionar_qp = """
Minimizar f(x,y) = x² + y²
sujeto a:
x + y = 100
20 ≤ x ≤ 70
y ≤ 60
"""

# Test 3: Solo desigualdades con cuadrática (debería ser KKT)
problema_kkt_puro = """
Minimizar C(x,y) = x² + 4y² - 6x - 8y + 30
sujeto a:
x + y ≤ 20
x ≥ 0
y ≥ 0
"""

print("="*80)
print("TEST 1: Menciona QP explícitamente")
print("="*80)
resultado1 = parse_and_determine_method(problema_qp_explicito)
if resultado1:
    print(f"Método: {resultado1['method']}")
    print(f"Razón: {resultado1['method_explanation']['reason']}")
    print(f"Regla: {resultado1['method_explanation']['rule_applied']}")
else:
    print("No se pudo parsear")

print("\n" + "="*80)
print("TEST 2: NO menciona QP (debería ser KKT)")
print("="*80)
resultado2 = parse_and_determine_method(problema_sin_mencionar_qp)
if resultado2:
    print(f"Método: {resultado2['method']}")
    print(f"Razón: {resultado2['method_explanation']['reason']}")
    print(f"Regla: {resultado2['method_explanation']['rule_applied']}")
else:
    print("No se pudo parsear")

print("\n" + "="*80)
print("TEST 3: KKT puro (solo desigualdades)")
print("="*80)
resultado3 = parse_and_determine_method(problema_kkt_puro)
if resultado3:
    print(f"Método: {resultado3['method']}")
    print(f"Razón: {resultado3['method_explanation']['reason']}")
    print(f"Regla: {resultado3['method_explanation']['rule_applied']}")
else:
    print("No se pudo parsear")
