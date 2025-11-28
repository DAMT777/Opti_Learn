"""
Visualizador pedagógico para el Método de Multiplicadores de Lagrange
Genera gráficos que muestran curvas de nivel, restricciones y el punto óptimo
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


class LagrangeVisualizer:
    """
    Visualizador para problemas de Lagrange en 2D.
    Muestra curvas de nivel de la función objetivo y la restricción de igualdad.
    """
    
    def __init__(self, output_dir: str = None):
        """
        Inicializa el visualizador.
        
        Args:
            output_dir: Directorio donde guardar las imágenes generadas
        """
        if output_dir is None:
            # Detectar directorio del proyecto Django
            import os
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
        constraints: List[str],
        optimal_point: Dict[str, float],
        optimal_value: float,
        filename: str = 'lagrange_plot.png'
    ) -> Optional[str]:
        """
        Genera visualización del método de Lagrange.
        
        Args:
            objective_expr: Expresión de la función objetivo
            var_names: Nombres de las variables ['x', 'y']
            constraints: Lista de restricciones de igualdad
            optimal_point: Punto óptimo {'x': val, 'y': val}
            optimal_value: Valor de f en el punto óptimo
            filename: Nombre del archivo de salida
        
        Returns:
            Ruta relativa al archivo generado o None si falla
        """
        # Solo para problemas 2D
        if len(var_names) != 2:
            return None
        
        try:
            # Parsear expresiones
            x_sym, y_sym = symbols(var_names)
            f_expr = sp.sympify(objective_expr)
            
            # Convertir a función numérica
            f_func = lambdify([x_sym, y_sym], f_expr, 'numpy')
            
            # Parsear restricciones
            g_funcs = []
            for constraint in constraints:
                g_expr = sp.sympify(constraint)
                g_func = lambdify([x_sym, y_sym], g_expr, 'numpy')
                g_funcs.append(g_func)
            
            # Extraer punto óptimo
            x_opt = optimal_point.get(var_names[0], 0)
            y_opt = optimal_point.get(var_names[1], 0)
            
            # Determinar rango de visualización
            x_range, y_range = self._compute_plot_range(
                x_opt, y_opt, margin=3.0
            )
            
            # Crear malla
            x_vals = np.linspace(x_range[0], x_range[1], 400)
            y_vals = np.linspace(y_range[0], y_range[1], 400)
            X, Y = np.meshgrid(x_vals, y_vals)
            
            # Evaluar función objetivo
            Z = f_func(X, Y)
            
            # Crear figura con tamaño optimizado para chat
            fig, ax = plt.subplots(figsize=(8, 6))  # Más compacto: 8x6 en lugar de 10x8
            
            # 1. Curvas de nivel de la función objetivo (al menos 10)
            levels = 15  # Más de 10 para mejor visualización
            contour = ax.contour(
                X, Y, Z,
                levels=levels,
                cmap='viridis',
                alpha=0.6,
                linewidths=1.2  # Líneas más finas
            )
            
            # Rellenar curvas de nivel con color
            contourf = ax.contourf(
                X, Y, Z,
                levels=levels,
                cmap='viridis',
                alpha=0.3
            )
            
            # Colorbar más compacto
            cbar = plt.colorbar(contourf, ax=ax, shrink=0.8)
            cbar.set_label('f(x, y)', rotation=270, labelpad=15, fontsize=10)
            
            # 2. Dibujar restricciones de igualdad
            for i, g_func in enumerate(g_funcs, 1):
                # Evaluar restricción
                G = g_func(X, Y)
                
                # Dibujar curva g(x,y) = 0
                constraint_contour = ax.contour(
                    X, Y, G,
                    levels=[0],
                    colors='red',
                    linewidths=3,
                    linestyles='solid'
                )
                
                # Etiqueta para la restricción
                ax.clabel(
                    constraint_contour,
                    inline=True,
                    fontsize=10,
                    fmt=f'Restricción {i}'
                )
            
            # 3. Marcar punto óptimo
            ax.plot(
                x_opt, y_opt,
                'go',  # Green circle
                markersize=12,  # Más pequeño: 12 en lugar de 15
                markeredgewidth=2,
                markeredgecolor='darkgreen',
                label=f'Óptimo: ({x_opt:.2f}, {y_opt:.2f})',
                zorder=5  # Asegurar que esté al frente
            )
            
            # Texto junto al punto óptimo - más compacto
            ax.annotate(
                'Óptimo',
                xy=(x_opt, y_opt),
                xytext=(8, 8),  # Offset más pequeño
                textcoords='offset points',
                fontsize=9,
                fontweight='bold',
                color='darkgreen',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.8),
                arrowprops=dict(arrowstyle='->', color='darkgreen', lw=1.5)
            )
            
            # 4. Comentario pedagógico - más compacto
            pedagogical_text = (
                "El óptimo ocurre donde una curva de nivel\n"
                "es tangente a la restricción"
            )
            ax.text(
                0.02, 0.98,
                pedagogical_text,
                transform=ax.transAxes,
                fontsize=8.5,
                verticalalignment='top',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='wheat', alpha=0.85),
                style='italic'
            )
            
            # Configuración de ejes
            ax.set_xlabel(var_names[0], fontsize=11, fontweight='bold')
            ax.set_ylabel(var_names[1], fontsize=11, fontweight='bold')
            ax.set_title(
                'Visualización Geométrica - Método de Lagrange',
                fontsize=12,
                fontweight='bold',
                pad=12
            )
            
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
            ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
            
            # Mantener proporción pero sin forzar cuadrado perfecto
            # para aprovechar mejor el espacio
            
            # Guardar figura con mayor DPI para mejor calidad en menor tamaño
            filepath = os.path.join(self.output_dir, filename)
            plt.tight_layout()
            plt.savefig(filepath, dpi=120, bbox_inches='tight')  # DPI reducido de 150 a 120
            plt.close(fig)
            
            # Retornar ruta relativa (Django sirve static/ de cada app bajo /static/)
            return f'/static/tmp/{filename}'
            
        except Exception as e:
            print(f"Error generando visualización: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _compute_plot_range(
        self,
        x_opt: float,
        y_opt: float,
        margin: float = 3.0
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """
        Calcula el rango apropiado para el gráfico centrado en el óptimo.
        
        Args:
            x_opt: Coordenada x del óptimo
            y_opt: Coordenada y del óptimo
            margin: Margen alrededor del punto óptimo
        
        Returns:
            ((x_min, x_max), (y_min, y_max))
        """
        x_range = (x_opt - margin, x_opt + margin)
        y_range = (y_opt - margin, y_opt + margin)
        
        # Asegurar rango mínimo
        if x_range[1] - x_range[0] < 1:
            x_range = (x_opt - 1, x_opt + 1)
        if y_range[1] - y_range[0] < 1:
            y_range = (y_opt - 1, y_opt + 1)
        
        return x_range, y_range


def generate_lagrange_plot(
    objective_expr: str,
    var_names: List[str],
    constraints: List[str],
    optimal_point: Dict[str, float],
    optimal_value: float,
    filename: str = 'lagrange_plot.png'
) -> Optional[str]:
    """
    Función helper para generar visualización de Lagrange.
    
    Args:
        objective_expr: Expresión de la función objetivo
        var_names: Nombres de variables ['x', 'y']
        constraints: Lista de restricciones de igualdad
        optimal_point: Punto óptimo {'x': val, 'y': val}
        optimal_value: Valor óptimo de f
        filename: Nombre del archivo de salida
    
    Returns:
        Ruta relativa al archivo generado o None
    """
    visualizer = LagrangeVisualizer()
    return visualizer.create_visualization(
        objective_expr=objective_expr,
        var_names=var_names,
        constraints=constraints,
        optimal_point=optimal_point,
        optimal_value=optimal_value,
        filename=filename
    )
