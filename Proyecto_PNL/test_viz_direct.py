"""
Test directo del visualizador
"""
import sys
sys.path.insert(0, 'opti_learn')

from opti_app.core.visualizer_lagrange import generate_lagrange_plot

objective = "x**2 + y**2"
variables = ["x", "y"]
constraints = ["x + y - 1"]
optimal_point = {'x': 0.5, 'y': 0.5}
optimal_value = 0.5

print("Generando visualización...")
try:
    path = generate_lagrange_plot(
        objective_expr=objective,
        var_names=variables,
        constraints=constraints,
        optimal_point=optimal_point,
        optimal_value=optimal_value,
        filename='test_viz.png'
    )
    print(f"✅ Visualización generada: {path}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
