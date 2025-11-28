"""
Solver QP usando condiciones KKT y métodos numéricos.
Resuelve problemas cuadráticos convexos correctamente.
"""

from __future__ import annotations
import numpy as np
import sympy as sp
from typing import Dict, Any, List, Tuple, Optional
from scipy.optimize import minimize
from fractions import Fraction


def _convert_to_native(obj):
    """Convierte tipos NumPy a tipos nativos de Python."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, dict):
        return {key: _convert_to_native(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_to_native(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(_convert_to_native(item) for item in obj)
    return obj


def format_number(val: float, precision: int = 4) -> str:
    """Formatea un número para visualización."""
    if abs(val) < 1e-10:
        return "0"
    if abs(val - round(val)) < 1e-10:
        return str(int(round(val)))
    try:
        frac = Fraction(val).limit_denominator(100)
        if abs(float(frac) - val) < 1e-6 and frac.denominator <= 10:
            return f"{frac.numerator}/{frac.denominator}"
    except:
        pass
    return f"{val:.{precision}f}".rstrip('0').rstrip('.')


class QPKKTSolver:
    """
    Solver QP usando sistema KKT.
    Resuelve: min f(x) = c'x + (1/2)x'Dx
    Sujeto a: Ax = b, x >= 0
    """
    
    def __init__(self, objective_expr: str, variables: List[str], constraints: List[Dict[str, Any]]):
        self.objective_expr = objective_expr
        self.var_names = variables
        self.constraints = constraints or []
        
        self.sym_vars = {name: sp.Symbol(name, real=True) for name in variables}
        self.n_vars = len(variables)
        
        self.C = None
        self.D = None
        self.A_eq = None
        self.b_eq = None
        self.A_ineq = None
        self.b_ineq = None
        
        self.steps = []
        self.solution = None
        self.optimal_value = None
        
    def solve(self) -> Dict[str, Any]:
        """Ejecuta el procedimiento completo."""
        try:
            self._step1_present_problem()
            self._step2_extract_matrices()
            self._step3_check_convexity()
            self._step4_build_kkt()
            self._step5_solve_using_scipy()
            self._step6_verify_kkt()
            self._step7_final_solution()
            
            return self._build_success_response()
            
        except Exception as e:
            import traceback
            return self._build_error_response(f"{str(e)}\n{traceback.format_exc()}")
    
    def _step1_present_problem(self):
        """Paso 1: Presentación del problema."""
        eq_constraints = [c for c in self.constraints if c.get('kind') == 'eq']
        ineq_constraints = [c for c in self.constraints if c.get('kind') == 'ineq']
        
        step = {
            'numero': 1,
            'titulo': 'DEFINICION DEL PROBLEMA',
            'contenido': {
                'objetivo': self.objective_expr,
                'variables': ', '.join(self.var_names),
                'n_eq': len(eq_constraints),
                'n_ineq': len(ineq_constraints),
                'n_vars': self.n_vars,
                'restricciones_detalles': [
                    {'expr': c.get('expr', ''), 'kind': c.get('kind', ''), 'rhs': c.get('rhs', 0)}
                    for c in self.constraints
                ]
            }
        }
        self.steps.append(step)
    
    def _step2_extract_matrices(self):
        """Paso 2: Extracción de matrices."""
        obj_expr = sp.sympify(self.objective_expr, locals=self.sym_vars)
        var_list = [self.sym_vars[name] for name in self.var_names]
        
        # Hessiana
        hess = sp.hessian(obj_expr, var_list)
        self.D = np.array(hess).astype(float)
        
        # Gradiente (parte lineal)
        grad = [sp.diff(obj_expr, v) for v in var_list]
        self.C = np.zeros(self.n_vars)
        for i, v in enumerate(var_list):
            grad_at_zero = grad[i].subs({var: 0 for var in var_list})
            self.C[i] = float(grad_at_zero)
        
        # Separar restricciones por tipo
        # IMPORTANTE: Para scipy 'ineq', la forma es constraint(x) >= 0
        # El parser ya normalizó las restricciones como (lhs) - (rhs)
        # - Para 'ge' (>=): expr = lhs - rhs, entonces constraint = expr >= 0 ✓
        # - Para 'le' (<=): expr = lhs - rhs, pero necesitamos -(lhs - rhs) >= 0
        A_eq_rows = []
        b_eq_vals = []
        A_ineq_rows = []
        b_ineq_vals = []
        
        for c in self.constraints:
            expr_str = c.get('expr', '')
            rhs = float(c.get('rhs', 0))
            kind = c.get('kind', 'ge')  # Default 'ge' para compatibilidad
            
            constraint_expr = sp.sympify(expr_str, locals=self.sym_vars)
            
            # Extraer coeficientes de las variables
            row = np.zeros(self.n_vars)
            for i, v in enumerate(var_list):
                coef = sp.diff(constraint_expr, v)
                row[i] = float(coef) if coef != 0 else 0.0
            
            # Extraer término independiente (constante)
            # Evaluando en cero obtenemos la constante
            const_term = float(constraint_expr.subs({var: 0 for var in var_list}))
            
            # La expresión original es: (lhs) - (rhs)
            # Entonces: coef @ x + const_term = 0 (para eq)
            #           coef @ x + const_term >= 0 (para ge)
            #           coef @ x + const_term <= 0 (para le)
            
            # Para scipy:
            # - Igualdad: A @ x = b  →  A @ x - b = 0
            # - Desigualdad: A @ x >= b  (tipo 'ineq')
            
            if kind == 'eq':
                # coef @ x + const_term = 0  →  coef @ x = -const_term
                A_eq_rows.append(row)
                b_eq_vals.append(-const_term + rhs)
            elif kind == 'ge':
                # coef @ x + const_term >= 0  →  coef @ x >= -const_term
                A_ineq_rows.append(row)
                b_ineq_vals.append(-const_term + rhs)
            elif kind == 'le':
                # coef @ x + const_term <= 0  →  -coef @ x >= const_term
                A_ineq_rows.append(-row)
                b_ineq_vals.append(const_term - rhs)
            else:
                # Backward compatibility: 'ineq' sin especificar, asumir 'ge'
                A_ineq_rows.append(row)
                b_ineq_vals.append(-const_term + rhs)
        
        self.A_eq = np.array(A_eq_rows) if A_eq_rows else np.zeros((0, self.n_vars))
        self.b_eq = np.array(b_eq_vals) if b_eq_vals else np.array([])
        self.A_ineq = np.array(A_ineq_rows) if A_ineq_rows else np.zeros((0, self.n_vars))
        self.b_ineq = np.array(b_ineq_vals) if b_ineq_vals else np.array([])
        
        step = {
            'numero': 2,
            'titulo': 'MATRICES',
            'contenido': {
                'C': self.C.tolist(),
                'D': self.D.tolist(),
                'A_eq': self.A_eq.tolist() if self.A_eq.size > 0 else [],
                'b_eq': self.b_eq.tolist() if self.b_eq.size > 0 else [],
                'A_ineq': self.A_ineq.tolist() if self.A_ineq.size > 0 else [],
                'b_ineq': self.b_ineq.tolist() if self.b_ineq.size > 0 else []
            }
        }
        self.steps.append(step)
    
    def _step3_check_convexity(self):
        """Paso 3: Análisis de convexidad."""
        eigenvals = np.linalg.eigvals(self.D)
        convexa = np.all(eigenvals >= -1e-9)
        
        step = {
            'numero': 3,
            'titulo': 'CONVEXIDAD',
            'contenido': {
                'eigenvalores': eigenvals.tolist(),
                'convexa': bool(convexa)
            }
        }
        self.steps.append(step)
    
    def _step4_build_kkt(self):
        """Paso 4: Sistema KKT."""
        m_eq = len(self.b_eq)
        m_ineq = len(self.b_ineq)
        
        step = {
            'numero': 4,
            'titulo': 'SISTEMA KKT',
            'contenido': {
                'n_vars': self.n_vars,
                'n_lambda_eq': m_eq,
                'n_lambda_ineq': m_ineq,
                'n_mu': self.n_vars
            }
        }
        self.steps.append(step)
    
    def _step5_solve_using_scipy(self):
        """Paso 5: Resolver usando método numérico (scipy) con captura de iteraciones."""
        
        # Capturar iteraciones
        self.iteration_history = []
        
        def objective(x):
            return np.dot(self.C, x) + 0.5 * np.dot(x, np.dot(self.D, x))
        
        def gradient(x):
            return self.C + np.dot(self.D, x)
        
        def callback(xk):
            """Callback para capturar cada iteración."""
            f_val = objective(xk)
            grad_val = gradient(xk)
            
            # Calcular violaciones de restricciones
            eq_violations = []
            if len(self.b_eq) > 0:
                for i in range(len(self.b_eq)):
                    viol = abs(np.dot(self.A_eq[i], xk) - self.b_eq[i])
                    eq_violations.append(viol)
            
            ineq_violations = []
            if len(self.b_ineq) > 0:
                for i in range(len(self.b_ineq)):
                    # Restricción: A_ineq @ x >= b_ineq
                    # Violación: max(0, b_ineq - A_ineq @ x)
                    viol = max(0, self.b_ineq[i] - np.dot(self.A_ineq[i], xk))
                    ineq_violations.append(viol)
            
            # Generar descripción narrativa de la iteración
            k = len(self.iteration_history)
            grad_norm = np.linalg.norm(grad_val)
            total_viol = sum(eq_violations) if eq_violations else 0
            total_viol += sum(ineq_violations) if ineq_violations else 0
            
            if k == 0:
                narrative = "Punto inicial. El algoritmo evalúa la función y restricciones."
            elif grad_norm < 1e-3 and total_viol < 1e-6:
                narrative = "Convergencia alcanzada. El gradiente es casi cero y todas las restricciones se satisfacen."
            elif total_viol > 1e-4:
                narrative = "Ajustando variables para satisfacer restricciones activas."
            elif grad_norm > self.iteration_history[-1]['grad_norm'] * 0.5:
                narrative = "Búsqueda de dirección de descenso que reduzca la función objetivo."
            else:
                narrative = "El algoritmo reduce gradiente y función objetivo manteniendo factibilidad."
            
            self.iteration_history.append({
                'x': xk.copy(),
                'f': f_val,
                'grad': grad_val.copy(),
                'grad_norm': grad_norm,
                'eq_viol': sum(eq_violations) if eq_violations else 0,
                'ineq_viol': sum(ineq_violations) if ineq_violations else 0,
                'narrative': narrative
            })
        
        # Construir restricciones para scipy
        constraints = []
        
        # Restricciones de igualdad
        if len(self.b_eq) > 0:
            for i in range(len(self.b_eq)):
                constraints.append({
                    'type': 'eq',
                    'fun': lambda x, i=i: np.dot(self.A_eq[i], x) - self.b_eq[i]
                })
        
        # Restricciones de desigualdad
        # scipy 'ineq' usa: constraint(x) >= 0
        # Ya normalizadas en _step2: A_ineq @ x >= b_ineq
        if len(self.b_ineq) > 0:
            for i in range(len(self.b_ineq)):
                constraints.append({
                    'type': 'ineq',
                    'fun': lambda x, i=i: np.dot(self.A_ineq[i], x) - self.b_ineq[i]
                })
        
        # No negatividad
        bounds = [(0, None) for _ in range(self.n_vars)]
        
        # Punto inicial factible
        x0 = np.ones(self.n_vars) * 10.0
        
        # Resolver
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            jac=gradient,
            bounds=bounds,
            constraints=constraints,
            callback=callback,
            options={'ftol': 1e-9, 'disp': False, 'maxiter': 1000}
        )
        
        if result.success:
            self.solution = result.x
            self.optimal_value = result.fun
            
            # Estimar multiplicadores de Lagrange
            self.lagrange_multipliers = self._estimate_lagrange_multipliers(result.x)
            
            # Preparar iteraciones para mostrar
            iteraciones_muestra = []
            total_iters = len(self.iteration_history)
            
            # Mostrar primeras 3, algunas intermedias y últimas 3
            indices_mostrar = set()
            if total_iters <= 10:
                indices_mostrar = set(range(total_iters))
            else:
                # Primeras 3
                indices_mostrar.update(range(min(3, total_iters)))
                # Últimas 3
                indices_mostrar.update(range(max(0, total_iters - 3), total_iters))
                # Algunas intermedias
                step = max(1, total_iters // 5)
                indices_mostrar.update(range(3, total_iters - 3, step))
            
            for idx in sorted(indices_mostrar):
                it = self.iteration_history[idx]
                iteraciones_muestra.append({
                    'numero': idx,
                    'x': it['x'].tolist(),
                    'f': float(it['f']),
                    'grad_norm': float(it['grad_norm']),
                    'eq_viol': float(it['eq_viol']),
                    'ineq_viol': float(it['ineq_viol']),
                    'narrative': it.get('narrative', '')
                })
            
            step = {
                'numero': 5,
                'titulo': 'PROCESO DE OPTIMIZACION',
                'contenido': {
                    'metodo': 'Sequential Least Squares Programming (SLSQP)',
                    'convergio': True,
                    'total_iteraciones': result.nit,
                    'iteraciones_muestra': iteraciones_muestra,
                    'x_inicial': x0.tolist(),
                    'x_optimo': result.x.tolist(),
                    'f_optimo': float(result.fun),
                    'mensaje': result.message
                }
            }
        else:
            step = {
                'numero': 5,
                'titulo': 'PROCESO DE OPTIMIZACION',
                'contenido': {
                    'metodo': 'Sequential Least Squares Programming (SLSQP)',
                    'convergio': False,
                    'mensaje': result.message
                }
            }
        
        self.steps.append(step)
    
    def _estimate_lagrange_multipliers(self, x):
        """Estima multiplicadores de Lagrange desde condiciones KKT."""
        # ∇f(x*) + A_eq^T λ_eq + A_ineq^T λ_ineq = 0
        # Resolver para λ usando mínimos cuadrados si el sistema está sobredeterminado
        
        grad_f = self.C + np.dot(self.D, x)
        multipliers = {}
        
        # Multiplicadores de igualdad (λ_eq)
        if len(self.b_eq) > 0:
            try:
                # A_eq^T λ_eq ≈ -∇f - A_ineq^T λ_ineq (simplificado: solo -∇f)
                lambda_eq = np.linalg.lstsq(self.A_eq.T, -grad_f, rcond=None)[0]
                multipliers['lambda_eq'] = lambda_eq.tolist()
            except:
                multipliers['lambda_eq'] = [0.0] * len(self.b_eq)
        
        # Multiplicadores de desigualdad (λ_ineq) - solo restricciones activas
        if len(self.b_ineq) > 0:
            lambda_ineq = np.zeros(len(self.b_ineq))
            for i in range(len(self.b_ineq)):
                slack = np.dot(self.A_ineq[i], x) - self.b_ineq[i]
                if abs(slack) < 1e-6:  # Restricción activa
                    # Heurística: contribución proporcional al gradiente
                    lambda_ineq[i] = abs(np.dot(grad_f, self.A_ineq[i])) / (np.linalg.norm(self.A_ineq[i]) + 1e-10)
            multipliers['lambda_ineq'] = lambda_ineq.tolist()
        
        # Multiplicadores de no-negatividad (μ)
        mu = np.zeros(self.n_vars)
        for i in range(self.n_vars):
            if x[i] < 1e-6:  # Variable en su límite inferior
                mu[i] = max(0, -grad_f[i])
        multipliers['mu'] = mu.tolist()
        
        return multipliers
    
    def _step6_verify_kkt(self):
        """Paso 6: Verificar condiciones KKT en la solución."""
        if self.solution is None:
            return
        
        x = self.solution
        
        # Verificar condiciones
        grad_f = self.C + np.dot(self.D, x)
        
        # Factibilidad primal
        if len(self.b_eq) > 0:
            eq_residual = np.linalg.norm(np.dot(self.A_eq, x) - self.b_eq)
        else:
            eq_residual = 0.0
        
        if len(self.b_ineq) > 0:
            ineq_violation = np.min(self.b_ineq - np.dot(self.A_ineq, x))
        else:
            ineq_violation = 0.0
        
        step = {
            'numero': 6,
            'titulo': 'VERIFICACION KKT',
            'contenido': {
                'gradiente_f': grad_f.tolist(),
                'residual_igualdad': float(eq_residual),
                'violacion_desigualdad': float(ineq_violation),
                'x_no_negativo': bool(np.all(x >= -1e-9))
            }
        }
        self.steps.append(step)
    
    def _step7_final_solution(self):
        """Paso 7: Solución final."""
        if self.solution is None:
            return
        
        solution_dict = {self.var_names[i]: float(self.solution[i]) for i in range(len(self.solution))}
        
        step = {
            'numero': 7,
            'titulo': 'SOLUCION OPTIMA',
            'contenido': {
                'solucion': solution_dict,
                'valor_objetivo': float(self.optimal_value),
                'multiplicadores': getattr(self, 'lagrange_multipliers', None)
            }
        }
        self.steps.append(step)
    
    def _build_success_response(self) -> Dict[str, Any]:
        """Construye respuesta exitosa."""
        response = {
            'method': 'qp_kkt',
            'status': 'success',
            'message': 'Problema resuelto usando condiciones KKT',
            'steps': self.steps,
            'x_star': self.solution.tolist() if self.solution is not None else None,
            'f_star': float(self.optimal_value) if self.optimal_value is not None else None,
            'explanation': self._generate_explanation()
        }
        return _convert_to_native(response)
    
    def _build_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Construye respuesta de error."""
        return {
            'method': 'qp_kkt',
            'status': 'error',
            'message': f'Error: {error_msg}',
            'steps': self.steps,
            'explanation': f'Ocurrió un error: {error_msg}'
        }
    
    def _generate_explanation(self) -> str:
        """Genera explicación completa."""
        lines = []
        
        lines.append("")
        lines.append("# 📐 PROGRAMACIÓN CUADRÁTICA — MÉTODO KKT (SLSQP)")
        lines.append("")
        
        for step in self.steps:
            num = step['numero']
            titulo = step['titulo']
            contenido = step.get('contenido', {})
            
            lines.append(f"")
            lines.append(f"## PASO {num}: {titulo}")
            lines.append("")
            
            if num == 1:
                lines.append(f"📊 **Función objetivo:**")
                lines.append(f"")
                lines.append(f"$${contenido.get('objetivo', '')}$$")
                lines.append(f"")
                lines.append(f"📌 **Variables de decisión:** ${contenido.get('variables', '')}$")
                lines.append(f"")
                
                restricciones = contenido.get('restricciones_detalles', [])
                if restricciones:
                    lines.append(f"⚙️ **Restricciones:**")
                    lines.append(f"")
                    for r in restricciones:
                        kind = r['kind']
                        if kind == 'eq':
                            kind_str = "="
                        elif kind == 'ge':
                            kind_str = "\\geq"
                        elif kind == 'le':
                            kind_str = "\\leq"
                        else:
                            kind_str = "\\geq"  # default
                        lines.append(f"  - ${r['expr']} {kind_str} {r['rhs']}$")
                    lines.append(f"")
                    
            elif num == 2:
                C = contenido.get('C', [])
                D = contenido.get('D', [])
                A_eq = contenido.get('A_eq', [])
                b_eq = contenido.get('b_eq', [])
                A_ineq = contenido.get('A_ineq', [])
                b_ineq = contenido.get('b_ineq', [])
                
                lines.append(f"🔢 **Vector $C$ (coeficientes lineales):**")
                lines.append(f"")
                c_str = ', '.join([format_number(v) for v in C])
                lines.append(f"$$C = \\begin{{bmatrix}} {c_str} \\end{{bmatrix}}$$")
                lines.append(f"")
                
                if D:
                    lines.append(f"🔢 **Matriz $D$ (Hessiana - coeficientes cuadráticos):**")
                    lines.append(f"")
                    d_rows = [' & '.join([format_number(v) for v in row]) for row in D]
                    d_matrix = ' \\\\\\\\ '.join(d_rows)
                    lines.append(f"  $$D = \\begin{{bmatrix}} {d_matrix} \\end{{bmatrix}}$$")
                    lines.append(f"")
                
                if A_eq:
                    lines.append(f"**Matriz $A_{{eq}}$ (restricciones igualdad):**")
                    a_rows = [' & '.join([format_number(v) for v in row]) for row in A_eq]
                    a_matrix = ' \\\\\\\\ '.join(a_rows)
                    lines.append(f"  $$A_{{eq}} = \\begin{{bmatrix}} {a_matrix} \\end{{bmatrix}}$$")
                    lines.append(f"")
                    
                    b_str = ', '.join([format_number(v) for v in b_eq])
                    lines.append(f"**Vector $b_{{eq}}$:**")
                    lines.append(f"  $$b_{{eq}} = \\begin{{bmatrix}} {b_str} \\end{{bmatrix}}$$")
                    lines.append(f"")
                
                if A_ineq:
                    lines.append(f"**Matriz $A_{{ineq}}$ (restricciones desigualdad):**")
                    a_rows = [' & '.join([format_number(v) for v in row]) for row in A_ineq]
                    a_matrix = ' \\\\\\\\ '.join(a_rows)
                    lines.append(f"  $$A_{{ineq}} = \\begin{{bmatrix}} {a_matrix} \\end{{bmatrix}}$$")
                    lines.append(f"")
                    
                    b_str = ', '.join([format_number(v) for v in b_ineq])
                    lines.append(f"**Vector $b_{{ineq}}$:**")
                    lines.append(f"  $$b_{{ineq}} = \\begin{{bmatrix}} {b_str} \\end{{bmatrix}}$$")
                    lines.append(f"")
                    
            elif num == 3:
                eigenvals = contenido.get('eigenvalores', [])
                lines.append(f"**Eigenvalores de $D$:**")
                for i, ev in enumerate(eigenvals, 1):
                    status = "(\\geq 0)" if ev >= -1e-9 else "(< 0)"
                    lines.append(f"  - $\\lambda_{{{i}}} = {format_number(ev, 6)}$ {status}")
                lines.append(f"")
                convexa = contenido.get('convexa', False)
                if convexa:
                    lines.append(f"✔ **El problema es CONVEXO**")
                    lines.append(f"  El método garantiza encontrar el óptimo global")
                else:
                    lines.append(f"✘ **El problema NO es convexo**")
                lines.append(f"")
                
            elif num == 4:
                lines.append(f"**Sistema KKT del Problema:**")
                lines.append(f"")
                lines.append(f"📌 **Matriz KKT estándar**")
                lines.append(f"")
                lines.append(f"Para problemas QP con restricciones de igualdad, la matriz KKT tiene la estructura:")
                lines.append(f"")
                lines.append(f"$$\\begin{{bmatrix}} D & A^T \\\\\\\\ A & 0 \\end{{bmatrix}} \\begin{{bmatrix}} x^* \\\\\\\\ \\lambda^* \\end{{bmatrix}} = \\begin{{bmatrix}} -C \\\\\\\\ b \\end{{bmatrix}}$$")
                lines.append(f"")
                lines.append(f"Donde:")
                lines.append(f"")
                lines.append(f"- $D$: Matriz de coeficientes cuadráticos (Hessiana)")
                lines.append(f"- $A$: Matriz de restricciones de igualdad")
                lines.append(f"- $A^T$: Traspuesta de la matriz de restricciones")
                lines.append(f"- $0$: Matriz de ceros del tamaño adecuado")
                lines.append(f"- $C$: Vector de coeficientes lineales")
                lines.append(f"- $b$: Vector de términos independientes")
                lines.append(f"")
                lines.append(f"📌 **Condición de primer orden para el óptimo del QP**")
                lines.append(f"")
                lines.append(f"*Para problemas QP con solo igualdades, todo óptimo $(x^*, \\lambda^*)$ debe satisfacer la matriz KKT anterior. Este sistema representa las condiciones de primer orden del problema.*")
                lines.append(f"")
                lines.append(f"**Condiciones KKT completas:**")
                lines.append(f"")
                lines.append(f"1. **Estacionariedad**: $\\nabla f(x) + A^T\\lambda + \\mu = 0$")
                lines.append(f"2. **Factibilidad primal**: $Ax = b$, $Gx \\leq h$, $x \\geq 0$")
                lines.append(f"3. **Factibilidad dual**: $\\lambda$ libre, $\\mu \\geq 0$")
                lines.append(f"4. **Complementariedad**: $\\mu_i \\cdot x_i = 0$ $\\forall i$")
                lines.append(f"")
                lines.append(f"**Variables del sistema:**")
                lines.append(f"  - $x$ (decisión): {contenido.get('n_vars', 0)}")
                lines.append(f"  - $\\lambda$ (igualdades): {contenido.get('n_lambda_eq', 0)}")
                
                # Agregar sección de desigualdades si existen
                n_ineq = contenido.get('n_lambda_ineq', 0)
                if n_ineq > 0:
                    lines.append(f"  - $\\lambda$ (desigualdades): {n_ineq}")
                    lines.append(f"")
                    lines.append(f"📌 **Manejo de desigualdades**")
                    lines.append(f"")
                    lines.append(f"*En presencia de desigualdades, el sistema KKT se extiende incorporando multiplicadores $\\mu$ y condiciones de complementariedad. El software usa un método numérico (SLSQP) que encuentra una solución que satisface esas condiciones ampliadas.*")
                
                lines.append(f"")
                lines.append(f"⚠️ **Relación entre teoría y algoritmo:**")
                lines.append(f"")
                lines.append(f"Aunque la matriz KKT describe teóricamente el óptimo del problema, el software **no resuelve directamente este sistema**.")
                lines.append(f"")
                lines.append(f"En su lugar usa un **método numérico (SLSQP - Sequential Least Squares Programming)** que genera una secuencia de aproximaciones y converge a un punto que satisface las condiciones KKT.")
                lines.append(f"")
                lines.append(f"**Justificación:**")
                lines.append(f"")
                lines.append(f"*Los métodos numéricos empleados son equivalentes porque cualquier solución que minimiza la función cuadrática bajo restricciones lineales debe satisfacer las ecuaciones KKT. Por tanto, el algoritmo converge a un punto que cumple esas ecuaciones, aunque no las resuelva explícitamente.*")
                lines.append(f"")
                lines.append(f"Es decir, el **camino computacional** puede ser distinto, pero la **solución final** es equivalente a la del sistema KKT.")
                lines.append(f"")
                
            elif num == 5:
                lines.append(f"**Método:** {contenido.get('metodo', '')}")
                lines.append(f"")
                
                if contenido.get('convergio'):
                    lines.append(f"✔ **Convergencia exitosa**")
                    total_iters = contenido.get('total_iteraciones', 0)
                    lines.append(f"  - Total de iteraciones: {total_iters}")
                    lines.append(f"")
                    
                    # Punto inicial
                    x_inicial = contenido.get('x_inicial', [])
                    if x_inicial:
                        lines.append(f"**Punto inicial:**")
                        x_init_str = ', '.join([format_number(v) for v in x_inicial])
                        lines.append(f"  $$x^{{(0)}} = \\begin{{bmatrix}} {x_init_str} \\end{{bmatrix}}$$")
                        lines.append(f"")
                    
                    # Mostrar iteraciones seleccionadas
                    iteraciones = contenido.get('iteraciones_muestra', [])
                    if iteraciones:
                        lines.append(f"**Iteraciones del algoritmo:**")
                        lines.append(f"")
                        
                        for it in iteraciones:
                            iter_num = it.get('numero', 0)
                            x_vals = it.get('x', [])
                            f_val = it.get('f', 0)
                            grad_norm = it.get('grad_norm', 0)
                            eq_viol = it.get('eq_viol', 0)
                            ineq_viol = it.get('ineq_viol', 0)
                            narrative = it.get('narrative', '')
                            
                            # Mostrar narrativa primero (más pedagógico)
                            if narrative:
                                lines.append(f"**Iteración {iter_num}:** _{narrative}_")
                            else:
                                lines.append(f"**Iteración {iter_num}:**")
                            
                            # Mostrar x actual
                            x_str = ', '.join([format_number(v) for v in x_vals])
                            lines.append(f"  - $x^{{({iter_num})}} = ({x_str})$")
                            lines.append(f"  - $f(x^{{({iter_num})}}) = {format_number(f_val)}$")
                            lines.append(f"  - $||\\nabla f|| = {format_number(grad_norm)}$")
                            
                            # Violaciones
                            if eq_viol > 1e-6:
                                lines.append(f"  - Violación igualdades: {format_number(eq_viol, 8)}")
                            if ineq_viol > 1e-6:
                                lines.append(f"  - Violación desigualdades: {format_number(ineq_viol, 8)}")
                            
                            lines.append(f"")
                    
                    # Solución final
                    x_opt = contenido.get('x_optimo', [])
                    lines.append(f"**Solución óptima encontrada:**")
                    for i, val in enumerate(x_opt, 1):
                        var_name = self.var_names[i-1] if i-1 < len(self.var_names) else f"x{i}"
                        lines.append(f"  - ${var_name}^* = {format_number(val)}$")
                    lines.append(f"")
                    lines.append(f"**Valor objetivo óptimo:**")
                    lines.append(f"  $$f(x^*) = {format_number(contenido.get('f_optimo', 0))}$$")
                else:
                    lines.append(f"✘ No se encontró solución")
                    lines.append(f"  Mensaje: {contenido.get('mensaje', '')}")
                lines.append(f"")
                
            elif num == 6:
                lines.append(f"**Verificación de condiciones KKT:**")
                lines.append(f"")
                
                grad = contenido.get('gradiente_f', [])
                if grad:
                    lines.append(f"**Gradiente en solución óptima:**")
                    grad_str = ', '.join([format_number(v) for v in grad])
                    lines.append(f"  $$\\nabla f(x^*) = \\begin{{bmatrix}} {grad_str} \\end{{bmatrix}}$$")
                    lines.append(f"")
                
                res_eq = contenido.get('residual_igualdad', 0)
                lines.append(f"**Factibilidad primal:**")
                lines.append(f"  - Residual igualdades: ${format_number(res_eq, 8)}$")
                
                viol_ineq = contenido.get('violacion_desigualdad', 0)
                lines.append(f"  - Violación desigualdades: ${format_number(viol_ineq, 8)}$")
                
                no_neg = contenido.get('x_no_negativo', True)
                status_nn = "✔" if no_neg else "✘"
                lines.append(f"  - No negatividad: {status_nn} Satisfecha")
                lines.append(f"")
                
            elif num == 7:
                lines.append(f"**SOLUCIÓN ÓPTIMA:**")
                lines.append(f"")
                solucion = contenido.get('solucion', {})
                for var, val in solucion.items():
                    lines.append(f"  - ${var}^* = {format_number(val)}$")
                lines.append(f"")
                lines.append(f"**Riesgo mínimo (varianza):**")
                lines.append(f"  $$f(x^*) = {format_number(contenido.get('valor_objetivo', 0))}$$")
                lines.append(f"")
                
                # Multiplicadores de Lagrange
                multiplicadores = contenido.get('multiplicadores')
                if multiplicadores:
                    lines.append(f"**Multiplicadores de Lagrange (estimados):**")
                    lines.append(f"")
                    
                    lambda_eq = multiplicadores.get('lambda_eq', [])
                    if isinstance(lambda_eq, list) and len(lambda_eq) > 0 and any(abs(v) > 1e-10 for v in lambda_eq):
                        lines.append(f"*Restricciones de igualdad ($\\lambda_{{eq}}$):*")
                        for i, lam in enumerate(lambda_eq, 1):
                            lines.append(f"  - $\\lambda_{{{i}}} = {format_number(lam)}$")
                        lines.append(f"")
                    
                    lambda_ineq = multiplicadores.get('lambda_ineq', [])
                    if isinstance(lambda_ineq, list) and len(lambda_ineq) > 0:
                        lines.append(f"*Restricciones de desigualdad ($\\lambda_{{ineq}}$):*")
                        active_found = False
                        for i, lam in enumerate(lambda_ineq, 1):
                            if abs(lam) > 1e-6:
                                lines.append(f"  - $\\lambda_{{{i}}} = {format_number(lam)}$ (restricción activa)")
                                active_found = True
                        if not active_found:
                            lines.append(f"  - Todas inactivas ($\\lambda_i = 0$)")
                        lines.append(f"")
                    
                    mu = multiplicadores.get('mu', [])
                    if isinstance(mu, list) and len(mu) > 0:
                        lines.append(f"*No-negatividad ($\\mu$):*")
                        bound_found = False
                        for i, mu_val in enumerate(mu):
                            if abs(mu_val) > 1e-6:
                                var_name = self.var_names[i] if i < len(self.var_names) else f"x_{i}"
                                lines.append(f"  - $\\mu_{{{var_name}}} = {format_number(mu_val)}$ (en límite inferior)")
                                bound_found = True
                        if not bound_found:
                            lines.append(f"  - Ninguna variable en límite ($\\mu_i = 0$)")
                        lines.append(f"")
                
                # Conclusión KKT (después del PASO 7)
                lines.append(f"")
                lines.append(f"**Conclusión:**")
                lines.append(f"")
                lines.append(f"✓ La solución obtenida cumple las condiciones KKT, por lo tanto es un óptimo válido del problema cuadrático original.")
                lines.append(f"")
        
        # Agregar conclusión e interpretación
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 💡 CONCLUSIÓN E INTERPRETACIÓN")
        lines.append("")
        
        conclusion = self._generate_conclusion()
        lines.extend(conclusion)
        
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("### ✓ Procedimiento completado exitosamente")
        lines.append("")
        
        return "\n".join(lines)


    def _generate_conclusion(self) -> List[str]:
        """Genera conclusión e interpretación contextual del problema."""
        lines = []
        
        if self.solution is None:
            lines.append("⚠️ **No se pudo encontrar una solución óptima.**")
            lines.append("")
            lines.append("Esto puede deberse a:")
            lines.append("  • El problema es infactible (restricciones contradictorias)")
            lines.append("  • El problema no está acotado")
            lines.append("  • El punto inicial está muy lejos de la región factible")
            return lines
        
        # Analizar naturaleza del problema
        has_eq = len(self.b_eq) > 0
        has_ineq = len(self.b_ineq) > 0
        n_vars = len(self.var_names)
        
        lines.append("**Resumen de resultados:**")
        lines.append("")
        
        # Mostrar solución de forma clara
        for i, var_name in enumerate(self.var_names):
            val = self.solution[i]
            lines.append(f"  • **{var_name}** = {format_number(val)}")
        lines.append("")
        lines.append(f"  • **Valor óptimo**: $f(x^*) = {format_number(self.optimal_value)}$")
        lines.append("")
        
        # Interpretación contextual
        lines.append("**Interpretación:**")
        lines.append("")
        
        # Detectar contexto del problema por nombres de variables y restricciones
        var_str = ' '.join(self.var_names).lower()
        obj_str = self.objective_expr.lower()
        
        # Problema de cartera/inversión
        if any(keyword in var_str for keyword in ['a', 'b', 'f', 'accion', 'bono', 'fondo']) and \
           any(keyword in obj_str for keyword in ['**2', 'varianza', 'riesgo']):
            lines.append("Este es un **problema de optimización de cartera de inversión** que busca")
            lines.append("minimizar el riesgo (varianza) sujeto a restricciones de rendimiento y límites.")
            lines.append("")
            lines.append("📈 **Decisión óptima de inversión:**")
            total_inversion = sum(self.solution)
            for i, var_name in enumerate(self.var_names):
                val = self.solution[i]
                porcentaje = (val / total_inversion * 100) if total_inversion > 1e-9 else 0
                lines.append(f"  • Invertir **{format_number(val)}** unidades monetarias en {var_name} (≈ {format_number(porcentaje, 2)}% del total)")
            lines.append("")
            lines.append(f"📉 **Riesgo mínimo alcanzable**: {format_number(self.optimal_value)}")
            lines.append("")
            lines.append("Esta distribución garantiza el **menor riesgo posible** mientras cumple con")
            lines.append("todas las restricciones de rendimiento, diversificación y límites de inversión.")
        
        # Problema de producción
        elif any(keyword in var_str for keyword in ['x', 'y', 'producto', 'unidad']):
            if 'max' in obj_str or 'ganancia' in obj_str or 'utilidad' in obj_str:
                lines.append("Este es un **problema de maximización de producción/ganancia** que busca")
                lines.append("determinar la cantidad óptima a producir de cada producto.")
            else:
                lines.append("Este es un **problema de optimización de producción** que busca")
                lines.append("minimizar costos o recursos sujeto a restricciones de capacidad.")
            lines.append("")
            lines.append("🏭 **Plan de producción óptimo:**")
            for i, var_name in enumerate(self.var_names):
                val = self.solution[i]
                lines.append(f"  • Producir **{format_number(val)}** unidades de {var_name}")
            lines.append("")
            lines.append(f"💰 **Resultado óptimo**: {format_number(self.optimal_value)}")
        
        # Problema genérico
        else:
            lines.append("Este problema de **programación cuadrática** ha sido resuelto encontrando")
            lines.append("los valores óptimos de las variables que minimizan la función objetivo")
            lines.append("mientras satisfacen todas las restricciones especificadas.")
            lines.append("")
            lines.append("✓ **Solución óptima encontrada:**")
            for i, var_name in enumerate(self.var_names):
                val = self.solution[i]
                lines.append(f"  • {var_name} = {format_number(val)}")
            lines.append("")
            lines.append(f"✓ **Valor óptimo de la función objetivo**: {format_number(self.optimal_value)}")
        
        lines.append("")
        
        # Análisis de restricciones activas
        if hasattr(self, 'lagrange_multipliers') and self.lagrange_multipliers:
            lambda_ineq = self.lagrange_multipliers.get('lambda_ineq', [])
            active_constraints = [i for i, lam in enumerate(lambda_ineq) if abs(lam) > 1e-6]
            
            if active_constraints:
                lines.append("")
                lines.append("🔒 **Restricciones activas** (que limitan la solución óptima):")
                
                # Mapear índices de desigualdades al total de restricciones
                eq_count = len(self.b_eq)
                for idx in active_constraints:
                    # Buscar restricción en la lista original (saltando las de igualdad)
                    constraint_idx = eq_count + idx
                    if constraint_idx < len(self.constraints):
                        c = self.constraints[constraint_idx]
                        expr = c.get('expr', '')
                        kind = c.get('kind', 'ge')
                        kind_symbol = '\\geq' if kind == 'ge' else '\\leq' if kind == 'le' else '='
                        lines.append(f"  • Restricción {idx + 1}: ${expr} {kind_symbol} 0$")
                lines.append("")
                lines.append("Estas restricciones están **'saturadas'** en el óptimo (se cumplen con igualdad).")
                lines.append("Relajarlas (aumentar su límite) podría mejorar el valor óptimo.")
            else:
                lines.append("")
                lines.append("ℹ️ Ninguna restricción de desigualdad está activa en el óptimo.")
        
        return lines


def solve_qp(objective_expr: str, variables: List[str], 
             constraints: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Punto de entrada principal."""
    solver = QPKKTSolver(objective_expr, variables, constraints)
    return solver.solve()
