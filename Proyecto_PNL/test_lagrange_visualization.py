"""
Test de visualización gráfica para el solver de Lagrange
"""
import sys
sys.path.insert(0, 'opti_learn')

from opti_app.core.solver_lagrange import solve_with_lagrange_method
import os


def test_visualization_basico():
    """
    Test con problema básico que debe generar visualización.
    """
    print("=" * 60)
    print("TEST: Visualización de Lagrange - Problema Básico")
    print("=" * 60)
    print()
    
    objective = "x**2 + y**2"
    variables = ["x", "y"]
    constraints = ["x + y - 1"]
    
    print(f"Objetivo: {objective}")
    print(f"Restricción: {constraints[0]} = 0")
    print()
    
    result = solve_with_lagrange_method(
        objective_expression=objective,
        variable_names=variables,
        equality_constraints=constraints
    )
    
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        # Guardar explicación
        with open('solucion_lagrange_visual_basico.md', 'w', encoding='utf-8') as f:
            f.write(result['explanation'])
        
        print("✅ Explicación guardada en: solucion_lagrange_visual_basico.md")
        print()
        
        # Verificar si se generó la visualización
        if 'lagrange_' in result['explanation'] and '.png' in result['explanation']:
            print("✅ Visualización incluida en la explicación")
            
            # Buscar la ruta del archivo
            lines = result['explanation'].split('\n')
            for line in lines:
                if 'static/tmp/lagrange_' in line:
                    print(f"   Ruta: {line.strip()}")
                    break
        else:
            print("⚠️  No se incluyó visualización (puede ser problema 1D o error)")
        
        print()
        
        # Mostrar solución
        if result.get('solution'):
            print("Solución:")
            for var, val in result['solution'].items():
                print(f"  {var} = {val}")
        
        return True
    else:
        print(f"❌ Error: {result.get('message')}")
        return False


def test_visualization_geometrico():
    """
    Test con problema geométrico (distancia mínima).
    """
    print()
    print("=" * 60)
    print("TEST: Visualización de Lagrange - Problema Geométrico")
    print("=" * 60)
    print()
    
    objective = "(x - 1)**2 + (y - 2)**2"
    variables = ["x", "y"]
    constraints = ["x + 2*y - 4"]
    
    print(f"Objetivo: {objective}")
    print(f"Restricción: {constraints[0]} = 0")
    print()
    
    result = solve_with_lagrange_method(
        objective_expression=objective,
        variable_names=variables,
        equality_constraints=constraints
    )
    
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        # Guardar explicación
        with open('solucion_lagrange_visual_geometrico.md', 'w', encoding='utf-8') as f:
            f.write(result['explanation'])
        
        print("✅ Explicación guardada en: solucion_lagrange_visual_geometrico.md")
        print()
        
        # Verificar visualización
        if '<img src=' in result['explanation'] and 'lagrange_' in result['explanation']:
            print("✅ Visualización incluida en la explicación")
        else:
            print("⚠️  No se incluyó visualización")
        
        return True
    else:
        print(f"❌ Error: {result.get('message')}")
        return False


def test_visualization_servidor():
    """
    Test con el problema del servidor.
    """
    print()
    print("=" * 60)
    print("TEST: Visualización de Lagrange - Problema del Servidor")
    print("=" * 60)
    print()
    
    objective = "-t**2 - k**2 + 12*t + 8*k"
    variables = ["t", "k"]
    constraints = ["2*t + k - 18"]
    
    print(f"Objetivo: {objective}")
    print(f"Restricción: {constraints[0]} = 0")
    print()
    
    result = solve_with_lagrange_method(
        objective_expression=objective,
        variable_names=variables,
        equality_constraints=constraints
    )
    
    print(f"Status: {result['status']}")
    
    if result['status'] == 'success':
        # Guardar explicación
        with open('solucion_lagrange_visual_servidor.md', 'w', encoding='utf-8') as f:
            f.write(result['explanation'])
        
        print("✅ Explicación guardada en: solucion_lagrange_visual_servidor.md")
        print()
        
        # Verificar visualización
        if '<img src=' in result['explanation'] and 'lagrange_' in result['explanation']:
            print("✅ Visualización incluida en la explicación")
            
            # Verificar que el archivo existe
            import re
            match = re.search(r'static/tmp/(lagrange_\d+\.png)', result['explanation'])
            if match:
                filepath = os.path.join('opti_learn/opti_app', match.group(0))
                if os.path.exists(filepath):
                    print(f"✅ Archivo de imagen existe: {filepath}")
                else:
                    print(f"⚠️  Archivo no encontrado: {filepath}")
        else:
            print("⚠️  No se incluyó visualización")
        
        return True
    else:
        print(f"❌ Error: {result.get('message')}")
        return False


if __name__ == '__main__':
    test1 = test_visualization_basico()
    test2 = test_visualization_geometrico()
    test3 = test_visualization_servidor()
    
    print()
    print("=" * 60)
    print("RESUMEN DE TESTS")
    print("=" * 60)
    print(f"Test básico: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Test geométrico: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Test servidor: {'✅ PASS' if test3 else '❌ FAIL'}")
    print("=" * 60)
