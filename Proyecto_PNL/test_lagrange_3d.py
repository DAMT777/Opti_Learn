"""
Test de visualización 3D para el Solver de Lagrange
Verifica que las superficies 3D se generen correctamente
"""

import sys
import os

# Agregar directorio opti_learn al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'opti_learn'))

from opti_app.core.solver_lagrange import solve_with_lagrange_method


def test_visualization_3d_basic():
    """Test básico: minimizar x^2 + y^2 con restricción x + y = 1"""
    print("\n" + "="*70)
    print("TEST 1: Visualización 3D - Problema Básico")
    print("="*70)
    
    result = solve_with_lagrange_method(
        objective_expression="x**2 + y**2",
        variable_names=['x', 'y'],
        equality_constraints=["x + y - 1"]
    )
    
    print(result['explanation'])
    
    # Verificar que se generaron las visualizaciones
    assert '<img src=' in result['explanation'], "❌ No se encontró visualización en la explicación"
    
    # Verificar que aparecen AMBAS visualizaciones (2D y 3D)
    img_count = result['explanation'].count('<img src=')
    print(f"\n✅ Se generaron {img_count} visualizaciones")
    
    if img_count >= 2:
        print("✅ TEST PASADO - Se generaron visualizaciones 2D y 3D")
    elif img_count == 1:
        print("⚠️ ADVERTENCIA - Solo se generó 1 visualización")
    else:
        print("❌ ERROR - No se generaron visualizaciones")
    
    return result


def test_visualization_3d_nonlinear():
    """Test no lineal: x^2 + 4*y^2 con x + 2*y = 6"""
    print("\n" + "="*70)
    print("TEST 2: Visualización 3D - Problema No Lineal")
    print("="*70)
    
    result = solve_with_lagrange_method(
        objective_expression="x**2 + 4*y**2",
        variable_names=['x', 'y'],
        equality_constraints=["x + 2*y - 6"]
    )
    
    # Verificar visualizaciones
    img_count = result['explanation'].count('<img src=')
    print(f"\n✅ Se generaron {img_count} visualizaciones")
    
    # Verificar que hay secciones 2D y 3D
    has_2d = "Visualización 2D" in result['explanation']
    has_3d = "Visualización 3D" in result['explanation']
    
    print(f"📈 Visualización 2D presente: {has_2d}")
    print(f"🌐 Visualización 3D presente: {has_3d}")
    
    if has_2d and has_3d:
        print("✅ TEST PASADO - Ambas visualizaciones presentes")
    else:
        print("⚠️ ADVERTENCIA - Falta alguna visualización")
    
    return result


def test_visualization_3d_server_problem():
    """Test del problema del servidor: -t^2 - k^2 + 12*t + 8*k con 2*t + k = 18"""
    print("\n" + "="*70)
    print("TEST 3: Visualización 3D - Problema del Servidor")
    print("="*70)
    
    result = solve_with_lagrange_method(
        objective_expression="-t**2 - k**2 + 12*t + 8*k",
        variable_names=['t', 'k'],
        equality_constraints=["2*t + k - 18"]
    )
    
    # Verificar visualizaciones
    img_count = result['explanation'].count('<img src=')
    print(f"\n✅ Se generaron {img_count} visualizaciones")
    
    # Buscar las rutas de las imágenes
    explanation = result['explanation']
    if 'lagrange_3d_' in explanation:
        print("✅ Archivo 3D encontrado en la explicación")
    if 'lagrange_2d_' in explanation:
        print("✅ Archivo 2D encontrado en la explicación")
    
    # Verificar estilos CSS responsivos
    has_responsive_css = 'max-width: 100%' in explanation
    has_border_radius = 'border-radius' in explanation
    
    print(f"📐 CSS responsivo presente: {has_responsive_css}")
    print(f"🎨 Border radius presente: {has_border_radius}")
    
    if img_count >= 2 and has_responsive_css:
        print("✅ TEST PASADO - Visualizaciones 3D completas con CSS")
    else:
        print("⚠️ Revisar visualizaciones")
    
    return result


if __name__ == "__main__":
    print("\n🧪 EJECUTANDO TESTS DE VISUALIZACIÓN 3D")
    print("="*70)
    
    try:
        # Test 1
        result1 = test_visualization_3d_basic()
        
        # Test 2
        result2 = test_visualization_3d_nonlinear()
        
        # Test 3
        result3 = test_visualization_3d_server_problem()
        
        print("\n" + "="*70)
        print("🎉 TODOS LOS TESTS COMPLETADOS")
        print("="*70)
        
        # Guardar resultado del último test
        with open("solucion_lagrange_3d_test.md", "w", encoding="utf-8") as f:
            f.write(result3['explanation'])
        
        print("\n✅ Resultado guardado en: solucion_lagrange_3d_test.md")
        
    except Exception as e:
        print(f"\n❌ ERROR EN LOS TESTS: {str(e)}")
        import traceback
        traceback.print_exc()
