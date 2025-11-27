"""
Test final del solver KKT - Verificación completa.
"""
import sys
import io

# Configurar salida UTF-8 en Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'opti_learn')

from opti_app.core.solver_kkt import KKTSolver


def test_problema_cartera():
    """
    Problema de cartera simplificado con KKT.
    min f(A,B) = 0.04*A² + 0.02*B² + 0.01*A*B
    s.a: A + B = 100
         A >= 20
         B >= 50
    """
    print("=" * 80)
    print("TEST FINAL KKT - Problema de Cartera Simplificado")
    print("=" * 80)
    print()
    
    solver = KKTSolver(
        objective_expr="0.04*A**2 + 0.02*B**2 + 0.01*A*B",
        variables=["A", "B"],
        constraints=[
            {"expression": "A + B - 100", "rhs": 0, "kind": "eq"},
            {"expression": "A - 20", "rhs": 0, "kind": "ge"},
            {"expression": "B - 50", "rhs": 0, "kind": "ge"}
        ],
        is_maximization=False
    )
    
    result = solver.solve()
    
    if result['status'] == 'success':
        print("✅ RESULTADO:")
        print(f"Variables: {result['solution']}")
        print(f"Riesgo mínimo: {result['optimal_value']:.4f}")
        print(f"Candidatos evaluados: {len(result['candidates'])}")
        print()
        
        # Guardar explicación
        with open('solucion_kkt_cartera.md', 'w', encoding='utf-8') as f:
            f.write(result['explanation'])
        
        print("📄 Explicación completa guardada en: solucion_kkt_cartera.md")
        print()
        
        # Mostrar primeros 1500 caracteres de la explicación
        print("EXPLICACIÓN (primeros 1500 caracteres):")
        print("=" * 80)
        print(result['explanation'][:1500])
        print("...")
        print()
        
    else:
        print("❌ ERROR:")
        print(result.get('message', 'Unknown error'))
        if 'traceback' in result:
            print(result['traceback'])


def test_problema_geometrico():
    """
    Problema geométrico clásico:
    min f(x,y) = x² + y²
    s.a: x + y >= 2
         x >= 0
         y >= 0
    """
    print("=" * 80)
    print("TEST FINAL KKT - Problema Geométrico")
    print("=" * 80)
    print()
    
    solver = KKTSolver(
        objective_expr="x**2 + y**2",
        variables=["x", "y"],
        constraints=[
            {"expression": "x + y - 2", "rhs": 0, "kind": "ge"},
            {"expression": "x", "rhs": 0, "kind": "ge"},
            {"expression": "y", "rhs": 0, "kind": "ge"}
        ],
        is_maximization=False
    )
    
    result = solver.solve()
    
    if result['status'] == 'success':
        print("✅ RESULTADO:")
        print(f"Variables: {result['solution']}")
        print(f"Valor óptimo: {result['optimal_value']:.6f}")
        print(f"Candidatos evaluados: {len(result['candidates'])}")
        print()
        
        # Verificar solución esperada (x=1, y=1, f=2)
        x_opt = result['solution'].get('x', 0)
        y_opt = result['solution'].get('y', 0)
        f_opt = result['optimal_value']
        
        if abs(x_opt - 1.0) < 0.01 and abs(y_opt - 1.0) < 0.01 and abs(f_opt - 2.0) < 0.01:
            print("✅ VERIFICACIÓN: Solución coincide con el óptimo esperado (x=1, y=1, f=2)")
        else:
            print(f"⚠️  ADVERTENCIA: Solución difiere del esperado")
            print(f"   Esperado: x=1, y=1, f=2")
            print(f"   Obtenido: x={x_opt:.6f}, y={y_opt:.6f}, f={f_opt:.6f}")
        
        print()
        
        # Guardar explicación
        with open('solucion_kkt_geometrico.md', 'w', encoding='utf-8') as f:
            f.write(result['explanation'])
        
        print("📄 Explicación guardada en: solucion_kkt_geometrico.md")
        
    else:
        print("❌ ERROR:")
        print(result.get('message', 'Unknown error'))
        if 'traceback' in result:
            print(result['traceback'])


def test_problema_negocio():
    """
    Problema de maximización de beneficio:
    max B(x,y) = 60x + 50y
    s.a: 3x + 2y <= 120 (horas disponibles)
         x + 2y <= 80  (materiales)
         x >= 0, y >= 0
    """
    print()
    print("=" * 80)
    print("TEST FINAL KKT - Maximización de Beneficio")
    print("=" * 80)
    print()
    
    solver = KKTSolver(
        objective_expr="60*x + 50*y",
        variables=["x", "y"],
        constraints=[
            {"expression": "3*x + 2*y - 120", "rhs": 0, "kind": "le"},
            {"expression": "x + 2*y - 80", "rhs": 0, "kind": "le"},
            {"expression": "-x", "rhs": 0, "kind": "le"},
            {"expression": "-y", "rhs": 0, "kind": "le"}
        ],
        is_maximization=True
    )
    
    result = solver.solve()
    
    if result['status'] == 'success':
        print("✅ RESULTADO:")
        print(f"Variables: {result['solution']}")
        print(f"Beneficio máximo: ${result['optimal_value']:.2f}")
        print(f"Candidatos evaluados: {len(result['candidates'])}")
        print()
        
        # Mostrar restricciones activas
        best = result.get('candidates', [{}])[0]
        active = best.get('active_constraints', [])
        if active:
            print(f"Restricciones activas: {active}")
            print()
        
        # Guardar explicación
        with open('solucion_kkt_negocio.md', 'w', encoding='utf-8') as f:
            f.write(result['explanation'])
        
        print("📄 Explicación guardada en: solucion_kkt_negocio.md")
        
    else:
        print("❌ ERROR:")
        print(result.get('message', 'Unknown error'))


if __name__ == "__main__":
    test_problema_cartera()
    print("\n\n")
    test_problema_geometrico()
    print("\n\n")
    test_problema_negocio()
    
    print()
    print("=" * 80)
    print("✅ TODOS LOS TESTS FINALES COMPLETADOS")
    print("=" * 80)
    print()
    print("Archivos generados:")
    print("  - solucion_kkt_cartera.md")
    print("  - solucion_kkt_geometrico.md")
    print("  - solucion_kkt_negocio.md")
