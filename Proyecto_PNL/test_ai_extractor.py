"""
Test directo del AI Extractor para ver qué JSON está generando
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'opti_learn'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opti_learn.settings')
import django
django.setup()

# Importar después de django.setup()
from opti_app.consumers_ai import _extract_payload_with_ai

# El texto del problema
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
print("TEST: AI Extractor (Groq)")
print("=" * 80 + "\n")

print("Llamando al AI Extractor...")
result = _extract_payload_with_ai(user_text)

if result:
    print("\n[OK] AI EXTRACTOR RESPONDIO\n")
    print("JSON completo:")
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n" + "=" * 80)
    print("ANÁLISIS DEL RESULTADO")
    print("=" * 80)
    
    print(f"\nFuncion objetivo: {result.get('objective_expr', 'NO DETECTADA')}")
    print(f"Variables: {result.get('variables', [])}")
    print(f"Metodo: {result.get('method', 'NO DETECTADO')}")
    
    constraints = result.get('constraints', [])
    print(f"\nRestricciones ({len(constraints)}):")
    for i, c in enumerate(constraints, 1):
        print(f"   {i}. [{c.get('kind')}] {c.get('expr')}")
    
    # Verificar estructura QP
    eq_count = sum(1 for c in constraints if c.get('kind') == 'eq')
    ge_count = sum(1 for c in constraints if c.get('kind') == 'ge')
    le_count = sum(1 for c in constraints if c.get('kind') == 'le')
    
    print(f"\nRESUMEN:")
    print(f"   - Igualdades (eq): {eq_count}")
    print(f"   - Mayor o igual (ge): {ge_count}")
    print(f"   - Menor o igual (le): {le_count}")
    print(f"   - TOTAL: {len(constraints)}")
    
    print(f"\nMetodo detectado: {result.get('method', 'NONE')}")
    
    if result.get('method') == 'qp':
        print("   [OK] CORRECTO: Detecto QP")
    elif result.get('method') == 'lagrange':
        print("   [ERROR] Detecto Lagrange (deberia ser QP)")
        print("   Causa: Probablemente no extrajo todas las desigualdades")
    elif result.get('method') == 'kkt':
        print("   [ERROR] Detecto KKT (deberia ser QP)")
        print("   Causa: Probablemente no reconocio la funcion cuadratica")
    else:
        print(f"   [ERROR] Detecto {result.get('method')}")
    
    # Verificación
    print("\n" + "=" * 80)
    print("VERIFICACIÓN")
    print("=" * 80)
    
    if len(constraints) < 7:
        print(f"[ERROR] Faltan restricciones: Se esperaban 7, se obtuvieron {len(constraints)}")
        print("   Restricciones faltantes:")
        if eq_count == 0:
            print("   - A + B + F = 100 (igualdad)")
        if ge_count < 5:
            print(f"   - Faltan {5 - ge_count} restricciones '>='")
        if le_count < 2:
            print(f"   - Faltan {2 - le_count} restricciones '<='")
    else:
        print(f"[OK] Restricciones completas: {len(constraints)}")
    
    if not result.get('objective_expr') or 'A**2' not in result.get('objective_expr', ''):
        print("[ERROR] Funcion objetivo mal parseada")
        print(f"   Se obtuvo: {result.get('objective_expr')}")
        print("   Se esperaba algo como: 0.04*A**2 + 0.02*B**2 + 0.03*F**2 + ...")
    else:
        print("[OK] Funcion objetivo bien parseada")
        
else:
    print("\n[ERROR] AI EXTRACTOR NO RESPONDIO")
    print("   Posibles causas:")
    print("   - Error de conexión con Groq")
    print("   - API key inválida")
    print("   - El AI respondió con texto en lugar de JSON")
    print("   - Token limit excedido")

print("\n" + "=" * 80 + "\n")
