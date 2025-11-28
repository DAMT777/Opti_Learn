"""
Visualizador 3D pedagógico para el Método de Cálculo Diferencial
Genera gráficos tridimensionales que muestran:
- Superficie de la función objetivo f(x,y)
- Puntos críticos sobre la superficie
- Punto óptimo destacado
- Interpretación geométrica del gradiente y Hessiano
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


class DifferentialVisualizer3D:
    """
    Visualizador 3D para problemas de Cálculo Diferencial (optimización sin restricciones).
    Muestra la superficie de la función objetivo y los puntos críticos encontrados.
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
        critical_points: List[Dict[str, float]],
        optimal_point: Dict[str, float],
        optimal_value: float,
        point_nature: str = "",
        filename: str = 'differential_plot_3d.png'
    ) -> Optional[str]:
        """
        Genera visualización 3D del método de Cálculo Diferencial.
        
        Args:
            objective_expr: Expresión de la función objetivo (ej: "x**2 + y**2")
            var_names: Lista de nombres de variables ['x', 'y']
            critical_points: Lista de puntos críticos encontrados
            optimal_point: Diccionario con valores óptimos {'x': val_x, 'y': val_y}
            optimal_value: Valor de f en el punto óptimo
            point_nature: Naturaleza del punto ("mínimo local", "máximo local", etc.)
            filename: Nombre del archivo PNG a generar
            
        Returns:
            Ruta relativa al archivo generado o None si hay error
        """
        # Validar que sea un problema 2D
        if len(var_names) != 2:
            print(f"⚠️ Visualización 3D solo disponible para problemas con 2 variables (recibidas: {len(var_names)})")
            return None
        
        try:
            # Crear símbolos de SymPy
            x_sym, y_sym = symbols(var_names[0]), symbols(var_names[1])
            
            # Parsear expresión
            f_sym = sp.sympify(objective_expr)
            
            # Convertir a función NumPy
            f_func = lambdify((x_sym, y_sym), f_sym, modules=['numpy'])
            
            # Extraer valores del punto óptimo
            x_opt = optimal_point[var_names[0]]
            y_opt = optimal_point[var_names[1]]
            z_opt = optimal_value
            
            # Calcular rango de visualización
            x_range, y_range = self._compute_plot_range_3d(
                x_opt, y_opt,
                critical_points,
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
            
            # 2. Puntos críticos (si hay más de uno)
            if len(critical_points) > 1:
                for i, cp in enumerate(critical_points):
                    if cp != optimal_point:  # No repetir el óptimo
                        x_cp = cp[var_names[0]]
                        y_cp = cp[var_names[1]]
                        z_cp = f_func(x_cp, y_cp)
                        
                        ax.scatter(
                            [x_cp], [y_cp], [z_cp],
                            color='orange',
                            s=100,
                            edgecolors='darkorange',
                            linewidths=2,
                            marker='o',
                            alpha=0.8,
                            zorder=12
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
            
            # Título basado en la naturaleza del punto
            if "mínimo" in point_nature.lower():
                title = 'Visualización 3D - Mínimo Local (Cálculo Diferencial)'
            elif "máximo" in point_nature.lower():
                title = 'Visualización 3D - Máximo Local (Cálculo Diferencial)'
            else:
                title = 'Visualización 3D - Cálculo Diferencial'
            
            ax.set_title(
                title,
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
            if "mínimo" in point_nature.lower():
                textstr = (
                    'El punto óptimo está en el "valle"\n'
                    'donde ∇f = 0 y el Hessiano\n'
                    'es definido positivo'
                )
            elif "máximo" in point_nature.lower():
                textstr = (
                    'El punto óptimo está en la "cima"\n'
                    'donde ∇f = 0 y el Hessiano\n'
                    'es definido negativo'
                )
            else:
                textstr = (
                    'Punto crítico donde ∇f = 0\n'
                    'Clasificado según eigenvalores\n'
                    'del Hessiano'
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
            return f"/static/tmp/{filename}"
            
        except Exception as e:
            print(f"❌ Error generando visualización 3D: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _compute_plot_range_3d(
        self,
        x_opt: float,
        y_opt: float,
        critical_points: List[Dict[str, float]],
        margin_factor: float = 1.5
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Calcula rangos apropiados para la visualización 3D.
        
        Args:
            x_opt: Valor óptimo de x
            y_opt: Valor óptimo de y
            critical_points: Lista de puntos críticos
            margin_factor: Factor de margen alrededor de los puntos
            
        Returns:
            Tupla ((x_min, x_max), (y_min, y_max))
        """
        # Recopilar todos los valores x e y
        x_vals = [x_opt]
        y_vals = [y_opt]
        
        for cp in critical_points:
            if len(cp) >= 2:
                x_vals.append(list(cp.values())[0])
                y_vals.append(list(cp.values())[1])
        
        # Calcular rangos
        x_min, x_max = min(x_vals), max(x_vals)
        y_min, y_max = min(y_vals), max(y_vals)
        
        # Añadir margen
        x_margin = max(abs(x_max - x_min) * 0.3, 2.0)
        y_margin = max(abs(y_max - y_min) * 0.3, 2.0)
        
        x_range = (x_min - x_margin, x_max + x_margin)
        y_range = (y_min - y_margin, y_max + y_margin)
        
        return x_range, y_range


def generate_differential_3d_plot(
    objective: str,
    variables: List[str],
    critical_points: List[Dict[str, float]],
    optimal_point: Dict[str, float],
    optimal_value: float,
    point_nature: str = "",
    filename: str = 'differential_3d.png'
) -> Optional[str]:
    """
    Función helper para generar visualización 3D de Cálculo Diferencial.
    
    Args:
        objective: Expresión de la función objetivo
        variables: Lista de nombres de variables
        critical_points: Lista de puntos críticos
        optimal_point: Diccionario con valores óptimos
        optimal_value: Valor de f en el punto óptimo
        point_nature: Naturaleza del punto (mínimo/máximo/silla)
        filename: Nombre del archivo a generar
        
    Returns:
        Ruta al archivo generado o None si hay error
    """
    visualizer = DifferentialVisualizer3D()
    return visualizer.create_3d_visualization(
        objective,
        variables,
        critical_points,
        optimal_point,
        optimal_value,
        point_nature,
        filename
    )
