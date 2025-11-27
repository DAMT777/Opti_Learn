"""
Test para verificar las mejoras y correcciones del solver QP
Verifica:
1. Conteo correcto de variables λ y μ
2. Ausencia de holguras cuando no hay desigualdades
3. Estructura pedagógica con bloques temáticos
4. Transiciones lúdicas
5. Micro-resúmenes
6. Notas pedagógicas
7. Dimensiones de matrices
8. Interpretación mejorada
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'opti_learn'))

from opti_app.core.solver_qp_numerical import solve_qp
import json


def test_problema_solo_igualdades():
    """Prueba con problema que solo tiene restricciones de igualdad (sin desigualdades)"""
    
    print("\n" + "="*80)
    print("TEST: Problema SOLO con restricciones de IGUALDAD")
    print("="*80 + "\n")
    
    # Problema: min x1^2 + x2^2 + x3^2
    # s.a. x1 + x2 + x3 = 1
    #      x1, x2, x3 >= 0
    
    objective_expr = "x1**2 + x2**2 + x3**2"
    variables = ["x1", "x2", "x3"]
    constraints = [
        {'expr': 'x1 + x2 + x3', 'kind': 'eq', 'rhs': 1.0}
    ]
    
    result = solve_qp(objective_expr, variables, constraints)
    
    print(f"[STATUS] {result['status']}")
    print(f"[PASOS] {len(result['steps'])} pasos generados")
    
    # Verificar conteo de variables
    step4 = result['steps'][3]  # Paso 4: KKT
    vars_totales = step4['contenido']['variables_totales']
    n_eq = step4['contenido']['n_eq']
    n_ineq = step4['contenido']['n_ineq']
    
    print(f"\n[VERIFICACIÓN 1] Conteo de restricciones:")
    print(f"  - Igualdades (n_eq): {n_eq} (esperado: 1) ✓" if n_eq == 1 else f"  - ERROR: n_eq={n_eq}")
    print(f"  - Desigualdades (n_ineq): {n_ineq} (esperado: 0) ✓" if n_ineq == 0 else f"  - ERROR: n_ineq={n_ineq}")
    
    print(f"\n[VERIFICACIÓN 2] Conteo de variables KKT:")
    print(f"  - Variables x: {vars_totales['x']} (esperado: 3) ✓" if vars_totales['x'] == 3 else f"  - ERROR: x={vars_totales['x']}")
    print(f"  - Multiplicadores λ: {vars_totales['lambda']} (esperado: 1) ✓" if vars_totales['lambda'] == 1 else f"  - ERROR: λ={vars_totales['lambda']}")
    print(f"  - Multiplicadores μ: {vars_totales['mu']} (esperado: 3) ✓" if vars_totales['mu'] == 3 else f"  - ERROR: μ={vars_totales['mu']}")
    
    # Verificar ausencia de holguras
    step5 = result['steps'][4]  # Paso 5: Preparación
    variables_sistema = step5['contenido']['variables']
    
    print(f"\n[VERIFICACIÓN 3] Variables del sistema:")
    tiene_holguras = 'holguras (S)' in variables_sistema
    print(f"  - ¿Tiene holguras S?: {'SÍ (ERROR!)' if tiene_holguras else 'NO ✓'}")
    tiene_artificiales = 'artificiales (R)' in variables_sistema
    print(f"  - ¿Tiene artificiales R?: {'SÍ ✓' if tiene_artificiales else 'NO (ERROR!)'}")
    
    # Verificar nota pedagógica
    tiene_nota = 'nota_pedagogica' in step5['contenido']
    print(f"\n[VERIFICACIÓN 4] Nota pedagógica presente: {'SÍ ✓' if tiene_nota else 'NO (ERROR!)'}")
    if tiene_nota:
        print(f"  - Contenido: {step5['contenido']['nota_pedagogica'][:100]}...")
    
    # Verificar dimensiones de matrices
    step2 = result['steps'][1]  # Paso 2: Matrices
    explicacion = result['explanation']
    
    tiene_dimensiones = 'Dimensiones detectadas' in explicacion or 'R^' in explicacion
    print(f"\n[VERIFICACIÓN 5] Dimensiones de matrices mostradas: {'SÍ ✓' if tiene_dimensiones else 'NO (ERROR!)'}")
    
    # Verificar bloques temáticos
    bloques = ['🟦 PRESENTACION', '🟩 DETECCION', '🟨 ANALISIS', '🟥 CONSTRUCCION', 
               '🟪 PREPARACION', '🟫 FASE I', '🟧 FASE II', '🟩 SOLUCION FINAL']
    
    print(f"\n[VERIFICACIÓN 6] Bloques temáticos con colores:")
    for bloque in bloques:
        presente = bloque in explicacion
        print(f"  - {bloque}: {'✓' if presente else '✗'}")
    
    # Verificar transiciones lúdicas
    transiciones = ['🎯 **Siguiente paso**', '✨ **Preparando', '🔍 **Analizando']
    print(f"\n[VERIFICACIÓN 7] Transiciones lúdicas:")
    for trans in transiciones:
        presente = trans in explicacion
        print(f"  - {trans}: {'✓' if presente else '✗'}")
    
    # Verificar micro-resúmenes
    tiene_micro_resumenes = '🧩 **Resumen' in explicacion
    print(f"\n[VERIFICACIÓN 8] Micro-resúmenes después de cada fase: {'SÍ ✓' if tiene_micro_resumenes else 'NO (ERROR!)'}")
    
    # Verificar notas pedagógicas en explicación
    tiene_notas = '📚 NOTAS PEDAGOGICAS' in explicacion
    print(f"\n[VERIFICACIÓN 9] Sección de notas pedagógicas: {'SÍ ✓' if tiene_notas else 'NO (ERROR!)'}")
    
    # Verificar interpretación mejorada
    step8 = result['steps'][7]  # Paso 8: Solución
    interpretacion = step8['contenido']['interpretacion']
    tiene_contexto = '💡' in interpretacion or 'significa' in interpretacion.lower()
    print(f"\n[VERIFICACIÓN 10] Interpretación con contexto real: {'SÍ ✓' if tiene_contexto else 'NO (ERROR!)'}")
    
    # Verificar JSON serializable
    try:
        json_str = json.dumps(result)
        print(f"\n[VERIFICACIÓN 11] JSON serializable: SÍ ✓ ({len(json_str)} caracteres)")
    except Exception as e:
        print(f"\n[VERIFICACIÓN 11] JSON serializable: NO (ERROR!) - {e}")
    
    # Guardar resultado
    with open('output_qp_mejoras.md', 'w', encoding='utf-8') as f:
        f.write(explicacion)
    
    print(f"\n[ARCHIVO] Explicación guardada en 'output_qp_mejoras.md'")
    print(f"[TAMAÑO] {len(explicacion)} caracteres")
    
    return result


def test_problema_con_desigualdades():
    """Prueba con problema que tiene igualdades Y desigualdades"""
    
    print("\n" + "="*80)
    print("TEST: Problema con IGUALDADES y DESIGUALDADES")
    print("="*80 + "\n")
    
    # Problema: min x1^2 + 2*x2^2
    # s.a. x1 + x2 = 1      (igualdad)
    #      2*x1 + x2 <= 3   (desigualdad)
    #      x1, x2 >= 0
    
    objective_expr = "x1**2 + 2*x2**2"
    variables = ["x1", "x2"]
    constraints = [
        {'expr': 'x1 + x2', 'kind': 'eq', 'rhs': 1.0},
        {'expr': '2*x1 + x2', 'kind': 'ineq', 'rhs': 3.0}
    ]
    
    result = solve_qp(objective_expr, variables, constraints)
    
    print(f"[STATUS] {result['status']}")
    
    # Verificar conteo de variables
    step4 = result['steps'][3]
    vars_totales = step4['contenido']['variables_totales']
    n_eq = step4['contenido']['n_eq']
    n_ineq = step4['contenido']['n_ineq']
    
    print(f"\n[VERIFICACIÓN] Conteo de restricciones:")
    print(f"  - Igualdades: {n_eq} (esperado: 1) ✓" if n_eq == 1 else f"  - ERROR: n_eq={n_eq}")
    print(f"  - Desigualdades: {n_ineq} (esperado: 1) ✓" if n_ineq == 1 else f"  - ERROR: n_ineq={n_ineq}")
    
    print(f"\n[VERIFICACIÓN] Variables KKT:")
    print(f"  - λ (restricciones): {vars_totales['lambda']} (esperado: 2) ✓" if vars_totales['lambda'] == 2 else f"  - ERROR")
    
    # Verificar presencia de holguras
    step5 = result['steps'][4]
    variables_sistema = step5['contenido']['variables']
    
    print(f"\n[VERIFICACIÓN] Variables del sistema:")
    tiene_holguras = 'holguras (S)' in variables_sistema
    print(f"  - ¿Tiene holguras S?: {'SÍ ✓' if tiene_holguras else 'NO (ERROR!)'}")
    tiene_artificiales = 'artificiales (R)' in variables_sistema
    print(f"  - ¿Tiene artificiales R?: {'SÍ ✓' if tiene_artificiales else 'NO (ERROR!)'}")
    
    return result


if __name__ == "__main__":
    print("\n" + "🎮"*40)
    print("SUITE DE TESTS - MEJORAS SOLVER QP")
    print("🎮"*40 + "\n")
    
    # Test 1: Solo igualdades
    result1 = test_problema_solo_igualdades()
    
    # Test 2: Igualdades + Desigualdades
    result2 = test_problema_con_desigualdades()
    
    print("\n" + "="*80)
    print("✅ TODOS LOS TESTS COMPLETADOS")
    print("="*80 + "\n")
