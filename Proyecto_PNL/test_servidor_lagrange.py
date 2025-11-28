"""
Test con el problema específico que falló en el servidor
"""
import sys
import json
sys.path.insert(0, 'opti_learn')

from opti_app.core.solver_lagrange import solve_with_lagrange_method

def test_problema_servidor():
    """
    Reproduce el problema exacto del servidor:
    objetivo: -t**2 - k**2 + 12*t + 8*k
    variables: ['t', 'k']
    restricción: (2*t + k) - (18) = 0
    """
    print("=" * 60)
    print("TEST: Problema del servidor")
    print("=" * 60)
    print()
    
    objective = "-t**2 - k**2 + 12*t + 8*k"
    variables = ["t", "k"]
    constraints = ["(2*t + k) - (18)"]
    
    print(f"Objetivo: {objective}")
    print(f"Variables: {variables}")
    print(f"Restricción: {constraints[0]} = 0")
    print()
    
    result = solve_with_lagrange_method(
        objective_expression=objective,
        variable_names=variables,
        equality_constraints=constraints
    )
    
    print(f"Status: {result['status']}")
    
    if result['status'] == 'error':
        print(f"Error: {result.get('message')}")
        return False
    
    print()
    
    # Intentar serializar a JSON
    try:
        json_str = json.dumps(result, indent=2)
        print("✅ Serialización JSON exitosa")
        print()
        
        # Mostrar solución
        if result.get('solution'):
            print("Solución encontrada:")
            for var, val in result['solution'].items():
                print(f"  {var} = {val}")
        
        print()
        
        # Verificar que se pueda deserializar
        parsed = json.loads(json_str)
        print("✅ Deserialización exitosa")
        print()
        
        # Guardar explicación
        with open('solucion_servidor_test.md', 'w', encoding='utf-8') as f:
            f.write(result['explanation'])
        print("📄 Explicación guardada en: solucion_servidor_test.md")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Tipo: {type(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_problema_servidor()
    print()
    print("=" * 60)
    print(f"TEST {'EXITOSO ✅' if success else 'FALLIDO ❌'}")
    print("=" * 60)
