"""
Test de integración del solver KKT con el sistema completo.
Simula el flujo desde la entrada del usuario hasta la solución.
"""
import sys
sys.path.insert(0, 'opti_learn')

from opti_app.core.method_detector import determine_method
from opti_app.consumers_ai import solve_kkt_payload


def test_integracion_kkt_simple():
    """Test con problema simple de KKT."""
    print("=" * 80)
    print("TEST INTEGRACIÓN KKT - Problema Simple")
    print("=" * 80)
    print()
    
    # Problema del usuario
    texto_usuario = """
    Minimizar f(x,y) = x² + y²
    Sujeto a: x + y = 1
    """
    
    # Parsear problema (simulado - normalmente vendría del AI)
    problema = {
        'objective_expr': 'x**2 + y**2',
        'is_maximization': False,
        'constraints': [
            {'expr': 'x + y - 1', 'rhs': 0, 'kind': 'eq'}
        ]
    }
    
    meta = {
        'variables': ['x', 'y']
    }
    
    # Detectar método
    metodo_info = determine_method(
        objective_expr=problema['objective_expr'],
        constraints=problema['constraints'],
        variables=meta['variables']
    )
    
    print(f"Método detectado: {metodo_info['method']}")
    print(f"Razón: {metodo_info['explanation']['reason']}")
    print()
    
    # Recomendación
    recomendacion = {
        'rationale': metodo_info['explanation']['reason'],
        'rule': metodo_info['explanation']['rule_applied']
    }
    
    # Resolver con KKT
    payload = {}
    resultado_texto, resultado_data = solve_kkt_payload(
        payload=payload,
        problema=problema,
        meta=meta,
        recomendacion=recomendacion,
        method_note="🎯 Problema resuelto con condiciones KKT analíticas"
    )
    
    print("RESULTADO:")
    print(resultado_texto)
    print()
    print("=" * 80)
    
    # Guardar salida
    with open('test_kkt_integracion_simple.md', 'w', encoding='utf-8') as f:
        f.write(resultado_texto)
    print("📄 Salida guardada en: test_kkt_integracion_simple.md")


def test_integracion_kkt_desigualdades():
    """Test con problema con desigualdades."""
    print()
    print("=" * 80)
    print("TEST INTEGRACIÓN KKT - Problema con Desigualdades")
    print("=" * 80)
    print()
    
    # Problema del usuario
    texto_usuario = """
    Minimizar f(x,y) = (x-3)² + (y-3)²
    Sujeto a:
        x + y <= 4
        x >= 0
        y >= 0
    """
    
    # Parsear problema
    problema = {
        'objective_expr': '(x-3)**2 + (y-3)**2',
        'is_maximization': False,
        'constraints': [
            {'expr': 'x + y - 4', 'rhs': 0, 'kind': 'le'},
            {'expr': '-x', 'rhs': 0, 'kind': 'le'},  # x >= 0 -> -x <= 0
            {'expr': '-y', 'rhs': 0, 'kind': 'le'}   # y >= 0 -> -y <= 0
        ]
    }
    
    meta = {
        'variables': ['x', 'y']
    }
    
    # Detectar método
    metodo_info = determine_method(
        objective_expr=problema['objective_expr'],
        constraints=problema['constraints'],
        variables=meta['variables']
    )
    
    print(f"Método detectado: {metodo_info['method']}")
    print(f"Razón: {metodo_info['explanation']['reason']}")
    print()
    
    # Recomendación
    recomendacion = {
        'rationale': metodo_info['explanation']['reason'],
        'rule': metodo_info['explanation']['rule_applied']
    }
    
    # Resolver con KKT
    payload = {}
    resultado_texto, resultado_data = solve_kkt_payload(
        payload=payload,
        problema=problema,
        meta=meta,
        recomendacion=recomendacion,
        method_note=None
    )
    
    print("RESULTADO:")
    print(resultado_texto[:1000])  # Primeros 1000 caracteres
    print("...")
    print()
    
    # Mostrar solución
    solver_info = resultado_data.get('solver', {})
    if solver_info.get('status') == 'success':
        sol = solver_info.get('solution', {})
        print("✅ SOLUCIÓN ÓPTIMA:")
        for var, val in sol.items():
            print(f"  {var} = {val:.6f}")
        print(f"  f(x*) = {solver_info.get('optimal_value', 'N/A'):.6f}")
        print(f"  Candidatos evaluados: {len(solver_info.get('candidates', []))}")
    
    print()
    print("=" * 80)
    
    # Guardar salida
    with open('test_kkt_integracion_desigualdades.md', 'w', encoding='utf-8') as f:
        f.write(resultado_texto)
    print("📄 Salida guardada en: test_kkt_integracion_desigualdades.md")


def test_integracion_kkt_maximizacion():
    """Test con problema de maximización."""
    print()
    print("=" * 80)
    print("TEST INTEGRACIÓN KKT - Maximización")
    print("=" * 80)
    print()
    
    # Problema del usuario
    texto_usuario = """
    Maximizar beneficio: B(x,y) = 50x + 40y
    Sujeto a:
        2x + y <= 100 (recurso A)
        x + 2y <= 80  (recurso B)
        x >= 0, y >= 0
    """
    
    # Parsear problema
    problema = {
        'objective_expr': '50*x + 40*y',
        'is_maximization': True,
        'constraints': [
            {'expr': '2*x + y - 100', 'rhs': 0, 'kind': 'le'},
            {'expr': 'x + 2*y - 80', 'rhs': 0, 'kind': 'le'},
            {'expr': '-x', 'rhs': 0, 'kind': 'le'},
            {'expr': '-y', 'rhs': 0, 'kind': 'le'}
        ]
    }
    
    meta = {
        'variables': ['x', 'y']
    }
    
    # Resolver con KKT
    recomendacion = {
        'rationale': 'Problema lineal con restricciones - KKT aplicable',
        'rule': 5
    }
    
    payload = {}
    resultado_texto, resultado_data = solve_kkt_payload(
        payload=payload,
        problema=problema,
        meta=meta,
        recomendacion=recomendacion,
        method_note="🎯 Problema de optimización lineal resuelto con KKT"
    )
    
    # Mostrar solución
    solver_info = resultado_data.get('solver', {})
    if solver_info.get('status') == 'success':
        sol = solver_info.get('solution', {})
        print("✅ SOLUCIÓN ÓPTIMA:")
        for var, val in sol.items():
            print(f"  {var} = {val:.6f}")
        print(f"  Beneficio máximo: ${solver_info.get('optimal_value', 'N/A'):.2f}")
        print(f"  Candidatos evaluados: {len(solver_info.get('candidates', []))}")
    
    print()
    print("=" * 80)
    
    # Guardar salida
    with open('test_kkt_integracion_maximizacion.md', 'w', encoding='utf-8') as f:
        f.write(resultado_texto)
    print("📄 Salida guardada en: test_kkt_integracion_maximizacion.md")


if __name__ == "__main__":
    test_integracion_kkt_simple()
    test_integracion_kkt_desigualdades()
    test_integracion_kkt_maximizacion()
    
    print()
    print("=" * 80)
    print("✅ TESTS DE INTEGRACIÓN COMPLETADOS")
    print("=" * 80)
