"""
Solver de Cálculo Diferencial
Implementación pedagógica completa para optimización sin restricciones
usando derivadas parciales y análisis del Hessiano
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
import sympy as sp
from sympy import symbols, diff, solve as sp_solve, latex, Matrix, simplify, hessian
import numpy as np

# Importar visualizadores
try:
    from .visualizer_differential import generate_differential_plot
    VISUALIZER_AVAILABLE = True
except ImportError:
    VISUALIZER_AVAILABLE = False
    print("Warning: Visualizador 2D de Cálculo Diferencial no disponible")

try:
    from .visualizer_differential_3d import generate_differential_3d_plot
    VISUALIZER_3D_AVAILABLE = True
except ImportError:
    VISUALIZER_3D_AVAILABLE = False
    print("Warning: Visualizador 3D de Cálculo Diferencial no disponible")


def format_number(value: float, decimals: int = 4) -> str:
    """Formatea un número con decimales fijos."""
    if abs(value) < 1e-10:
        return "0"
    return f"{value:.{decimals}f}"


def serialize_for_json(obj):
    """
    Convierte objetos SymPy a tipos serializables JSON.
    
    Args:
        obj: Objeto a serializar (puede ser Symbol, Expr, dict, list, etc.)
        
    Returns:
        Versión serializable del objeto
    """
    if isinstance(obj, (sp.Symbol, sp.Expr, sp.Basic)):
        return str(obj)
    elif isinstance(obj, dict):
        # Convertir tanto claves como valores
        return {str(k) if isinstance(k, (sp.Symbol, sp.Expr, sp.Basic)) else k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj)


class DifferentialSolver:
    """
    Solver para optimización sin restricciones usando Cálculo Diferencial.
    
    Pasos pedagógicos:
    1. Presentar el problema
    2. Calcular el gradiente (∇f)
    3. Encontrar puntos críticos (∇f = 0)
    4. Calcular el Hessiano (H)
    5. Clasificar puntos críticos (eigenvalores)
    6. Evaluar función en puntos críticos
    7. Interpretación y conclusiones
    """
    
    def __init__(
        self,
        objective_expression: str,
        variable_names: List[str]
    ):
        """
        Inicializa el solver de Cálculo Diferencial.
        
        Args:
            objective_expression: Expresión de la función objetivo f(x)
            variable_names: Lista de nombres de variables
        """
        self.objective_str = objective_expression
        self.var_names = variable_names
        self.n_vars = len(variable_names)
        
        # Crear símbolos de SymPy
        self.vars = [symbols(name, real=True) for name in variable_names]
        
        # Parsear expresión objetivo usando los símbolos creados
        try:
            # Crear diccionario local de símbolos
            local_dict = {var.name: var for var in self.vars}
            self.objective = sp.sympify(objective_expression, locals=local_dict)
        except Exception as e:
            raise ValueError(f"Error parseando función objetivo: {e}")
        
        # Resultados
        self.gradient = None
        self.critical_points = []
        self.hessian_matrix = None
        self.optimal_point = None
        self.optimal_value = None  # Valor óptimo de f
        self.point_nature = ""
        
    def solve(self) -> Dict[str, Any]:
        """Ejecuta el proceso completo de solución."""
        try:
            # PASO 1: Presentar problema
            step1 = self._step1_present_problem()
            
            # PASO 2: Calcular gradiente
            step2 = self._step2_compute_gradient()
            
            # PASO 3: Encontrar puntos críticos
            step3 = self._step3_find_critical_points()
            
            # PASO 4: Calcular Hessiano
            step4 = self._step4_compute_hessian()
            
            # PASO 5: Clasificar puntos críticos
            step5 = self._step5_classify_critical_points()
            
            # PASO 6: Evaluar función en puntos críticos
            step6 = self._step6_evaluate_function()
            
            # PASO 7: Generar visualizaciones (solo para 2D)
            plot_path_2d = None
            plot_path_3d = None
            
            if self.n_vars == 2 and step6.get('optimal_point'):
                # Visualización 2D (curvas de nivel)
                if VISUALIZER_AVAILABLE:
                    try:
                        plot_path_2d = generate_differential_plot(
                            objective_expr=self.objective_str,
                            var_names=self.var_names,
                            critical_points=step3['critical_points_numeric'],
                            optimal_point=step6['optimal_point'],
                            optimal_value=step6['optimal_value'],
                            filename=f'differential_2d_{hash(self.objective_str) % 10000}.png'
                        )
                    except Exception as e:
                        print(f"Error generando visualización 2D: {e}")
                        plot_path_2d = None
                
                # Visualización 3D (superficie)
                if VISUALIZER_3D_AVAILABLE:
                    try:
                        plot_path_3d = generate_differential_3d_plot(
                            objective=self.objective_str,
                            variables=self.var_names,
                            critical_points=step3['critical_points_numeric'],
                            optimal_point=step6['optimal_point'],
                            optimal_value=step6['optimal_value'],
                            point_nature=self.point_nature,
                            filename=f'differential_3d_{hash(self.objective_str) % 10000}.png'
                        )
                    except Exception as e:
                        print(f"Error generando visualización 3D: {e}")
                        plot_path_3d = None
            
            # Generar explicación completa
            explanation = self._generate_explanation(
                step1, step2, step3, step4, step5, step6, plot_path_2d, plot_path_3d
            )
            
            # Serializar solución para JSON
            solution_serializable = serialize_for_json(self.optimal_point) if self.optimal_point else None
            
            return {
                'method': 'differential',
                'status': 'success',
                'explanation': explanation,
                'solution': solution_serializable,
                'critical_points': step3.get('critical_points_numeric', []),
                'optimal_point': self.optimal_point,
                'optimal_value': self.optimal_value,
                'nature': self.point_nature,
                'plot_2d_path': plot_path_2d,
                'plot_3d_path': plot_path_3d,
                'steps': {
                    'step1': serialize_for_json(step1),
                    'step2': serialize_for_json(step2),
                    'step3': serialize_for_json(step3),
                    'step4': serialize_for_json(step4),
                    'step5': serialize_for_json(step5),
                    'step6': serialize_for_json(step6),
                }
            }
            
        except Exception as e:
            return {
                'method': 'differential',
                'status': 'error',
                'error': str(e),
                'explanation': f"## ❌ Error en Cálculo Diferencial\n\n{str(e)}"
            }
    
    def _step1_present_problem(self) -> Dict[str, Any]:
        """Paso 1: Presentar el problema de optimización."""
        return {
            'objective_latex': latex(self.objective),
            'objective_str': self.objective_str,
            'variables': self.var_names,
            'n_vars': self.n_vars,
            'problem_type': 'sin restricciones'
        }
    
    def _step2_compute_gradient(self) -> Dict[str, Any]:
        """Paso 2: Calcular el gradiente ∇f."""
        self.gradient = [diff(self.objective, var) for var in self.vars]
        
        return {
            'gradient': self.gradient,
            'gradient_latex': [latex(g) for g in self.gradient],
            'n_components': len(self.gradient)
        }
    
    def _step3_find_critical_points(self) -> Dict[str, Any]:
        """Paso 3: Encontrar puntos críticos resolviendo ∇f = 0."""
        # Resolver sistema ∇f = 0
        try:
            solutions = sp_solve(self.gradient, self.vars, dict=True)
            
            if not solutions:
                return {
                    'critical_points': [],
                    'critical_points_numeric': [],
                    'n_points': 0,
                    'status': 'no_solution'
                }
            
            # Convertir a valores numéricos
            critical_points_numeric = []
            for sol in solutions:
                try:
                    point_numeric = {}
                    for var in self.vars:
                        val = sol.get(var, 0)
                        # Intentar convertir a float
                        try:
                            point_numeric[str(var)] = float(val.evalf())
                        except:
                            point_numeric[str(var)] = float(val)
                    critical_points_numeric.append(point_numeric)
                except Exception as e:
                    print(f"No se pudo convertir solución a numérico: {e}")
                    continue
            
            self.critical_points = solutions
            
            return {
                'critical_points': solutions,
                'critical_points_numeric': critical_points_numeric,
                'n_points': len(solutions),
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'critical_points': [],
                'critical_points_numeric': [],
                'n_points': 0,
                'status': 'error',
                'error': str(e)
            }
    
    def _step4_compute_hessian(self) -> Dict[str, Any]:
        """Paso 4: Calcular la matriz Hessiana."""
        try:
            self.hessian_matrix = hessian(self.objective, self.vars)
            
            return {
                'hessian': self.hessian_matrix,
                'hessian_latex': latex(self.hessian_matrix),
                'shape': f"{self.n_vars}×{self.n_vars}"
            }
        except Exception as e:
            return {
                'hessian': None,
                'error': str(e),
                'status': 'error'
            }
    
    def _step5_classify_critical_points(self) -> Dict[str, Any]:
        """Paso 5: Clasificar puntos críticos usando eigenvalores del Hessiano."""
        if not self.critical_points or self.hessian_matrix is None:
            return {
                'classifications': [],
                'status': 'no_points'
            }
        
        classifications = []
        
        for i, point in enumerate(self.critical_points):
            try:
                # Evaluar Hessiano en el punto crítico
                H_at_point = self.hessian_matrix.subs(point)
                
                # Calcular eigenvalores
                eigenvals = list(H_at_point.eigenvals().keys())
                eigenvals_numeric = [float(ev.evalf()) for ev in eigenvals]
                
                # Clasificar basado en eigenvalores
                if all(ev > 0 for ev in eigenvals_numeric):
                    nature = "mínimo local"
                    definitude = "definida positiva"
                elif all(ev < 0 for ev in eigenvals_numeric):
                    nature = "máximo local"
                    definitude = "definida negativa"
                elif any(abs(ev) < 1e-10 for ev in eigenvals_numeric):
                    nature = "degenerado"
                    definitude = "semidefinida"
                else:
                    nature = "punto silla"
                    definitude = "indefinida"
                
                classifications.append({
                    'point_index': i,
                    'point': point,
                    'eigenvalues': eigenvals_numeric,
                    'nature': nature,
                    'definitude': definitude
                })
                
            except Exception as e:
                classifications.append({
                    'point_index': i,
                    'point': point,
                    'error': str(e),
                    'nature': 'desconocido'
                })
        
        return {
            'classifications': classifications,
            'n_classified': len(classifications),
            'status': 'success'
        }
    
    def _step6_evaluate_function(self) -> Dict[str, Any]:
        """Paso 6: Evaluar la función en los puntos críticos."""
        if not self.critical_points:
            return {
                'evaluations': [],
                'optimal_point': None,
                'optimal_value': None,
                'status': 'no_points'
            }
        
        evaluations = []
        
        for i, point in enumerate(self.critical_points):
            try:
                # Evaluar f en el punto
                f_value = float(self.objective.subs(point).evalf())
                
                # Extraer valores numéricos del punto
                point_numeric = {}
                for var in self.vars:
                    val = point.get(var, 0)
                    try:
                        point_numeric[str(var)] = float(val.evalf())
                    except:
                        point_numeric[str(var)] = float(val)
                
                evaluations.append({
                    'point_index': i,
                    'point': point,
                    'point_numeric': point_numeric,
                    'f_value': f_value
                })
                
            except Exception as e:
                evaluations.append({
                    'point_index': i,
                    'point': point,
                    'error': str(e)
                })
        
        # Determinar el punto óptimo (por ahora, el primero encontrado)
        if evaluations and 'f_value' in evaluations[0]:
            self.optimal_point = evaluations[0]['point_numeric']
            self.optimal_value = evaluations[0]['f_value']
        else:
            self.optimal_point = None
            self.optimal_value = None
        
        return {
            'evaluations': evaluations,
            'optimal_point': self.optimal_point,
            'optimal_value': self.optimal_value,
            'n_evaluations': len(evaluations),
            'status': 'success'
        }
    
    def _generate_explanation(
        self, step1, step2, step3, step4, step5, step6, plot_path_2d=None, plot_path_3d=None
    ) -> str:
        """Genera la explicación pedagógica completa en Markdown."""
        lines = []
        
        # Título
        lines.append("# 📐 MÉTODO DE CÁLCULO DIFERENCIAL")
        lines.append("")
        lines.append("**Optimización sin restricciones usando derivadas**")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # PASO 1: Presentación del problema
        lines.append("## PASO 1: PRESENTACIÓN DEL PROBLEMA")
        lines.append("")
        lines.append("### ✔️ Función Objetivo")
        lines.append("")
        vars_str = ', '.join(self.var_names)
        lines.append(f"$$f({vars_str}) = {step1['objective_latex']}$$")
        lines.append("")
        lines.append(f"**Tipo de problema:** {step1['problem_type']}")
        lines.append("")
        lines.append("### ✔️ Variables de Decisión")
        lines.append("")
        lines.append(f"**Variables:** ${', '.join(self.var_names)}$")
        lines.append(f"**Dimensión:** {step1['n_vars']}")
        lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("### 🔧 Estrategia de Solución")
        lines.append("")
        lines.append("Para problemas **sin restricciones**, buscamos puntos donde el gradiente se anula:")
        lines.append("$$\\nabla f = 0$$")
        lines.append("")
        lines.append("Luego clasificamos estos puntos críticos usando el **Hessiano**.")
        lines.append("")
        
        # PASO 2: Gradiente
        lines.append("## PASO 2: CÁLCULO DEL GRADIENTE")
        lines.append("")
        lines.append("El gradiente es el vector de derivadas parciales:")
        lines.append("")
        lines.append("$$\\nabla f = \\begin{bmatrix}")
        for i, (var, grad_latex) in enumerate(zip(self.var_names, step2['gradient_latex'])):
            lines.append(f"\\frac{{\\partial f}}{{\\partial {var}}} \\\\")
        lines.append("\\end{bmatrix}$$")
        lines.append("")
        
        lines.append("**Componentes del gradiente:**")
        lines.append("")
        for var, grad, grad_latex in zip(self.var_names, step2['gradient'], step2['gradient_latex']):
            lines.append(f"$$\\frac{{\\partial f}}{{\\partial {var}}} = {grad_latex}$$")
            lines.append("")
        
        lines.append("💡 **Interpretación:** El gradiente apunta en la dirección de máximo crecimiento de f.")
        lines.append("")
        
        # PASO 3: Puntos críticos
        lines.append("## PASO 3: PUNTOS CRÍTICOS (∇f = 0)")
        lines.append("")
        lines.append("Resolvemos el sistema:")
        lines.append("")
        
        # Construir sistema de ecuaciones con formato correcto
        system_lines = []
        for var, grad_latex in zip(self.var_names, step2['gradient_latex']):
            system_lines.append(f"{grad_latex} &= 0")
        
        lines.append("$$\\begin{aligned}")
        lines.append(" \\\\ ".join(system_lines))
        lines.append("\\end{aligned}$$")
        lines.append("")
        
        if step3['n_points'] > 0:
            lines.append(f"✅ **Se encontraron {step3['n_points']} punto(s) crítico(s)**")
            lines.append("")
            
            for i, point in enumerate(step3['critical_points'], 1):
                lines.append(f"### Punto Crítico {i}:")
                lines.append("")
                for var in self.vars:
                    if var in point:
                        val_latex = latex(point[var])
                        lines.append(f"- ${latex(var)}^* = {val_latex}$")
                lines.append("")
        else:
            lines.append("❌ **No se encontraron puntos críticos**")
            lines.append("")
        
        # PASO 4: Hessiano
        lines.append("## PASO 4: MATRIZ HESSIANA")
        lines.append("")
        lines.append("El Hessiano es la matriz de segundas derivadas:")
        lines.append("")
        lines.append(f"$$H = {step4.get('hessian_latex', 'Error')}$$")
        lines.append("")
        lines.append("💡 **Utilidad:** Los eigenvalores del Hessiano determinan la naturaleza del punto crítico.")
        lines.append("")
        
        # PASO 5: Clasificación (siempre mostrar)
        lines.append("## PASO 5: CLASIFICACIÓN DE PUNTOS CRÍTICOS")
        lines.append("")
        
        if step5.get('classifications') and len(step5['classifications']) > 0:
            for classification in step5['classifications']:
                i = classification['point_index'] + 1
                lines.append(f"### Análisis del Punto {i}:")
                lines.append("")
                
                if 'eigenvalues' in classification:
                    lines.append("**Valores propios del Hessiano:**")
                    lines.append("")
                    for j, ev in enumerate(classification['eigenvalues'], 1):
                        lines.append(f"- $\\lambda_{j} = {format_number(ev)}$")
                    lines.append("")
                    
                    lines.append(f"**Definitud:** {classification['definitude']}")
                    lines.append("")
                    lines.append(f"**Naturaleza:** {classification['nature']} 🎯")
                    lines.append("")
                    
                    # Guardar naturaleza para el primer punto
                    if i == 1:
                        self.point_nature = classification['nature']
                
                lines.append("---")
                lines.append("")
        else:
            lines.append("⚠️ **No se encontraron puntos críticos para clasificar.**")
            lines.append("")
            lines.append("Esto puede ocurrir cuando:")
            lines.append("- El sistema ∇f = 0 no tiene solución real")
            lines.append("- La función no tiene extremos locales en el dominio")
            lines.append("- Se requieren métodos numéricos para encontrar soluciones aproximadas")
            lines.append("")
        
        # PASO 6: Evaluación (siempre mostrar)
        lines.append("## PASO 6: EVALUACIÓN DE LA FUNCIÓN")
        lines.append("")
        
        if step6.get('optimal_point'):
            lines.append("**Punto óptimo encontrado:**")
            lines.append("")
            
            point_str = ", ".join([f"{var}^* = {format_number(val)}" for var, val in step6['optimal_point'].items()])
            lines.append(f"$({point_str})$")
            lines.append("")
            
            lines.append(f"$$f(x^*) = {format_number(step6['optimal_value'])}$$")
            lines.append("")
            
            if self.point_nature:
                if "mínimo" in self.point_nature:
                    lines.append(f"✅ **Este es un {self.point_nature}**")
                elif "máximo" in self.point_nature:
                    lines.append(f"✅ **Este es un {self.point_nature}**")
                else:
                    lines.append(f"⚠️ **Este es un {self.point_nature}**")
            lines.append("")
        else:
            lines.append("⚠️ **No se pudo evaluar la función en un punto óptimo.**")
            lines.append("")
            lines.append("Sin puntos críticos válidos, no es posible determinar el valor óptimo analíticamente.")
            lines.append("")
        
        # Interpretación
        lines.append("## PASO 7: INTERPRETACIÓN PEDAGÓGICA")
        lines.append("")
        lines.append("### 📘 ¿Qué hicimos?")
        lines.append("")
        lines.append("1. **Calculamos el gradiente**: Vector de derivadas parciales")
        lines.append("2. **Encontramos puntos críticos**: Donde ∇f = 0 (pendiente cero en todas direcciones)")
        lines.append("3. **Calculamos el Hessiano**: Matriz de segundas derivadas")
        lines.append("4. **Clasificamos el punto**: Usando eigenvalores (curvatura)")
        lines.append("5. **Evaluamos f**: Determinamos el valor óptimo")
        lines.append("")
        
        lines.append("### 🎯 Criterios de Clasificación")
        lines.append("")
        lines.append("| Eigenvalores del Hessiano | Naturaleza del Punto |")
        lines.append("|---------------------------|---------------------|")
        lines.append("| Todos positivos | Mínimo local |")
        lines.append("| Todos negativos | Máximo local |")
        lines.append("| Mixtos (+ y -) | Punto silla |")
        lines.append("| Alguno cero | Degenerado |")
        lines.append("")
        
        # Visualizaciones geométricas
        if plot_path_2d or plot_path_3d:
            lines.append("---")
            lines.append("")
            lines.append("## 📊 VISUALIZACIONES GEOMÉTRICAS")
            lines.append("")
        
        # Visualización 2D
        if plot_path_2d:
            lines.append("### 📈 Visualización 2D - Curvas de Nivel")
            lines.append("")
            lines.append("**Interpretación gráfica en el plano:**")
            lines.append("")
            lines.append("El siguiente gráfico muestra:")
            lines.append("- **Curvas de nivel** de la función objetivo f(x, y)")
            lines.append("- **Puntos críticos** marcados con círculos")
            lines.append("- **Punto óptimo** destacado en verde")
            lines.append("")
            lines.append(f'<img src="/{plot_path_2d}" alt="Visualización 2D" style="max-width: 100%; width: 600px; height: auto; display: block; margin: 20px auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />')
            lines.append("")
            lines.append("💡 **Observación:** Los puntos críticos están donde el gradiente es cero (nivel plano).")
            lines.append("")
        
        # Visualización 3D
        if plot_path_3d:
            lines.append("### 🌐 Visualización 3D - Superficie")
            lines.append("")
            lines.append("**Interpretación gráfica en el espacio:**")
            lines.append("")
            lines.append("El siguiente gráfico tridimensional muestra:")
            lines.append("- **Superficie de la función objetivo** f(x, y)")
            lines.append("- **Puntos críticos** marcados sobre la superficie")
            lines.append("- **Punto óptimo** destacado en verde brillante")
            lines.append("")
            lines.append(f'<img src="/{plot_path_3d}" alt="Visualización 3D" style="max-width: 100%; width: 700px; height: auto; display: block; margin: 20px auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />')
            lines.append("")
            
            if "mínimo" in self.point_nature:
                lines.append("💡 **Perspectiva 3D:** Se puede apreciar el 'valle' donde se encuentra el mínimo.")
            elif "máximo" in self.point_nature:
                lines.append("💡 **Perspectiva 3D:** Se puede apreciar la 'cima' donde se encuentra el máximo.")
            else:
                lines.append("💡 **Perspectiva 3D:** Se puede apreciar la geometría del punto crítico.")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("### ✓ Análisis completado exitosamente")
        lines.append("")
        
        return "\n".join(lines)


def solve_with_differential_method(
    objective_expression: str,
    variable_names: List[str],
) -> Dict[str, Any]:
    """
    Resuelve un problema de optimización sin restricciones usando Cálculo Diferencial.
    
    Args:
        objective_expression: Expresión de la función objetivo f(x)
        variable_names: Lista de nombres de variables
        
    Returns:
        Diccionario con la solución y explicación pedagógica
    """
    solver = DifferentialSolver(objective_expression, variable_names)
    return solver.solve()
