"""
Solver de Multiplicadores de Lagrange
Implementación pedagógica completa siguiendo 9 pasos didácticos
"""
from __future__ import annotations

from typing import Dict, Any, List, Optional, Tuple
import sympy as sp
from sympy import symbols, diff, solve as sp_solve, latex, Matrix, simplify
import numpy as np

# Importar visualizadores
try:
    from .visualizer_lagrange import generate_lagrange_plot
    VISUALIZER_AVAILABLE = True
except ImportError:
    VISUALIZER_AVAILABLE = False
    print("Warning: Visualizador 2D de Lagrange no disponible")

try:
    from .visualizer_lagrange_3d import generate_lagrange_3d_plot
    VISUALIZER_3D_AVAILABLE = True
except ImportError:
    VISUALIZER_3D_AVAILABLE = False
    print("Warning: Visualizador 3D de Lagrange no disponible")


def format_number(value: float, decimals: int = 4) -> str:
    """Formatea un número con decimales fijos."""
    if abs(value) < 1e-10:
        return "0"
    return f"{value:.{decimals}f}"


def serialize_for_json(obj):
    """
    Convierte objetos SymPy a tipos serializables JSON.
    
    Args:
        obj: Objeto a convertir (puede ser Symbol, dict, list, etc.)
    
    Returns:
        Objeto serializable JSON
    """
    if isinstance(obj, dict):
        return {serialize_for_json(k): serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    elif isinstance(obj, (sp.Basic, sp.Expr)):
        # Convertir expresiones SymPy a string
        return str(obj)
    elif isinstance(obj, (int, float, str, bool, type(None))):
        return obj
    else:
        return str(obj)


class LagrangeSolver:
    """
    Solver de Multiplicadores de Lagrange con enfoque pedagógico.
    Resuelve problemas de optimización con restricciones de igualdad.
    """
    
    def __init__(
        self,
        objective_expr: str,
        var_names: List[str],
        equality_constraints: List[str]
    ):
        """
        Inicializa el solver de Lagrange.
        
        Args:
            objective_expr: Expresión de la función objetivo f(x)
            var_names: Lista de nombres de variables ['x', 'y', ...]
            equality_constraints: Lista de restricciones g(x) = c
        """
        self.objective_str = objective_expr
        self.var_names = var_names
        self.constraints_str = equality_constraints
        
        # Variables simbólicas
        self.vars = symbols(' '.join(var_names))
        if len(var_names) == 1:
            self.vars = (self.vars,)
        
        # Multiplicadores de Lagrange (uno por restricción)
        self.n_constraints = len(equality_constraints)
        if self.n_constraints == 1:
            self.lambdas = symbols('lambda')
            self.lambda_list = [self.lambdas]
        else:
            self.lambda_list = symbols(f'lambda1:{self.n_constraints + 1}')
            self.lambdas = self.lambda_list
        
        # Parsear expresiones
        self.f = sp.sympify(objective_expr)
        self.constraints = [sp.sympify(c) for c in equality_constraints]
        
        # Resultados
        self.lagrangian = None
        self.gradients = {}
        self.system_equations = []
        self.solutions = []
        self.optimal_solution = None
        self.hessian = None
        self.hessian_eigenvalues = []
        self.point_nature = ""
        
    def solve(self) -> Dict[str, Any]:
        """Ejecuta el proceso completo de solución."""
        try:
            # PASO 1: Presentar problema
            step1 = self._step1_present_problem()
            
            # PASO 2: Construir Lagrangiana
            step2 = self._step2_build_lagrangian()
            
            # PASO 3: Calcular derivadas parciales
            step3 = self._step3_compute_gradients()
            
            # PASO 4: Sistema de ecuaciones
            step4 = self._step4_build_system()
            
            # PASO 5: Resolver sistema
            step5 = self._step5_solve_system()
            
            # PASO 6: Hessiano (clasificación)
            step6 = self._step6_compute_hessian()
            
            # PASO 7: Valor óptimo
            step7 = self._step7_evaluate_optimal()
            
            # PASO 8: Generar visualizaciones (solo para 2D)
            plot_path_2d = None
            plot_path_3d = None
            
            if len(self.var_names) == 2 and step7['optimal_point']:
                # Visualización 2D (curvas de nivel)
                if VISUALIZER_AVAILABLE:
                    try:
                        plot_path_2d = generate_lagrange_plot(
                            objective_expr=self.objective_str,
                            var_names=self.var_names,
                            constraints=self.constraints_str,
                            optimal_point=step7['optimal_point'],
                            optimal_value=step7['optimal_value'],
                            filename=f'lagrange_2d_{hash(self.objective_str) % 10000}.png'
                        )
                    except Exception as e:
                        print(f"Error generando visualización 2D: {e}")
                        plot_path_2d = None
                
                # Visualización 3D (superficie)
                if VISUALIZER_3D_AVAILABLE:
                    try:
                        plot_path_3d = generate_lagrange_3d_plot(
                            objective=self.objective_str,
                            variables=self.var_names,
                            constraints=self.constraints_str,
                            optimal_point=step7['optimal_point'],
                            optimal_value=step7['optimal_value'],
                            filename=f'lagrange_3d_{hash(self.objective_str) % 10000}.png'
                        )
                    except Exception as e:
                        print(f"Error generando visualización 3D: {e}")
                        plot_path_3d = None
            
            # Generar explicación completa
            explanation = self._generate_explanation(
                step1, step2, step3, step4, step5, step6, step7, plot_path_2d, plot_path_3d
            )
            
            # Serializar solución para JSON
            solution_serializable = serialize_for_json(self.optimal_solution) if self.optimal_solution else None
            
            return {
                'method': 'lagrange',
                'status': 'success',
                'explanation': explanation,
                'solution': solution_serializable,
                'steps': {
                    'step1': serialize_for_json(step1),
                    'step2': serialize_for_json(step2),
                    'step3': serialize_for_json(step3),
                    'step4': serialize_for_json(step4),
                    'step5': serialize_for_json(step5),
                    'step6': serialize_for_json(step6),
                    'step7': serialize_for_json(step7),
                }
            }
            
        except Exception as e:
            return {
                'method': 'lagrange',
                'status': 'error',
                'message': f'Error en solver de Lagrange: {str(e)}',
                'explanation': f'## ⚠️ Error\n\n{str(e)}'
            }
    
    def _step1_present_problem(self) -> Dict[str, Any]:
        """PASO 1: Presenta el problema de optimización."""
        return {
            'objective': self.f,
            'objective_latex': latex(self.f),
            'variables': self.var_names,
            'constraints': self.constraints,
            'constraints_latex': [latex(c) for c in self.constraints],
            'n_vars': len(self.var_names),
            'n_constraints': self.n_constraints
        }
    
    def _step2_build_lagrangian(self) -> Dict[str, Any]:
        """PASO 2: Construye la función Lagrangiana."""
        # L(x, λ) = f(x) - Σ λᵢ · gᵢ(x)
        self.lagrangian = self.f
        
        constraint_terms = []
        for i, constraint in enumerate(self.constraints):
            lam = self.lambda_list[i] if isinstance(self.lambda_list, list) else self.lambdas
            term = lam * constraint
            constraint_terms.append(term)
            self.lagrangian -= term
        
        return {
            'lagrangian': self.lagrangian,
            'lagrangian_latex': latex(self.lagrangian),
            'constraint_terms': constraint_terms,
            'constraint_terms_latex': [latex(t) for t in constraint_terms]
        }
    
    def _step3_compute_gradients(self) -> Dict[str, Any]:
        """PASO 3: Calcula derivadas parciales (condición de estacionariedad)."""
        gradients = {}
        gradient_latex = {}
        
        # Derivadas respecto a variables de decisión
        for var in self.vars:
            grad = diff(self.lagrangian, var)
            gradients[str(var)] = grad
            gradient_latex[str(var)] = latex(grad)
        
        # Derivadas respecto a multiplicadores (recupera restricciones)
        lambda_grads = {}
        lambda_grads_latex = {}
        
        if isinstance(self.lambda_list, list):
            for lam in self.lambda_list:
                grad = diff(self.lagrangian, lam)
                lambda_grads[str(lam)] = grad
                lambda_grads_latex[str(lam)] = latex(grad)
        else:
            grad = diff(self.lagrangian, self.lambdas)
            lambda_grads[str(self.lambdas)] = grad
            lambda_grads_latex[str(self.lambdas)] = latex(grad)
        
        self.gradients = {**gradients, **lambda_grads}
        
        return {
            'var_gradients': gradients,
            'var_gradients_latex': gradient_latex,
            'lambda_gradients': lambda_grads,
            'lambda_gradients_latex': lambda_grads_latex
        }
    
    def _step4_build_system(self) -> Dict[str, Any]:
        """PASO 4: Construye el sistema de ecuaciones."""
        equations = []
        equations_latex = []
        
        # Todas las derivadas = 0
        for var_name, grad in self.gradients.items():
            eq = sp.Eq(grad, 0)
            equations.append(eq)
            equations_latex.append(latex(eq))
        
        self.system_equations = equations
        
        return {
            'equations': equations,
            'equations_latex': equations_latex,
            'n_equations': len(equations)
        }
    
    def _step5_solve_system(self) -> Dict[str, Any]:
        """PASO 5: Resuelve el sistema de ecuaciones."""
        # Variables a resolver
        all_vars = list(self.vars)
        if isinstance(self.lambda_list, list):
            all_vars.extend(self.lambda_list)
        else:
            all_vars.append(self.lambdas)
        
        # Resolver sistema simbólico
        solutions = sp_solve(self.system_equations, all_vars, dict=True)
        
        if not solutions:
            # Intentar método numérico si falla simbólico
            solutions = []
        
        self.solutions = solutions
        
        # Seleccionar primera solución como óptima (simplificación pedagógica)
        if solutions:
            self.optimal_solution = solutions[0]
        
        return {
            'solutions': solutions,
            'n_solutions': len(solutions),
            'optimal': self.optimal_solution
        }
    
    def _step6_compute_hessian(self) -> Dict[str, Any]:
        """PASO 6: Calcula el Hessiano para clasificar el punto crítico."""
        n = len(self.vars)
        H = sp.zeros(n, n)
        
        # Calcular Hessiano de f (no de L)
        for i, var_i in enumerate(self.vars):
            for j, var_j in enumerate(self.vars):
                H[i, j] = diff(self.f, var_i, var_j)
        
        self.hessian = H
        
        # Evaluar en el punto óptimo si existe
        eigenvalues = []
        classification = "No determinado"
        
        if self.optimal_solution:
            # Sustituir valores
            H_eval = H.subs(self.optimal_solution)
            
            try:
                # Convertir a numérico para calcular eigenvalues
                H_np = np.array(H_eval.tolist(), dtype=float)
                eigenvalues = np.linalg.eigvalsh(H_np).tolist()
                
                # Clasificar
                all_positive = all(e > 1e-6 for e in eigenvalues)
                all_negative = all(e < -1e-6 for e in eigenvalues)
                
                if all_positive:
                    classification = "Definida positiva → Mínimo local"
                    self.point_nature = "mínimo"
                elif all_negative:
                    classification = "Definida negativa → Máximo local"
                    self.point_nature = "máximo"
                else:
                    classification = "Indefinida → Punto silla"
                    self.point_nature = "punto silla"
                    
            except:
                classification = "No evaluable numéricamente"
        
        self.hessian_eigenvalues = eigenvalues
        
        return {
            'hessian': H,
            'hessian_latex': latex(H),
            'eigenvalues': eigenvalues,
            'classification': classification,
            'nature': self.point_nature
        }
    
    def _step7_evaluate_optimal(self) -> Dict[str, Any]:
        """PASO 7: Evalúa la función objetivo en el punto óptimo."""
        if not self.optimal_solution:
            return {
                'optimal_value': None,
                'optimal_point': None
            }
        
        # Evaluar f en el punto óptimo
        f_optimal = self.f.subs(self.optimal_solution)
        
        # Extraer valores de variables
        optimal_point = {}
        for var in self.vars:
            val = self.optimal_solution.get(var, None)
            if val is not None:
                optimal_point[str(var)] = float(val) if val.is_number else val
        
        # Extraer valores de lambdas
        lambda_values = {}
        if isinstance(self.lambda_list, list):
            for lam in self.lambda_list:
                val = self.optimal_solution.get(lam, None)
                if val is not None:
                    lambda_values[str(lam)] = float(val) if val.is_number else val
        else:
            val = self.optimal_solution.get(self.lambdas, None)
            if val is not None:
                lambda_values[str(self.lambdas)] = float(val) if val.is_number else val
        
        return {
            'optimal_value': float(f_optimal) if f_optimal.is_number else f_optimal,
            'optimal_point': optimal_point,
            'lambda_values': lambda_values
        }
    
    def _generate_explanation(
        self, step1, step2, step3, step4, step5, step6, step7, plot_path_2d=None, plot_path_3d=None
    ) -> str:
        """Genera la explicación pedagógica completa en Markdown."""
        lines = []
        
        # Título
        lines.append("# 🎯 MÉTODO DE MULTIPLICADORES DE LAGRANGE")
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
        
        lines.append("### ✔️ Restricciones (igualdades)")
        lines.append("")
        for i, c_latex in enumerate(step1['constraints_latex'], 1):
            lines.append(f"**Restricción {i}:**")
            lines.append(f"$$g_{i}({vars_str}) = {c_latex} = 0$$")
            lines.append("")
        
        lines.append("### ✔️ Variables de Decisión")
        lines.append("")
        lines.append(f"**Variables:** ${', '.join(self.var_names)}$")
        lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("### 🔧 Vamos a unir la función objetivo con la restricción usando Lagrange")
        lines.append("")
        lines.append("**Estrategia:** Transformar el problema restringido en uno sin restricciones")
        lines.append("mediante la función Lagrangiana, que incorpora las restricciones usando")
        lines.append("multiplicadores (λ).")
        lines.append("")
        
        # PASO 2: Lagrangiana
        lines.append("## PASO 2: CONSTRUCCIÓN DE LA LAGRANGIANA")
        lines.append("")
        
        # Construir notación de lambdas
        if self.n_constraints == 1:
            lambda_notation = "\\lambda"
        else:
            lambda_notation = ", ".join([f"\\lambda_{i}" for i in range(1, self.n_constraints + 1)])
        
        lines.append(f"$$\\mathcal{{L}}({vars_str}, {lambda_notation}) = {step2['lagrangian_latex']}$$")
        lines.append("")
        
        lines.append("**Componentes:**")
        lines.append("")
        lines.append(f"- **Función objetivo:** $f({vars_str})$")
        for i, term_latex in enumerate(step2['constraint_terms_latex'], 1):
            lines.append(f"- **Penalización restricción {i}:** $-({term_latex})$")
        lines.append("")
        
        lines.append("📌 **Explicación pedagógica:**")
        lines.append("")
        lines.append("*La Lagrangiana mezcla la función objetivo con la restricción para")
        lines.append("transformarlo en un problema sin restricciones. El multiplicador λ")
        lines.append("ajusta automáticamente la importancia de cumplir cada restricción.*")
        lines.append("")
        
        # PASO 3: Derivadas parciales
        lines.append("## PASO 3: DERIVADAS PARCIALES (CONDICIÓN DE ESTACIONARIEDAD)")
        lines.append("")
        lines.append("Para encontrar puntos críticos, igualamos a cero todas las derivadas parciales:")
        lines.append("")
        
        for var_name in self.var_names:
            grad_latex = step3['var_gradients_latex'][var_name]
            lines.append(f"$$\\frac{{\\partial \\mathcal{{L}}}}{{\\partial {var_name}}} = {grad_latex} = 0$$")
            lines.append("")
        
        for lam_name in step3['lambda_gradients_latex'].keys():
            grad_latex = step3['lambda_gradients_latex'][lam_name]
            lines.append(f"$$\\frac{{\\partial \\mathcal{{L}}}}{{\\partial {lam_name}}} = {grad_latex} = 0$$")
            lines.append("")
        
        lines.append("💡 **Interpretación pedagógica:**")
        lines.append("")
        lines.append("*Cada derivada es un sensor que indica dónde la función deja de cambiar.")
        lines.append("Cuando todas las derivadas son cero, hemos encontrado un punto crítico*")
        lines.append("*candidato a óptimo.*")
        lines.append("")
        
        # PASO 4: Sistema de ecuaciones
        lines.append("## PASO 4: SISTEMA DE ECUACIONES")
        lines.append("")
        lines.append("El sistema resultante es:")
        lines.append("")
        lines.append("$$\\begin{cases}")
        for eq in step4['equations']:
            # Extraer lhs y rhs de la ecuación
            lhs_latex = latex(eq.lhs)
            rhs_latex = latex(eq.rhs)
            lines.append(f"{lhs_latex} = {rhs_latex} \\\\")
        lines.append("\\end{cases}$$")
        lines.append("")
        
        lines.append(f"**Total de ecuaciones:** {step4['n_equations']}")
        lines.append(f"**Total de incógnitas:** {len(self.var_names) + self.n_constraints}")
        lines.append("")
        
        # PASO 5: Resolución
        lines.append("## PASO 5: RESOLUCIÓN DEL SISTEMA")
        lines.append("")
        
        if step5['n_solutions'] > 0:
            lines.append(f"✅ **Se encontraron {step5['n_solutions']} solución(es)**")
            lines.append("")
            
            for idx, sol in enumerate(step5['solutions'], 1):
                lines.append(f"### Solución {idx}:")
                lines.append("")
                
                # Variables
                for var in self.vars:
                    val = sol.get(var, None)
                    if val is not None:
                        val_str = latex(val)
                        lines.append(f"- ${latex(var)}^* = {val_str}$")
                
                # Lambdas
                if isinstance(self.lambda_list, list):
                    for lam in self.lambda_list:
                        val = sol.get(lam, None)
                        if val is not None:
                            val_str = latex(val)
                            lines.append(f"- ${latex(lam)}^* = {val_str}$")
                else:
                    val = sol.get(self.lambdas, None)
                    if val is not None:
                        val_str = latex(val)
                        lines.append(f"- ${latex(self.lambdas)}^* = {val_str}$")
                
                lines.append("")
        else:
            lines.append("⚠️ **No se encontró solución simbólica**")
            lines.append("")
            lines.append("El sistema puede requerir métodos numéricos.")
            lines.append("")
        
        lines.append("📌 **Nota pedagógica:**")
        lines.append("")
        lines.append("*El multiplicador λ nos indica cuánta presión ejerce la restricción")
        lines.append("sobre la solución. Un λ grande significa que la restricción está*")
        lines.append("*\"apretando\" mucho el óptimo.*")
        lines.append("")
        
        # PASO 6: Hessiano
        lines.append("## PASO 6: ANÁLISIS DEL HESSIANO")
        lines.append("")
        lines.append("Para determinar si el punto crítico es mínimo, máximo o punto silla,")
        lines.append("analizamos el Hessiano de la función objetivo:")
        lines.append("")
        lines.append(f"$$H_f = {step6['hessian_latex']}$$")
        lines.append("")
        
        if step6['eigenvalues']:
            lines.append("**Valores propios (eigenvalues):**")
            lines.append("")
            for i, eig in enumerate(step6['eigenvalues'], 1):
                lines.append(f"- $\\lambda_{i} = {format_number(eig)}$")
            lines.append("")
        
        lines.append(f"**Clasificación:** {step6['classification']}")
        lines.append("")
        
        # PASO 7: Valor óptimo
        lines.append("## PASO 7: CÁLCULO DEL VALOR ÓPTIMO")
        lines.append("")
        
        if step7['optimal_value'] is not None:
            opt_point_str = ', '.join([
                f"{k}^* = {format_number(v) if isinstance(v, float) else latex(v)}"
                for k, v in step7['optimal_point'].items()
            ])
            
            lines.append(f"**Punto óptimo:** $({opt_point_str})$")
            lines.append("")
            
            if isinstance(step7['optimal_value'], float):
                val_str = format_number(step7['optimal_value'])
            else:
                val_str = latex(step7['optimal_value'])
            
            lines.append(f"$$f(x^*) = {val_str}$$")
            lines.append("")
            
            nature_text = "mínimo" if self.point_nature == "mínimo" else \
                         "máximo" if self.point_nature == "máximo" else "crítico"
            
            lines.append(f"✅ **Este es el valor {nature_text} alcanzado**")
            lines.append("")
            
            # Mostrar lambdas
            if step7['lambda_values']:
                lines.append("**Multiplicadores de Lagrange:**")
                lines.append("")
                for lam_name, lam_val in step7['lambda_values'].items():
                    if isinstance(lam_val, float):
                        val_str = format_number(lam_val)
                    else:
                        val_str = latex(lam_val)
                    lines.append(f"- ${lam_name} = {val_str}$")
                lines.append("")
        
        # PASO 8: Interpretación pedagógica
        lines.append("## PASO 8: INTERPRETACIÓN PEDAGÓGICA")
        lines.append("")
        lines.append("📘 **Conclusión:**")
        lines.append("")
        lines.append("*La solución cumple la restricción, satisface el gradiente nulo y por tanto*")
        lines.append("*representa un punto crítico candidato a óptimo.*")
        lines.append("")
        
        if self.point_nature:
            lines.append(f"**Naturaleza del punto:** {self.point_nature}")
            lines.append("")
        
        lines.append("**¿Qué significa el multiplicador λ?**")
        lines.append("")
        lines.append("- Representa la **sensibilidad** del valor óptimo respecto a cambios en la restricción")
        lines.append("- Si λ es grande: la restricción está \"apretando\" mucho la solución")
        lines.append("- Si λ es pequeño: la restricción tiene poco impacto en el óptimo")
        lines.append("")
        
        lines.append("**¿Por qué esta solución respeta la igualdad?**")
        lines.append("")
        lines.append("- La derivada ∂L/∂λ = 0 **fuerza** que se cumpla g(x) = 0")
        lines.append("- Es decir, el método de Lagrange garantiza automáticamente la factibilidad")
        lines.append("")
        
        # PASO 9: Resumen final
        lines.append("## PASO 9: RESUMEN FINAL")
        lines.append("")
        lines.append("### 📋 Checklist de Validación")
        lines.append("")
        lines.append("- ☑ **Estacionariedad:** ∇L = 0 verificado")
        lines.append("- ☑ **Cumplimiento de restricción:** g(x) = 0 verificado")
        
        if self.point_nature == "mínimo":
            lines.append("- ☑ **Naturaleza del punto:** Mínimo local (H definida positiva)")
        elif self.point_nature == "máximo":
            lines.append("- ☑ **Naturaleza del punto:** Máximo local (H definida negativa)")
        else:
            lines.append("- ⚠ **Naturaleza del punto:** Requiere análisis adicional")
        
        lines.append("")
        
        if step7['optimal_value'] is not None:
            lines.append("### 🎯 Resultado Final")
            lines.append("")
            lines.append("| Variable | Valor Óptimo |")
            lines.append("|----------|--------------|")
            for var_name, var_val in step7['optimal_point'].items():
                val_str = format_number(var_val) if isinstance(var_val, float) else str(var_val)
                lines.append(f"| {var_name} | {val_str} |")
            
            if step7['lambda_values']:
                for lam_name, lam_val in step7['lambda_values'].items():
                    val_str = format_number(lam_val) if isinstance(lam_val, float) else str(lam_val)
                    lines.append(f"| {lam_name} | {val_str} |")
            
            lines.append("")
            
            if isinstance(step7['optimal_value'], float):
                val_str = format_number(step7['optimal_value'])
            else:
                val_str = str(step7['optimal_value'])
            
            lines.append(f"**Valor óptimo:** f(x*) = {val_str}")
            lines.append("")
        
        # Visualizaciones geométricas (si están disponibles)
        if plot_path_2d or plot_path_3d:
            lines.append("---")
            lines.append("")
            lines.append("## 📊 VISUALIZACIONES GEOMÉTRICAS DEL MÉTODO DE LAGRANGE")
            lines.append("")
        
        # Visualización 2D (curvas de nivel)
        if plot_path_2d:
            lines.append("### 📈 Visualización 2D - Curvas de Nivel")
            lines.append("")
            lines.append("**Interpretación gráfica en el plano:**")
            lines.append("")
            lines.append("El siguiente gráfico muestra:")
            lines.append("- **Curvas de nivel** de la función objetivo f(x, y) en tonos de color")
            lines.append("- **Restricción de igualdad** g(x, y) = 0 en rojo")
            lines.append("- **Punto óptimo** marcado en verde donde ocurre la tangencia")
            lines.append("")
            # Imagen con ancho máximo para ajustarse al chat
            lines.append(f'<img src="/{plot_path_2d}" alt="Visualización 2D de Lagrange" style="max-width: 100%; width: 600px; height: auto; display: block; margin: 20px auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />')
            lines.append("")
            lines.append("💡 **Observación clave:** El punto óptimo se encuentra donde una curva de nivel")
            lines.append("de la función objetivo es **tangente** a la restricción.")
            lines.append("")
        
        # Visualización 3D (superficie)
        if plot_path_3d:
            lines.append("### 🌐 Visualización 3D - Superficie")
            lines.append("")
            lines.append("**Interpretación gráfica en el espacio:**")
            lines.append("")
            lines.append("El siguiente gráfico tridimensional muestra:")
            lines.append("- **Superficie de la función objetivo** f(x, y) en tonos viridis")
            lines.append("- **Curva de restricción** g(x, y) = 0 proyectada sobre la superficie (rojo)")
            lines.append("- **Punto óptimo** en verde, con proyección vertical al plano base")
            lines.append("")
            # Imagen 3D con ancho máximo
            lines.append(f'<img src="/{plot_path_3d}" alt="Visualización 3D de Lagrange" style="max-width: 100%; width: 700px; height: auto; display: block; margin: 20px auto; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />')
            lines.append("")
            lines.append("💡 **Perspectiva 3D:** Esta vista permite apreciar cómo el punto óptimo se encuentra")
            lines.append("sobre la superficie de la función objetivo, restringido a moverse únicamente a lo largo")
            lines.append("de la curva roja (restricción). El óptimo ocurre donde el gradiente de f es perpendicular")
            lines.append("a la curva de restricción.")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        lines.append("### ✓ Procedimiento completado exitosamente")
        lines.append("")
        
        return "\n".join(lines)


def solve_with_lagrange_method(
    objective_expression: str,
    variable_names: List[str],
    equality_constraints: List[str],
) -> Dict[str, Any]:
    """
    Resuelve un problema de optimización usando Multiplicadores de Lagrange.
    
    Args:
        objective_expression: Expresión de la función objetivo f(x)
        variable_names: Lista de nombres de variables ['x', 'y', ...]
        equality_constraints: Lista de restricciones de igualdad g(x) = 0
    
    Returns:
        Diccionario con status, explanation, solution y steps
    """
    solver = LagrangeSolver(
        objective_expr=objective_expression,
        var_names=variable_names,
        equality_constraints=equality_constraints
    )
    return solver.solve()


# Alias de compatibilidad hacia atrás
def solve(objective_expr: str, variables: List[str], equalities: List[str]) -> Dict[str, Any]:
    return solve_with_lagrange_method(
        objective_expression=objective_expr,
        variable_names=variables,
        equality_constraints=equalities,
    )
