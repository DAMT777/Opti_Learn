"""
Test detallado del solver numérico QP mostrando todo el contenido.
"""

from opti_learn.opti_app.core.solver_qp_numerical import solve_qp
import pprint


def test_detailed_output():
    """Muestra la salida completa con todos los detalles."""
    print("=" * 80)
    print("TEST DETALLADO: Problema QP con Salida Completa")
    print("=" * 80)
    
    # Problema simple pero interesante
    objective = "x1**2 + 2*x2**2 + x1*x2 - 5*x1 - 3*x2"
    variables = ["x1", "x2"]
    constraints = [
        {'expr': 'x1 + x2', 'kind': 'eq', 'rhs': 2.0},
        {'expr': '2*x1 + x2', 'kind': 'ineq', 'rhs': 5.0}
    ]
    
    result = solve_qp(objective, variables, constraints)
    
    print(f"\nMETODO: {result['method']}")
    print(f"ESTADO: {result['status']}")
    print(f"MENSAJE: {result['message']}")
    
    if result.get('x_star'):
        print(f"\nSOLUCION OPTIMA:")
        print(f"  x* = {result['x_star']}")
        print(f"  f(x*) = {result['f_star']}")
    
    print("\n" + "=" * 80)
    print("PASOS EDUCATIVOS:")
    print("=" * 80)
    
    for step in result.get('steps', []):
        print(f"\n{'='*80}")
        print(f"PASO {step['numero']}: {step['titulo']}")
        print(f"{'='*80}")
        
        contenido = step.get('contenido', {})
        pprint.pprint(contenido, width=80)
    
    print("\n" + "=" * 80)
    print("TEST COMPLETADO")
    print("=" * 80)
    
    return result


if __name__ == "__main__":
    result = test_detailed_output()
    
    print(f"\nRESULTADO FINAL: {result['status']}")

