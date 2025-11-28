"""
Test del solver de Multiplicadores de Lagrange
Prueba con un problema clásico de optimización con restricción
"""
import sys
sys.path.insert(0, 'opti_learn')

from opti_app.core.solver_lagrange import solve_with_lagrange_method

def test_lagrange_basico():
    """
    Problema clásico:
    Minimizar: f(x, y) = x^2 + y^2
    Sujeto a: x + y = 1
    
    Solución esperada: x* = 0.5, y* = 0.5, f* = 0.5
    """
    print("=" * 60)
    print("TEST 1: Problema básico de Lagrange")
    print("=" * 60)
    print()
    
    objective = "x**2 + y**2"
    variables = ["x", "y"]
    constraints = ["x + y - 1"]  # x + y - 1 = 0
    
    result = solve_with_lagrange_method(
        objective_expression=objective,
        variable_names=variables,
        equality_constraints=constraints
    )
    
    print(f"Status: {result['status']}")
    print()
    
    if result['status'] == 'success':
        # Guardar explicación
        with open('solucion_lagrange_basico.md', 'w', encoding='utf-8') as f:
            f.write(result['explanation'])
        
        print("Explicación guardada en: solucion_lagrange_basico.md")
        print()
        
        # Mostrar solución
        if result.get('solution'):
            print("Solución óptima:")
            for var, val in result['solution'].items():
                print(f"  {var} = {val}")
    else:
        print(f"Error: {result.get('message', 'Desconocido')}")
    
    print()


def test_lagrange_no_lineal():
    """
    Problema no lineal:
    Minimizar: f(x, y) = x^2 + y^2 + 3*x + x*y
    Sujeto a: x + y = 2
    """
    print("=" * 60)
    print("TEST 2: Problema no lineal con restricción")
    print("=" * 60)
    print()
    
    objective = "x**2 + y**2 + 3*x + x*y"
    variables = ["x", "y"]
    constraints = ["x + y - 2"]  # x + y - 2 = 0
    
    result = solve_with_lagrange_method(
        objective_expression=objective,
        variable_names=variables,
        equality_constraints=constraints
    )
    
    print(f"Status: {result['status']}")
    print()
    
    if result['status'] == 'success':
        # Guardar explicación
        with open('solucion_lagrange_nolineal.md', 'w', encoding='utf-8') as f:
            f.write(result['explanation'])
        
        print("Explicación guardada en: solucion_lagrange_nolineal.md")
        print()
        
        # Mostrar solución
        if result.get('solution'):
            print("Solución óptima:")
            for var, val in result['solution'].items():
                print(f"  {var} = {val}")
    
    print()


def test_lagrange_geometrico():
    """
    Problema geométrico:
    Minimizar: f(x, y) = (x - 1)^2 + (y - 2)^2
    Sujeto a: x + 2*y = 4
    
    (Distancia mínima de un punto a una recta)
    """
    print("=" * 60)
    print("TEST 3: Problema geométrico - distancia mínima")
    print("=" * 60)
    print()
    
    objective = "(x - 1)**2 + (y - 2)**2"
    variables = ["x", "y"]
    constraints = ["x + 2*y - 4"]  # x + 2*y - 4 = 0
    
    result = solve_with_lagrange_method(
        objective_expression=objective,
        variable_names=variables,
        equality_constraints=constraints
    )
    
    print(f"Status: {result['status']}")
    print()
    
    if result['status'] == 'success':
        # Guardar explicación
        with open('solucion_lagrange_geometrico.md', 'w', encoding='utf-8') as f:
            f.write(result['explanation'])
        
        print("Explicación guardada en: solucion_lagrange_geometrico.md")
        print()
        
        # Mostrar valores
        step7 = result['steps']['step7']
        if step7['optimal_point']:
            print("Punto óptimo:")
            for var, val in step7['optimal_point'].items():
                print(f"  {var}* = {val:.4f}")
            print(f"\nValor óptimo: f* = {step7['optimal_value']:.4f}")
            
            print("\nMultiplicadores:")
            for lam, val in step7['lambda_values'].items():
                print(f"  {lam} = {val:.4f}")
    
    print()


if __name__ == '__main__':
    test_lagrange_basico()
    test_lagrange_no_lineal()
    test_lagrange_geometrico()
    
    print("=" * 60)
    print("TESTS COMPLETADOS")
    print("=" * 60)
