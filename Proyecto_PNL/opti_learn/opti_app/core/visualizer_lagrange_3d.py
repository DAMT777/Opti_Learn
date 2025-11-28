"""
Visualizador 3D pedagógico para el Método de Multiplicadores de Lagrange
Genera gráficos tridimensionales que muestran:
- Superficie de la función objetivo f(x,y)
- Curva/superficie de restricción g(x,y) = 0
- Punto óptimo en el espacio
- Interpretación geométrica de la condición de tangencia
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI para servidor
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from typing import Dict, Any, Optional, List, Tuple
import sympy as sp
from sympy import symbols, lambdify


class LagrangeVisualizer3D:
    """
    Visualizador 3D para problemas de Lagrange en 2D (2 variables).
    Muestra la superficie de la función objetivo y la restricción en el espacio 3D.
    """
    
    def __init__(self, output_dir: str = None):
        """
        Inicializa el visualizador 3D.
        
        Args:
            output_dir: Directorio donde guardar las imágenes generadas
        """
        if output_dir is None:
            # Detectar directorio del proyecto Django
            current_file = os.path.abspath(__file__)
            app_dir = os.path.dirname(os.path.dirname(current_file))  # opti_app/
            self.output_dir = os.path.join(app_dir, 'static', 'tmp')
        else:
            self.output_dir = output_dir
        
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_3d_visualization(
        self,
        objective_expr: str,
        var_names: List[str],
        constraints: List[str],
        optimal_point: Dict[str, float],
        optimal_value: float,
        filename: str = 'lagrange_plot_3d.png'
    ) -> Optional[str]:
        """
        Genera visualización 3D del método de Lagrange.
        
        Args:
            objective_expr: Expresión de la función objetivo (ej: "x**2 + y**2")
            var_names: Lista de nombres de variables ['x', 'y']
            constraints: Lista de restricciones de igualdad (ej: ["x + y - 1"])
            optimal_point: Diccionario con valores óptimos {'x': val_x, 'y': val_y}
            optimal_value: Valor de f en el punto óptimo
            filename: Nombre del archivo PNG a generar
            
        Returns:
            Ruta completa al archivo generado o None si hay error
        """
        # Validar que sea un problema 2D
        if len(var_names) != 2:
            print(f"⚠️ Visualización 3D solo disponible para problemas con 2 variables (recibidas: {len(var_names)})")
            return None
        
        if not constraints:
            print("⚠️ Se requiere al menos una restricción para visualización 3D")
            return None
        
        try:
            # Crear símbolos de SymPy
            x_sym, y_sym = symbols(var_names[0]), symbols(var_names[1])
            
            # Parsear expresiones
            f_sym = sp.sympify(objective_expr)
            g_sym = sp.sympify(constraints[0])  # Primera restricción
            
            # Convertir a funciones NumPy
            f_func = lambdify((x_sym, y_sym), f_sym, modules=['numpy'])
            g_func = lambdify((x_sym, y_sym), g_sym, modules=['numpy'])
            
            # Extraer valores del punto óptimo
            x_opt = optimal_point[var_names[0]]
            y_opt = optimal_point[var_names[1]]
            z_opt = optimal_value
            
            # Calcular rango de visualización
            x_range, y_range = self._compute_plot_range_3d(
                x_opt, y_opt, 
                f_func, g_func,
                margin_factor=1.5
            )
            
            # Crear malla para evaluación
            x_mesh = np.linspace(x_range[0], x_range[1], 100)
            y_mesh = np.linspace(y_range[0], y_range[1], 100)
            X, Y = np.meshgrid(x_mesh, y_mesh)
            
            # Evaluar función objetivo en la malla
            with np.errstate(all='ignore'):
                Z = f_func(X, Y)
                Z = np.nan_to_num(Z, nan=np.nan, posinf=np.nan, neginf=np.nan)
            
            # Crear figura 3D
            fig = plt.figure(figsize=(10, 8), dpi=120)
            ax = fig.add_subplot(111, projection='3d')
            
            # 1. Superficie de la función objetivo
            surf = ax.plot_surface(
                X, Y, Z,
                cmap=cm.viridis,
                alpha=0.7,
                antialiased=True,
                edgecolor='none',
                label='f(x,y)'
            )
            
            # 2. Curva de restricción en 3D (proyectada sobre la superficie)
            # Resolver g(x,y) = 0 para obtener puntos de la restricción
            constraint_points = self._compute_constraint_curve(
                g_func, x_range, y_range, num_points=200
            )
            
            if constraint_points is not None:
                x_constraint, y_constraint = constraint_points
                # Evaluar f en los puntos de la restricción
                with np.errstate(all='ignore'):
                    z_constraint = f_func(x_constraint, y_constraint)
                    z_constraint = np.nan_to_num(z_constraint, nan=np.nan)
                
                # Dibujar curva de restricción sobre la superficie
                valid_mask = ~np.isnan(z_constraint)
                ax.plot(
                    x_constraint[valid_mask],
                    y_constraint[valid_mask],
                    z_constraint[valid_mask],
                    color='red',
                    linewidth=3,
                    label='Restricción g(x,y)=0',
                    zorder=10
                )
            
            # 3. Punto óptimo
            ax.scatter(
                [x_opt], [y_opt], [z_opt],
                color='lime',
                s=150,
                edgecolors='darkgreen',
                linewidths=2,
                marker='o',
                label=f'Óptimo ({x_opt:.2f}, {y_opt:.2f}, {z_opt:.2f})',
                zorder=15
            )
            
            # 4. Línea vertical desde la base hasta el punto óptimo
            ax.plot(
                [x_opt, x_opt],
                [y_opt, y_opt],
                [ax.get_zlim()[0], z_opt],
                color='lime',
                linestyle='--',
                linewidth=1.5,
                alpha=0.6,
                zorder=5
            )
            
            # 5. Proyección del punto óptimo en el plano xy
            ax.scatter(
                [x_opt], [y_opt], [ax.get_zlim()[0]],
                color='lime',
                s=80,
                alpha=0.5,
                marker='o',
                zorder=5
            )
            
            # Configuración de ejes y título
            ax.set_xlabel(var_names[0], fontsize=10, labelpad=8)
            ax.set_ylabel(var_names[1], fontsize=10, labelpad=8)
            ax.set_zlabel('f(x,y)', fontsize=10, labelpad=8)
            ax.set_title(
                'Visualización 3D - Método de Multiplicadores de Lagrange',
                fontsize=11,
                pad=15,
                fontweight='bold'
            )
            
            # Leyenda
            ax.legend(loc='upper left', fontsize=8.5, framealpha=0.9)
            
            # Colorbar para la superficie
            fig.colorbar(surf, ax=ax, shrink=0.6, aspect=10, pad=0.1)
            
            # Ajuste de vista (ángulo de cámara)
            ax.view_init(elev=25, azim=45)
            
            # Agregar grid
            ax.grid(True, alpha=0.3)
            
            # Texto pedagógico
            textstr = (
                'El punto óptimo se encuentra donde\n'
                'la restricción (roja) es tangente a\n'
                'una curva de nivel de f(x,y)'
            )
            props = dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.8)
            ax.text2D(
                0.02, 0.98,
                textstr,
                transform=ax.transAxes,
                fontsize=8.5,
                verticalalignment='top',
                bbox=props
            )
            
            # Ajustar layout
            plt.tight_layout()
            
            # Guardar figura
            output_path = os.path.join(self.output_dir, filename)
            plt.savefig(output_path, dpi=120, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            
            print(f"✅ Visualización 3D generada: {output_path}")
            
            # Retornar ruta relativa para usar en el servidor web
            # Convertir de absoluto a relativo desde opti_app/
            relative_path = os.path.join('static', 'tmp', filename)
            return relative_path
            
        except Exception as e:
            print(f"❌ Error generando visualización 3D: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _compute_constraint_curve(
        self,
        g_func,
        x_range: Tuple[float, float],
        y_range: Tuple[float, float],
        num_points: int = 200
    ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Calcula puntos de la curva de restricción g(x,y) = 0.
        
        Args:
            g_func: Función de restricción compilada
            x_range: Rango (min, max) para x
            y_range: Rango (min, max) para y
            num_points: Número de puntos a calcular
            
        Returns:
            Tupla (x_points, y_points) o None si falla
        """
        try:
            from scipy.optimize import fsolve
            
            x_vals = np.linspace(x_range[0], x_range[1], num_points)
            y_vals = []
            
            # Para cada x, resolver g(x, y) = 0 para encontrar y
            y_guess = (y_range[0] + y_range[1]) / 2
            
            for x_val in x_vals:
                try:
                    # Resolver g(x_val, y) = 0
                    def equation(y):
                        return g_func(x_val, y)
                    
                    y_sol = fsolve(equation, y_guess, full_output=False)
                    
                    # Verificar que la solución es válida
                    if y_range[0] <= y_sol[0] <= y_range[1]:
                        residual = abs(g_func(x_val, y_sol[0]))
                        if residual < 0.01:  # Tolerancia
                            y_vals.append(y_sol[0])
                            y_guess = y_sol[0]  # Actualizar guess
                        else:
                            y_vals.append(np.nan)
                    else:
                        y_vals.append(np.nan)
                except:
                    y_vals.append(np.nan)
            
            y_vals = np.array(y_vals)
            
            # Filtrar puntos inválidos
            valid_mask = ~np.isnan(y_vals)
            if valid_mask.sum() < 10:  # Si hay muy pocos puntos válidos
                return None
            
            return x_vals[valid_mask], y_vals[valid_mask]
            
        except Exception as e:
            print(f"⚠️ No se pudo calcular curva de restricción: {e}")
            return None
    
    def _compute_plot_range_3d(
        self,
        x_opt: float,
        y_opt: float,
        f_func,
        g_func,
        margin_factor: float = 1.5
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Calcula rangos apropiados para la visualización 3D.
        
        Args:
            x_opt: Valor óptimo de x
            y_opt: Valor óptimo de y
            f_func: Función objetivo
            g_func: Función de restricción
            margin_factor: Factor de margen alrededor del punto óptimo
            
        Returns:
            Tupla ((x_min, x_max), (y_min, y_max))
        """
        # Usar punto óptimo como centro
        base_range = max(abs(x_opt), abs(y_opt), 2.0)
        margin = base_range * margin_factor
        
        x_range = (x_opt - margin, x_opt + margin)
        y_range = (y_opt - margin, y_opt + margin)
        
        return x_range, y_range


def generate_lagrange_3d_plot(
    objective: str,
    variables: List[str],
    constraints: List[str],
    optimal_point: Dict[str, float],
    optimal_value: float,
    filename: str = 'lagrange_3d.png'
) -> Optional[str]:
    """
    Función helper para generar visualización 3D de Lagrange.
    
    Args:
        objective: Expresión de la función objetivo
        variables: Lista de nombres de variables
        constraints: Lista de restricciones de igualdad
        optimal_point: Diccionario con valores óptimos
        optimal_value: Valor de f en el punto óptimo
        filename: Nombre del archivo a generar
        
    Returns:
        Ruta al archivo generado o None si hay error
    """
    visualizer = LagrangeVisualizer3D()
    return visualizer.create_3d_visualization(
        objective,
        variables,
        constraints,
        optimal_point,
        optimal_value,
        filename
    )
