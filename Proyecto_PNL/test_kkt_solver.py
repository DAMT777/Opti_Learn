"""
Test del solver KKT con un problema clásico.
"""
import sys
sys.path.insert(0, 'opti_learn')

from opti_app.core.solver_kkt import KKTSolver

def test_problema_simple():
    """
    Problema clásico:
    min f(x,y) = x² + y²
    s.a: x + y = 1
    """
    print("=" * 80)
    print("TEST 1: Problema con restricción de igualdad")
    print("=" * 80)
    print()
    
    solver = KKTSolver(
        objective_expr="x**2 + y**2",
        variables=["x", "y"],
        constraints=[
            {"expression": "x + y", "rhs": 1, "kind": "eq"}
        ],
        is_maximization=False
    )
    
    result = solver.solve()
    
    if result['status'] == 'success':
        print("✅ RESULTADO:")
        print(f"Variables: {result['solution']}")
        print(f"Valor óptimo: {result['optimal_value']}")
        print()
        print("EXPLICACIÓN COMPLETA:")
        print(result['explanation'])
        
        # Guardar explicación
        with open('solucion_kkt_simple.md', 'w', encoding='utf-8') as f:
            f.write(result['explanation'])
        print()
        print("📄 Explicación guardada en: solucion_kkt_simple.md")
    else:
        print("❌ ERROR:")
        print(result.get('message', 'Unknown error'))
        if 'traceback' in result:
            print(result['traceback'])


def test_problema_desigualdades():
    """
    Problema con desigualdades:
    min f(x,y) = (x-2)² + (y-2)²
    s.a: x + y <= 2
         x >= 0
         y >= 0
    """
    print()
    print("=" * 80)
    print("TEST 2: Problema con desigualdades")
    print("=" * 80)
    print()
    
    solver = KKTSolver(
        objective_expr="(x-2)**2 + (y-2)**2",
        variables=["x", "y"],
        constraints=[
            {"expression": "x + y - 2", "rhs": 0, "kind": "le"},  # x + y <= 2
            {"expression": "-x", "rhs": 0, "kind": "le"},         # x >= 0
            {"expression": "-y", "rhs": 0, "kind": "le"}          # y >= 0
        ],
        is_maximization=False
    )
    
    result = solver.solve()
    
    if result['status'] == 'success':
        print("✅ RESULTADO:")
        print(f"Variables: {result['solution']}")
        print(f"Valor óptimo: {result['optimal_value']}")
        print(f"Candidatos válidos: {len(result['candidates'])}")
        print()
        
        # Guardar explicación
        with open('solucion_kkt_desigualdades.md', 'w', encoding='utf-8') as f:
            f.write(result['explanation'])
        print("📄 Explicación guardada en: solucion_kkt_desigualdades.md")
    else:
        print("❌ ERROR:")
        print(result.get('message', 'Unknown error'))
        if 'traceback' in result:
            print(result['traceback'])


def test_problema_produccion():
    """
    Problema de producción:
    max P = 40x + 30y (beneficio)
    s.a: 2x + y <= 100 (recurso A)
         x + 2y <= 80  (recurso B)
         x >= 0, y >= 0
    """
    print()
    print("=" * 80)
    print("TEST 3: Problema de producción (maximización)")
    print("=" * 80)
    print()
    
    solver = KKTSolver(
        objective_expr="40*x + 30*y",
        variables=["x", "y"],
        constraints=[
            {"expression": "2*x + y - 100", "rhs": 0, "kind": "le"},
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
        print(f"Beneficio máximo: {result['optimal_value']}")
        print(f"Candidatos evaluados: {len(result['candidates'])}")
        print()
        
        # Guardar explicación
        with open('solucion_kkt_produccion.md', 'w', encoding='utf-8') as f:
            f.write(result['explanation'])
        print("📄 Explicación guardada en: solucion_kkt_produccion.md")
    else:
        print("❌ ERROR:")
        print(result.get('message', 'Unknown error'))
        if 'traceback' in result:
            print(result['traceback'])


if __name__ == "__main__":
    test_problema_simple()
    test_problema_desigualdades()
    test_problema_produccion()
    
    print()
    print("=" * 80)
    print("✅ TESTS COMPLETADOS")
    print("=" * 80)
