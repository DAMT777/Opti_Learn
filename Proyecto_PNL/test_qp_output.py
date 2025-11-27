"""
Test para ver la salida formateada del solver QP.
"""

from opti_learn.opti_app.core.solver_qp_numerical import solve_qp


def test_qp_output():
    """Prueba la salida formateada del solver."""
    
    print("="*80)
    print("PROBLEMA DE CARTERA DE INVERSION")
    print("="*80)
    
    # Problema de portafolio real
    objective = "A**2 + B**2"
    variables = ["A", "B"]
    constraints = [
        {'expr': 'A + B', 'kind': 'eq', 'rhs': 100.0},
        {'expr': 'A', 'kind': 'ineq', 'rhs': 20.0},
        {'expr': 'A', 'kind': 'ineq', 'rhs': 70.0},
        {'expr': 'B', 'kind': 'ineq', 'rhs': 60.0},
        {'expr': 'B', 'kind': 'ineq', 'rhs': 65.0},
        {'expr': '0.254*A + 0.358*B', 'kind': 'ineq', 'rhs': 28.0}
    ]
    
    result = solve_qp(objective, variables, constraints)
    
    print(f"\nEstado: {result['status']}")
    print(f"Metodo: {result['method']}")
    
    if result.get('x_star'):
        print(f"\nSOLUCION:")
        print(f"  A = {result['x_star'][0]:.2f}")
        print(f"  B = {result['x_star'][1]:.2f}")
        print(f"  Riesgo (varianza) = {result['f_star']:.2f}")
    
    print("\n" + "="*80)
    print("EXPLICACION COMPLETA (FORMATO MARKDOWN)")
    print("="*80)
    
    # Mostrar la explicación completa
    explanation = result.get('explanation', '')
    print(explanation)
    
    return result


if __name__ == "__main__":
    result = test_qp_output()
    print("\n" + "="*80)
    print(f"TEST COMPLETADO - Status: {result['status']}")
    print("="*80)
