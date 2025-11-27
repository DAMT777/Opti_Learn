"""
Test del solver numérico QP.
"""

from opti_learn.opti_app.core.solver_qp_numerical import solve_qp


def test_simple_qp():
    """Test con un problema QP simple de 2 variables."""
    print("=" * 60)
    print("TEST: Problema QP Simple")
    print("=" * 60)
    
    # Problema simple: min f(x1, x2) = x1^2 + x2^2 - 2*x1 - 4*x2
    # s.a. x1 + 2*x2 <= 4
    #      x1, x2 >= 0
    
    objective = "x1**2 + x2**2 - 2*x1 - 4*x2"
    variables = ["x1", "x2"]
    constraints = [
        {
            'expr': 'x1 + 2*x2',
            'kind': 'ineq',
            'rhs': 4.0
        }
    ]
    
    result = solve_qp(objective, variables, constraints)
    
    print(f"\nEstado: {result['status']}")
    print(f"Mensaje: {result['message']}")
    
    if result['status'] == 'success':
        print(f"\n✅ SOLUCIÓN ENCONTRADA:")
        print(f"   x* = {result['x_star']}")
        print(f"   f(x*) = {result['f_star']}")
    
    print(f"\nPasos generados: {len(result.get('steps', []))}")
    for step in result.get('steps', []):
        print(f"\n  Paso {step['numero']}: {step['titulo']}")
    
    print("\n" + "=" * 60)
    return result


def test_portfolio_qp():
    """Test con el problema de cartera (portafolio)."""
    print("\n" * 2)
    print("=" * 60)
    print("TEST: Problema de Portafolio de Inversión")
    print("=" * 60)
    
    # Problema de portafolio
    # min variance = x1^2 + x2^2 + x3^2
    # s.a. x1 + x2 + x3 = 1 (toda la inversión)
    #      0.05*x1 + 0.10*x2 + 0.15*x3 >= 0.08 (retorno mínimo)
    #      x1, x2, x3 >= 0
    
    objective = "x1**2 + x2**2 + x3**2"
    variables = ["x1", "x2", "x3"]
    constraints = [
        {
            'expr': 'x1 + x2 + x3',
            'kind': 'eq',
            'rhs': 1.0
        },
        {
            'expr': '0.05*x1 + 0.10*x2 + 0.15*x3',
            'kind': 'ineq',
            'rhs': 0.08
        }
    ]
    
    result = solve_qp(objective, variables, constraints)
    
    print(f"\nEstado: {result['status']}")
    print(f"Mensaje: {result['message']}")
    
    if result['status'] == 'success':
        print(f"\n✅ SOLUCIÓN ENCONTRADA:")
        print(f"   x* = {result['x_star']}")
        print(f"   Riesgo mínimo (varianza): {result['f_star']}")
        
        x_star = result['x_star']
        if len(x_star) == 3:
            print(f"\n   Interpretación:")
            print(f"   - Activo 1 (bajo riesgo, 5% retorno): {x_star[0]*100:.2f}%")
            print(f"   - Activo 2 (medio riesgo, 10% retorno): {x_star[1]*100:.2f}%")
            print(f"   - Activo 3 (alto riesgo, 15% retorno): {x_star[2]*100:.2f}%")
    
    print(f"\nPasos generados: {len(result.get('steps', []))}")
    for step in result.get('steps', []):
        print(f"\n  Paso {step['numero']}: {step['titulo']}")
        if 'contenido' in step and isinstance(step['contenido'], dict):
            if 'solucion' in step['contenido']:
                print(f"    Solución: {step['contenido']['solucion']}")
    
    print("\n" + "=" * 60)
    return result


if __name__ == "__main__":
    # Ejecutar tests
    result1 = test_simple_qp()
    result2 = test_portfolio_qp()
    
    # Resumen
    print("\n\n" + "="*60)
    print("RESUMEN DE TESTS")
    print("="*60)
    print(f"Test Simple QP: {result1['status']}")
    print(f"Test Portafolio: {result2['status']}")
    print("="*60)
