"""
Test de serialización JSON del solver QP.
"""

import json
from opti_learn.opti_app.core.solver_qp_numerical import solve_qp


def test_json_serialization():
    """Verifica que el resultado del solver sea serializable a JSON."""
    
    print("="*80)
    print("TEST DE SERIALIZACION JSON")
    print("="*80)
    
    # Problema de ejemplo
    objective = "A**2 + B**2"
    variables = ["A", "B"]
    constraints = [
        {'expr': 'A', 'kind': 'ineq', 'rhs': 20.0},
        {'expr': 'A', 'kind': 'ineq', 'rhs': 70.0},
        {'expr': 'B', 'kind': 'ineq', 'rhs': 60.0},
        {'expr': 'A + B', 'kind': 'eq', 'rhs': 100.0}
    ]
    
    # Ejecutar solver
    result = solve_qp(objective, variables, constraints)
    
    print(f"\nEstado: {result['status']}")
    print(f"Metodo: {result['method']}")
    
    # Intentar serializar a JSON
    try:
        json_str = json.dumps(result, indent=2)
        print("\n[OK] Serializacion JSON exitosa!")
        print(f"\nTamano del JSON: {len(json_str)} caracteres")
        
        # Verificar que se pueda deserializar
        result_decoded = json.loads(json_str)
        print(f"[OK] Deserializacion exitosa!")
        print(f"[OK] Pasos en resultado: {len(result_decoded.get('steps', []))}")
        
        if result_decoded.get('x_star'):
            print(f"[OK] Solucion: {result_decoded['x_star']}")
            print(f"[OK] Valor optimo: {result_decoded['f_star']}")
        
        return True
        
    except TypeError as e:
        print(f"\n[ERROR] Fallo la serializacion JSON: {e}")
        print(f"Tipo del error: {type(e)}")
        
        # Encontrar el valor problemático
        def find_non_serializable(obj, path=""):
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
                    print(f"  Valor no serializable en: {path}")
                    print(f"  Tipo: {type(obj)}")
                    print(f"  Valor: {obj}")
        
        find_non_serializable(result)
        return False


if __name__ == "__main__":
    success = test_json_serialization()
    print("\n" + "="*80)
    if success:
        print("RESULTADO: EXITO - El solver genera JSON valido")
    else:
        print("RESULTADO: FALLO - Hay problemas de serializacion")
    print("="*80)
