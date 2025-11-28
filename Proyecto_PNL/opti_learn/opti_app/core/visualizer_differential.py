"""
Visualizador 2D pedagógico para el Método de Cálculo Diferencial
Genera gráficos de curvas de nivel mostrando puntos críticos
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI para servidor
from matplotlib import cm
from typing import Dict, Any, Optional, List, Tuple
import sympy as sp
from sympy import symbols, lambdify


class DifferentialVisualizer:
    """
    Visualizador 2D para problemas de Cálculo Diferencial.
    Muestra curvas de nivel de la función objetivo y los puntos críticos.
    """
    
    def __init__(self, output_dir: str = None):
        """
        Inicializa el visualizador.
        
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
    
    def create_visualization(
        self,
        objective_expr: str,
        var_names: List[str],
        critical_points: List[Dict[str, float]],
        optimal_point: Dict[str, float],
        optimal_value: float,
        filename: str = 'differential_plot.png'
    ) -> Optional[str]:
        """
        Genera visualización 2D del método de Cálculo Diferencial.
        
        Args:
            objective_expr: Expresión de la función objetivo
            var_names: Lista de nombres de variables
            critical_points: Lista de puntos críticos
            optimal_point: Diccionario con valores óptimos
            optimal_value: Valor de f en el punto óptimo
            filename: Nombre del archivo PNG a generar
            
        Returns:
            Ruta completa al archivo generado o None si hay error
        """
        # Validar que sea un problema 2D
        if len(var_names) != 2:
            print(f"⚠️ Visualización 2D solo disponible para problemas con 2 variables (recibidas: {len(var_names)})")
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
            
            # Calcular rango de visualización
            x_range, y_range = self._compute_plot_range(
                x_opt, y_opt,
                critical_points,
                margin_factor=1.5
            )
            
            # Crear malla
            x_mesh = np.linspace(x_range[0], x_range[1], 200)
            y_mesh = np.linspace(y_range[0], y_range[1], 200)
            X, Y = np.meshgrid(x_mesh, y_mesh)
            
            # Evaluar función
            with np.errstate(all='ignore'):
                Z = f_func(X, Y)
                Z = np.nan_to_num(Z, nan=np.nan, posinf=np.nan, neginf=np.nan)
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(8, 6), dpi=120)
            
            # Curvas de nivel
            contour = ax.contour(X, Y, Z, levels=15, cmap='viridis', alpha=0.6)
            contourf = ax.contourf(X, Y, Z, levels=15, cmap='viridis', alpha=0.3)
            
            # Colorbar
            cbar = plt.colorbar(contourf, ax=ax, shrink=0.8)
            cbar.set_label('f(x,y)', fontsize=9)
            
            # Puntos críticos (si hay más de uno)
            if len(critical_points) > 1:
                for cp in critical_points:
                    if cp != optimal_point:
                        x_cp = cp[var_names[0]]
                        y_cp = cp[var_names[1]]
                        
                        ax.plot(
                            x_cp, y_cp,
                            'o',
                            color='orange',
                            markersize=10,
                            markeredgecolor='darkorange',
                            markeredgewidth=2,
                            alpha=0.7,
                            label='Punto crítico'
                        )
            
            # Punto óptimo
            ax.plot(
                x_opt, y_opt,
                'o',
                color='lime',
                markersize=12,
                markeredgecolor='darkgreen',
                markeredgewidth=2,
                label='Óptimo',
                zorder=10
            )
            
            # Configuración
            ax.set_xlabel(var_names[0], fontsize=10)
            ax.set_ylabel(var_names[1], fontsize=10)
            ax.set_title('Cálculo Diferencial - Curvas de Nivel', fontsize=11, fontweight='bold')
            ax.legend(loc='best', fontsize=8.5, framealpha=0.9)
            ax.grid(True, alpha=0.3)
            ax.set_aspect('equal', adjustable='box')
            
            # Texto pedagógico
            textstr = f'Óptimo en ({x_opt:.2f}, {y_opt:.2f})\n∇f = 0 en este punto'
            props = dict(boxstyle='round,pad=0.5', facecolor='wheat', alpha=0.8)
            ax.text(
                0.02, 0.98,
                textstr,
                transform=ax.transAxes,
                fontsize=8.5,
                verticalalignment='top',
                bbox=props
            )
            
            plt.tight_layout()
            
            # Guardar
            output_path = os.path.join(self.output_dir, filename)
            plt.savefig(output_path, dpi=120, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            
            print(f"✅ Visualización 2D generada: {output_path}")
            
            # Retornar ruta relativa para usar en el servidor web
            return f"/static/tmp/{filename}"
            
        except Exception as e:
            print(f"❌ Error generando visualización 2D: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _compute_plot_range(
        self,
        x_opt: float,
        y_opt: float,
        critical_points: List[Dict[str, float]],
        margin_factor: float = 1.5
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Calcula rangos apropiados para la visualización."""
        x_vals = [x_opt]
        y_vals = [y_opt]
        
        for cp in critical_points:
            if len(cp) >= 2:
                x_vals.append(list(cp.values())[0])
                y_vals.append(list(cp.values())[1])
        
        x_min, x_max = min(x_vals), max(x_vals)
        y_min, y_max = min(y_vals), max(y_vals)
        
        x_margin = max(abs(x_max - x_min) * 0.3, 2.0)
        y_margin = max(abs(y_max - y_min) * 0.3, 2.0)
        
        x_range = (x_min - x_margin, x_max + x_margin)
        y_range = (y_min - y_margin, y_max + y_margin)
        
        return x_range, y_range


def generate_differential_plot(
    objective_expr: str,
    var_names: List[str],
    critical_points: List[Dict[str, float]],
    optimal_point: Dict[str, float],
    optimal_value: float,
    filename: str = 'differential.png'
) -> Optional[str]:
    """
    Función helper para generar visualización 2D.
    """
    visualizer = DifferentialVisualizer()
    return visualizer.create_visualization(
        objective_expr,
        var_names,
        critical_points,
        optimal_point,
        optimal_value,
        filename
    )
