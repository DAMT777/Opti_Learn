"""
Test de serialización JSON para el solver de Lagrange
"""
import sys
import json
sys.path.insert(0, 'opti_learn')

from opti_app.core.solver_lagrange import solve_with_lagrange_method

def test_lagrange_json():
    """Verifica que el resultado sea serializable a JSON."""
    print("=" * 60)
    print("TEST: Serialización JSON del solver de Lagrange")
    print("=" * 60)
    print()
    
    objective = "x**2 + y**2"
    variables = ["x", "y"]
    constraints = ["x + y - 1"]
    
    result = solve_with_lagrange_method(
        objective_expression=objective,
        variable_names=variables,
        equality_constraints=constraints
    )
    
    print(f"Status: {result['status']}")
    print()
    
    # Intentar serializar a JSON
    try:
        json_str = json.dumps(result, indent=2)
        print("✅ Serialización JSON exitosa")
        print()
        print("Solución serializada:")
        print(json.dumps(result['solution'], indent=2))
        print()
        print("Steps serializados:")
        print(f"  - step1 keys: {list(result['steps']['step1'].keys())}")
        print(f"  - step7 optimal_point: {result['steps']['step7']['optimal_point']}")
        print()
        return True
    except TypeError as e:
        print(f"❌ Error de serialización: {e}")
        print()
        
        # Diagnóstico detallado
        def find_non_serializable(obj, path="root"):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    find_non_serializable(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    find_non_serializable(item, f"{path}[{i}]")
            else:
                try:
                    json.dumps(obj)
                except TypeError:
                    print(f"  ❌ No serializable en: {path}")
                    print(f"     Tipo: {type(obj)}")
                    print(f"     Valor: {obj}")
        
        find_non_serializable(result)
        return False


if __name__ == '__main__':
    success = test_lagrange_json()
    print("=" * 60)
    print(f"TEST {'EXITOSO ✅' if success else 'FALLIDO ❌'}")
    print("=" * 60)
