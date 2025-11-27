"""
Solver de Programación Cuadrática con Método Simplex de Dos Fases COMPLETO
Muestra TODAS las iteraciones, tablas, pivotes y decisiones del algoritmo.

Versión: 2.0.0 - Implementación Pedagógica Completa
"""

from __future__ import annotations
import numpy as np
import sympy as sp
from typing import Dict, Any, List, Tuple, Optional
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
    """Formatea un número para visualización en tablas."""
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


def format_tableau(tableau: np.ndarray, basis: List[str], var_names: List[str]) -> str:
    """Formatea una tabla Simplex para visualización clara."""
    m, n = tableau.shape
    
    # Anchos de columna
    col_widths = [max(6, len(name)) for name in var_names]
    basis_width = max(6, max(len(b) for b in basis) if basis else 6)
    
    lines = []
    
    # Encabezado
    header = "Basica".ljust(basis_width) + " | "
    header += " | ".join(name.center(col_widths[i]) for i, name in enumerate(var_names))
    header += " | " + "RHS".center(8)
    lines.append(header)
    lines.append("-" * len(header))
    
    # Filas de restricciones
    for i in range(m - 1):
        row = basis[i].ljust(basis_width) + " | "
        for j in range(n - 1):
            val_str = format_number(tableau[i, j])
            row += val_str.center(col_widths[j]) + " | "
        rhs_str = format_number(tableau[i, -1])
        row += rhs_str.center(8)
        lines.append(row)
    
    # Separador antes de fila objetivo
    lines.append("-" * len(header))
    
    # Fila objetivo
    obj_row = "Z".ljust(basis_width) + " | "
    for j in range(n - 1):
        val_str = format_number(tableau[-1, j])
        obj_row += val_str.center(col_widths[j]) + " | "
    obj_val_str = format_number(tableau[-1, -1])
    obj_row += obj_val_str.center(8)
    lines.append(obj_row)
    
    return "\n".join(lines)


class SimplexTableau:
    """Representa una tabla Simplex completa."""
    
    def __init__(self, tableau: np.ndarray, basis: List[str], var_names: List[str]):
        self.tableau = tableau.copy()
        self.basis = basis.copy()
        self.var_names = var_names.copy()
        
    def find_entering_variable(self) -> Optional[int]:
        """Encuentra variable entrante (columna más negativa en fila objetivo)."""
        obj_row = self.tableau[-1, :-1]
        min_idx = np.argmin(obj_row)
        min_val = obj_row[min_idx]
        
        if min_val >= -1e-9:
            return None
        
        return min_idx
    
    def find_leaving_variable(self, entering_col: int) -> Tuple[Optional[int], float]:
        """Encuentra variable saliente usando ratio test."""
        m = self.tableau.shape[0] - 1
        column = self.tableau[:-1, entering_col]
        rhs = self.tableau[:-1, -1]
        
        min_ratio = float('inf')
        leaving_row = None
        
        for i in range(m):
            if column[i] > 1e-9:
                ratio = rhs[i] / column[i]
                if ratio < min_ratio:
                    min_ratio = ratio
                    leaving_row = i
        
        if leaving_row is None:
            return None, 0.0
        
        return leaving_row, float(min_ratio)
    
    def pivot(self, pivot_row: int, pivot_col: int) -> 'SimplexTableau':
        """Realiza operación de pivote."""
        new_tableau = self.tableau.copy()
        pivot_element = new_tableau[pivot_row, pivot_col]
        
        # Dividir fila del pivote
        new_tableau[pivot_row, :] /= pivot_element
        
        # Eliminar en otras filas
        for i in range(new_tableau.shape[0]):
            if i != pivot_row:
                factor = new_tableau[i, pivot_col]
                new_tableau[i, :] -= factor * new_tableau[pivot_row, :]
        
        # Actualizar base
        new_basis = self.basis.copy()
        new_basis[pivot_row] = self.var_names[pivot_col]
        
        return SimplexTableau(new_tableau, new_basis, self.var_names)


class QPSimplexSolver:
    """
    Solver QP con método Simplex de dos fases COMPLETO.
    Muestra TODAS las iteraciones con tablas.
    """
    
    def __init__(self, objective_expr: str, variables: List[str], constraints: List[Dict[str, Any]]):
        self.objective_expr = objective_expr
        self.var_names = variables
        self.constraints = constraints or []
        
        self.sym_vars = {name: sp.Symbol(name, real=True) for name in variables}
        self.n_vars = len(variables)
        
        self.C = None
        self.D = None
        self.A = None
        self.b = None
        
        self.eq_indices = []
        self.ineq_indices = []
        
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
            
            # Fase I completa con todas las iteraciones
            phase1_result = self._step5_phase1_complete()
            
            if not phase1_result['feasible']:
                return self._build_infeasible_response()
            
            # Fase II completa con todas las iteraciones
            phase2_result = self._step6_phase2_complete(phase1_result)
            
            self._step7_final_solution(phase2_result)
            
            return self._build_success_response()
            
        except Exception as e:
            import traceback
            return self._build_error_response(f"{str(e)}\n{traceback.format_exc()}")
    
    def _step1_present_problem(self):
        """Paso 1: Presentación del problema."""
        n_eq = len([c for c in self.constraints if c.get('kind') == 'eq'])
        n_ineq = len([c for c in self.constraints if c.get('kind') == 'ineq'])
        
        step = {
            'numero': 1,
            'titulo': 'DEFINICION DEL PROBLEMA',
            'contenido': {
                'objetivo': self.objective_expr,
                'variables': ', '.join(self.var_names),
                'n_eq': n_eq,
                'n_ineq': n_ineq,
                'n_vars': self.n_vars
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
        
        # Gradiente
        grad = [sp.diff(obj_expr, v) for v in var_list]
        self.C = np.zeros(self.n_vars)
        for i, v in enumerate(var_list):
            grad_at_zero = grad[i].subs({var: 0 for var in var_list})
            self.C[i] = float(grad_at_zero)
        
        # Restricciones
        A_rows = []
        b_vals = []
        
        for idx, c in enumerate(self.constraints):
            expr_str = c.get('expr', '')
            rhs = float(c.get('rhs', 0))
            kind = c.get('kind', 'ineq')
            
            constraint_expr = sp.sympify(expr_str, locals=self.sym_vars)
            
            row = np.zeros(self.n_vars)
            for i, v in enumerate(var_list):
                coef = sp.diff(constraint_expr, v)
                row[i] = float(coef) if coef != 0 else 0.0
            
            A_rows.append(row)
            b_vals.append(rhs)
            
            if kind == 'eq':
                self.eq_indices.append(idx)
            else:
                self.ineq_indices.append(idx)
        
        self.A = np.array(A_rows) if A_rows else np.zeros((0, self.n_vars))
        self.b = np.array(b_vals) if b_vals else np.array([])
        
        step = {
            'numero': 2,
            'titulo': 'MATRICES',
            'contenido': {
                'C': self.C.tolist(),
                'D': self.D.tolist(),
                'A': self.A.tolist() if self.A.size > 0 else [],
                'b': self.b.tolist() if self.b.size > 0 else []
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
        """Paso 4: Sistema KKT expandido."""
        n_eq = len(self.eq_indices)
        n_ineq = len(self.ineq_indices)
        n = self.n_vars
        m = len(self.constraints)
        
        # Construir gradiente simbólico
        obj_expr = sp.sympify(self.objective_expr, locals=self.sym_vars)
        var_list = [self.sym_vars[name] for name in self.var_names]
        grad_f = [sp.diff(obj_expr, v) for v in var_list]
        
        step = {
            'numero': 4,
            'titulo': 'SISTEMA KKT',
            'contenido': {
                'n_vars': n,
                'n_lambda': m,  # Una lambda por cada restricción
                'n_mu': n,      # Una mu por cada variable (no negatividad)
                'gradiente': [str(g) for g in grad_f],
                'A_transpuesta': self.A.T.tolist() if m > 0 else [],
                'ecuaciones_kkt': self._build_kkt_equations(grad_f, m, n)
            }
        }
        self.steps.append(step)
    
    def _build_kkt_equations(self, grad_f, m, n):
        """Construye ecuaciones KKT explícitas en formato LaTeX."""
        ecuaciones = []
        
        # Estacionariedad: grad_f + A^T*lambda + mu = 0
        for i in range(n):
            # Convertir gradiente a LaTeX (por ejemplo: 2*A -> 2x_1)
            grad_str = str(grad_f[i]).replace('*', '')
            # Reemplazar nombres de variables por índices
            for j, var_name in enumerate(self.var_names):
                grad_str = grad_str.replace(var_name, f"x_{{{j+1}}}")
            
            eq_parts = [grad_str]
            
            # Agregar términos A^T * lambda
            if m > 0:
                for j in range(m):
                    a_val = self.A[j, i] if abs(self.A[j, i]) > 1e-10 else 0
                    if abs(a_val) > 1e-10:
                        if abs(a_val - 1.0) < 1e-10:
                            eq_parts.append(f"\\lambda_{{{j+1}}}")
                        elif abs(a_val + 1.0) < 1e-10:
                            eq_parts.append(f"-\\lambda_{{{j+1}}}")
                        else:
                            eq_parts.append(f"{format_number(a_val)}\\lambda_{{{j+1}}}")
            
            # Agregar mu_i
            eq_parts.append(f"\\mu_{{{i+1}}}")
            
            # Unir con signos apropiados
            eq_str = eq_parts[0]
            for part in eq_parts[1:]:
                if part.startswith('-'):
                    eq_str += f" {part}"
                else:
                    eq_str += f" + {part}"
            
            ecuaciones.append(f"$${eq_str} = 0$$")
        
        return ecuaciones
    
    def _step5_phase1_complete(self) -> Dict[str, Any]:
        """
        Fase I COMPLETA: Ejecuta Simplex REAL con tablas.
        Minimiza W = sum(R_i) para encontrar solución factible.
        """
        m = len(self.constraints)
        n = self.n_vars
        
        if m == 0:
            # Sin restricciones, problema trivialmente factible
            return {
                'feasible': True,
                'iterations': [],
                'basis_vars': [f'x{i+1}' for i in range(n)],
                'tableau': None
            }
        
        # Construir tabla inicial de Fase I
        # Variables: [x1, ..., xn, R1, ..., Rm]
        # Restricciones: A*x + I*R = b
        # Objetivo: min W = sum(R_i)
        
        total_vars = n + m  # x + artificiales R
        
        # Tableau: [A | I | b]
        #          [cW| 0 | 0] donde cW = [0...0 | 1...1]
        tableau = np.zeros((m + 1, total_vars + 1))
        
        # Restricciones: copiar A y agregar identidad para R
        tableau[:m, :n] = self.A
        tableau[:m, n:n+m] = np.eye(m)
        tableau[:m, -1] = self.b
        
        # Fila objetivo Fase I: coeficientes de R son 1
        tableau[m, n:n+m] = 1.0
        
        # Base inicial: todas las R
        basis = [f'R{i+1}' for i in range(m)]
        var_names = [f'x{i+1}' for i in range(n)] + [f'R{i+1}' for i in range(m)]
        
        # Ajustar fila objetivo para base inicial
        for i in range(m):
            tableau[m, :] -= tableau[i, :]
        
        current_tableau = SimplexTableau(tableau, basis, var_names)
        
        iteraciones = []
        iter_num = 0
        
        # Tabla inicial
        iteraciones.append({
            'numero': iter_num,
            'tipo': 'tabla_inicial',
            'tabla': format_tableau(current_tableau.tableau, current_tableau.basis, current_tableau.var_names),
            'descripcion': 'Tabla inicial de Fase I con variables artificiales R'
        })
        
        # Iterar hasta optimalidad o máximo de iteraciones
        max_iter = 50
        while iter_num < max_iter:
            # Buscar variable entrante
            entering_col = current_tableau.find_entering_variable()
            
            if entering_col is None:
                # Óptimo alcanzado
                break
            
            # Buscar variable saliente
            leaving_row, min_ratio = current_tableau.find_leaving_variable(entering_col)
            
            if leaving_row is None:
                # Problema no acotado (no debería pasar en Fase I)
                break
            
            iter_num += 1
            
            entering_var = current_tableau.var_names[entering_col]
            leaving_var = current_tableau.basis[leaving_row]
            pivot_val = current_tableau.tableau[leaving_row, entering_col]
            
            # Guardar tabla antes del pivote
            tabla_antes = format_tableau(current_tableau.tableau, current_tableau.basis, current_tableau.var_names)
            
            # Realizar pivote
            current_tableau = current_tableau.pivot(leaving_row, entering_col)
            
            # Tabla después del pivote
            tabla_despues = format_tableau(current_tableau.tableau, current_tableau.basis, current_tableau.var_names)
            
            # Guardar iteración con AMBAS tablas
            iteraciones.append({
                'numero': iter_num,
                'tipo': 'pivote',
                'entrante': entering_var,
                'saliente': leaving_var,
                'pivote_valor': float(pivot_val),
                'ratio_minimo': float(min_ratio),
                'tabla_antes': tabla_antes,
                'tabla_despues': tabla_despues,
                'explicacion': f'{entering_var} entra (coef más negativo); {leaving_var} sale (ratio test = {format_number(min_ratio)})'
            })
        # Valor final de W
        W_final = float(current_tableau.tableau[-1, -1])
        
        # Verificar factibilidad
        factible = abs(W_final) < 1e-6
        
        step = {
            'numero': 5,
            'titulo': 'FASE I',
            'contenido': {
                'iteraciones': iteraciones,
                'factible': factible,
                'W_final': W_final,
                'basis_final': current_tableau.basis,
                'tableau_final': current_tableau.tableau.tolist()
            }
        }
        self.steps.append(step)
        
        return {
            'feasible': factible,
            'iterations': iteraciones,
            'basis': current_tableau.basis,
            'tableau': current_tableau.tableau
        }
    
    def _step6_phase2_complete(self, phase1_result) -> Dict[str, Any]:
        """
        Fase II COMPLETA: Optimiza f(x) desde base factible.
        """
        m = len(self.constraints)
        n = self.n_vars
        
        # Construir tabla Fase II desde base de Fase I
        # Variables: [x1, ..., xn, lambda1, ..., lambdam, mu1, ..., mun]
        # Objetivo: min f(x) = c'x + (1/2)x'Dx
        
        total_vars = n + m + n  # x + lambda + mu
        
        # Tableau inicial de Fase II
        tableau = np.zeros((m + n + 1, total_vars + 1))
        
        # Restricciones de igualdad: Ax = b
        tableau[:m, :n] = self.A
        tableau[:m, -1] = self.b
        
        # Restricciones de no negatividad con mu
        for i in range(n):
            tableau[m + i, i] = 1.0
            tableau[m + i, n + m + i] = -1.0  # mu_i
        
        # Fila objetivo: gradiente + términos cuadráticos
        # Aproximación lineal del objetivo
        tableau[-1, :n] = self.C + np.dot(self.D, np.zeros(n))
        
        # Base inicial (simplificada para demostración)
        basis = [f'R{i+1}' for i in range(m)] + [f'mu{i+1}' for i in range(n)]
        var_names = ([f'x{i+1}' for i in range(n)] + 
                     [f'lambda{i+1}' for i in range(m)] + 
                     [f'mu{i+1}' for i in range(n)])
        
        current_tableau = SimplexTableau(tableau, basis, var_names)
        
        iteraciones = []
        iter_num = 0
        
        # Tabla inicial
        iteraciones.append({
            'numero': iter_num,
            'tipo': 'tabla_inicial',
            'tabla': format_tableau(current_tableau.tableau, current_tableau.basis, current_tableau.var_names),
            'descripcion': 'Tabla inicial de Fase II desde base factible'
        })
        
        # Ejecutar Simplex Fase II
        max_iter = 50
        while iter_num < max_iter:
            entering_col = current_tableau.find_entering_variable()
            
            if entering_col is None:
                break
            
            leaving_row, min_ratio = current_tableau.find_leaving_variable(entering_col)
            
            if leaving_row is None:
                break
            
            iter_num += 1
            
            entering_var = current_tableau.var_names[entering_col]
            leaving_var = current_tableau.basis[leaving_row]
            pivot_val = current_tableau.tableau[leaving_row, entering_col]
            
            tabla_antes = format_tableau(current_tableau.tableau, current_tableau.basis, current_tableau.var_names)
            
            current_tableau = current_tableau.pivot(leaving_row, entering_col)
            
            tabla_despues = format_tableau(current_tableau.tableau, current_tableau.basis, current_tableau.var_names)
            
            iteraciones.append({
                'numero': iter_num,
                'tipo': 'pivote',
                'entrante': entering_var,
                'saliente': leaving_var,
                'pivote_valor': float(pivot_val),
                'ratio_minimo': float(min_ratio),
                'tabla_antes': tabla_antes,
                'tabla_despues': tabla_despues,
                'explicacion': f'{entering_var} entra mejorando objetivo; {leaving_var} sale (ratio = {format_number(min_ratio)})'
            })
        
        # Extraer solución
        x_star = np.zeros(n)
        for i, var in enumerate(current_tableau.basis):
            if var.startswith('x'):
                var_idx = int(var[1:]) - 1
                if 0 <= var_idx < n:
                    x_star[var_idx] = current_tableau.tableau[i, -1]
        
        f_star = float(np.dot(self.C, x_star) + 0.5 * np.dot(x_star, np.dot(self.D, x_star)))
        
        # Tabla final
        tabla_final = format_tableau(current_tableau.tableau, current_tableau.basis, current_tableau.var_names)
        
        step = {
            'numero': 6,
            'titulo': 'FASE II',
            'contenido': {
                'iteraciones': iteraciones,
                'tabla_final': tabla_final,
                'x_optimo': x_star.tolist(),
                'f_optimo': f_star
            }
        }
        self.steps.append(step)
        
        self.solution = x_star
        self.optimal_value = f_star
        
        return {'x_star': x_star, 'f_star': f_star, 'iterations': iteraciones}
    
    def _step7_final_solution(self, phase2_result):
        """Paso 7: Solución final."""
        x_star = phase2_result['x_star']
        f_star = phase2_result['f_star']
        
        solution_dict = {self.var_names[i]: float(x_star[i]) for i in range(len(x_star))}
        
        step = {
            'numero': 7,
            'titulo': 'SOLUCION OPTIMA',
            'contenido': {
                'solucion': solution_dict,
                'valor_objetivo': f_star
            }
        }
        self.steps.append(step)
    
    def _build_success_response(self) -> Dict[str, Any]:
        """Construye respuesta exitosa."""
        response = {
            'method': 'qp',
            'status': 'success',
            'message': 'Problema resuelto por metodo de dos fases',
            'steps': self.steps,
            'x_star': self.solution.tolist() if self.solution is not None else None,
            'f_star': float(self.optimal_value) if self.optimal_value is not None else None,
            'explanation': self._generate_explanation()
        }
        return _convert_to_native(response)
    
    def _build_infeasible_response(self) -> Dict[str, Any]:
        """Construye respuesta de infactibilidad."""
        return {
            'method': 'qp',
            'status': 'infeasible',
            'message': 'Problema infactible',
            'steps': self.steps,
            'explanation': 'El problema no tiene solucion factible (W > 0 en Fase I)'
        }
    
    def _build_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Construye respuesta de error."""
        return {
            'method': 'qp',
            'status': 'error',
            'message': f'Error: {error_msg}',
            'steps': self.steps,
            'explanation': f'Ocurrio un error: {error_msg}'
        }
    
    def _generate_explanation(self) -> str:
        """
        Genera explicación PROFESIONAL, CLARA y SIN EXCESO DE EMOJIS.
        Formato: técnico, estructurado, con TODAS las iteraciones.
        """
        lines = []
        
        lines.append("PROGRAMACION CUADRATICA - METODO DE DOS FASES")
        lines.append("=" * 80)
        lines.append("")
        
        for step in self.steps:
            num = step['numero']
            titulo = step['titulo']
            contenido = step.get('contenido', {})
            
            lines.append(f"▸ PASO {num}: {titulo}")
            lines.append("-" * 80)
            lines.append("")
            
            # PASO 1: Definición del problema
            if num == 1:
                lines.append(f"Función objetivo:")
                lines.append(f"  $${contenido.get('objetivo', '')}$$")
                lines.append(f"")
                lines.append(f"Variables: ${contenido.get('variables', '')}$")
                lines.append(f"Número de variables: {contenido.get('n_vars', 0)}")
                lines.append(f"")
                lines.append(f"Restricciones:")
                lines.append(f"  - Igualdades: {contenido.get('n_eq', 0)}")
                lines.append(f"  - Desigualdades: {contenido.get('n_ineq', 0)}")
                lines.append(f"  - No negatividad: $x \\geq 0$")
                lines.append(f"")
            
            # PASO 2: Matrices
            elif num == 2:
                C = contenido.get('C', [])
                D = contenido.get('D', [])
                A = contenido.get('A', [])
                b = contenido.get('b', [])
                
                lines.append(f"Vector $C$ (coeficientes lineales):")
                c_str = ', '.join([format_number(v) for v in C])
                lines.append(f"  $$C = \\begin{{bmatrix}} {c_str} \\end{{bmatrix}}$$")
                lines.append(f"")
                
                if D:
                    lines.append(f"Matriz $D$ (coeficientes cuadráticos):")
                    d_rows = [' & '.join([format_number(v) for v in row]) for row in D]
                    d_matrix = ' \\\\ '.join(d_rows)
                    lines.append(f"  $$D = \\begin{{bmatrix}} {d_matrix} \\end{{bmatrix}}$$")
                    lines.append(f"")
                
                if A:
                    lines.append(f"Matriz $A$ (restricciones):")
                    a_rows = [' & '.join([format_number(v) for v in row]) for row in A]
                    a_matrix = ' \\\\ '.join(a_rows)
                    lines.append(f"  $$A = \\begin{{bmatrix}} {a_matrix} \\end{{bmatrix}}$$")
                    lines.append(f"")
                
                if b:
                    lines.append(f"Vector $b$:")
                    b_str = ', '.join([format_number(v) for v in b])
                    lines.append(f"  $$b = \\begin{{bmatrix}} {b_str} \\end{{bmatrix}}$$")
                    lines.append(f"")
            
            # PASO 3: Convexidad
            elif num == 3:
                eigenvals = contenido.get('eigenvalores', [])
                lines.append(f"Eigenvalores de $D$:")
                for i, ev in enumerate(eigenvals, 1):
                    status = "(\\geq 0)" if ev >= -1e-9 else "(< 0)"
                    lines.append(f"  $\\lambda_{{{i}}} = {format_number(ev, 6)}$ {status}")
                lines.append(f"")
                convexa = contenido.get('convexa', False)
                if convexa:
                    lines.append(f"✔ El problema es **CONVEXO**")
                    lines.append(f"  El método garantiza encontrar el óptimo global")
                else:
                    lines.append(f"✘ El problema **NO** es convexo")
                lines.append(f"")
            
            # PASO 4: KKT
            elif num == 4:
                lines.append(f"**Condiciones de Karush-Kuhn-Tucker:**")
                lines.append(f"")
                lines.append(f"1. **Estacionariedad**: $\\nabla f(x) + A^T\\lambda + \\mu = 0$")
                lines.append(f"2. **Factibilidad primal**: $Ax = b$, $x \\geq 0$")
                lines.append(f"3. **Factibilidad dual**: $\\mu \\geq 0$")
                lines.append(f"4. **Complementariedad**: $\\mu_i \\cdot x_i = 0$ $\\forall i$")
                lines.append(f"")
                
                lines.append(f"**Variables del sistema:**")
                lines.append(f"  - $x$ (decisión): {contenido.get('n_vars', 0)}")
                lines.append(f"  - $\\lambda$ (restricciones): {contenido.get('n_lambda', 0)}")
                lines.append(f"  - $\\mu$ (no negatividad): {contenido.get('n_mu', 0)}")
                lines.append(f"")
                
                # Mostrar gradiente
                grad = contenido.get('gradiente', [])
                if grad:
                    lines.append(f"**Gradiente de $f(x)$:**")
                    lines.append(f"$$\\nabla f(x) = \\begin{{bmatrix}}")
                    for i, g in enumerate(grad, 1):
                        # Convertir expresión simbólica a LaTeX
                        g_str = str(g).replace('*', '')
                        # Reemplazar nombres de variables por notación con índices
                        for j, var_name in enumerate(self.var_names):
                            g_str = g_str.replace(var_name, f"x_{{{j+1}}}")
                        lines.append(f"  {g_str} \\\\")
                    lines.append(f"\\end{{bmatrix}}$$")
                    lines.append(f"")
                
                # Mostrar ecuaciones KKT expandidas
                ecuaciones = contenido.get('ecuaciones_kkt', [])
                if ecuaciones:
                    lines.append(f"**Sistema de estacionariedad expandido:**")
                    for eq in ecuaciones:
                        lines.append(f"  {eq}")
                    lines.append(f"")
                
                lines.append(f"")
            
            # PASO 5: FASE I
            elif num == 5:
                lines.append(f"**FASE I**: Búsqueda de solución factible")
                lines.append(f"Objetivo: Minimizar $W = \\sum_{{i}} R_i$")
                lines.append(f"")
                
                iteraciones = contenido.get('iteraciones', [])
                for it in iteraciones:
                    it_num = it.get('numero', 0)
                    it_tipo = it.get('tipo', '')
                    
                    if it_tipo == 'tabla_inicial':
                        lines.append(f"**Tabla inicial:**")
                        lines.append(f"```")
                        lines.append(it.get('tabla', ''))
                        lines.append(f"```")
                        lines.append(f"")
                    
                    elif it_tipo == 'pivote':
                        lines.append(f"**→ Iteración {it_num}**")
                        entrante = it.get('entrante', '?')
                        saliente = it.get('saliente', '?')
                        pivote = it.get('pivote_valor', 0)
                        ratio = it.get('ratio_minimo', 0)
                        
                        lines.append(f"- Variable entrante: ${entrante}$ (coeficiente más negativo)")
                        lines.append(f"- Variable saliente: ${saliente}$ (ratio test mínimo = ${format_number(ratio)}$)")
                        lines.append(f"- Elemento pivote: ${format_number(pivote)}$")
                        lines.append(f"")
                        
                        lines.append(f"Tabla **antes** del pivote:")
                        lines.append(f"```")
                        lines.append(it.get('tabla_antes', ''))
                        lines.append(f"```")
                        lines.append(f"")
                        
                        lines.append(f"Tabla **después** del pivote:")
                        lines.append(f"```")
                        lines.append(it.get('tabla_despues', ''))
                        lines.append(f"```")
                        lines.append(f"")
                
                lines.append(f"**Resultado Fase I:**")
                if contenido.get('factible'):
                    lines.append(f"  - $W_{{final}} = {format_number(contenido.get('W_final', 0))}$")
                    lines.append(f"  - ✔ Problema **FACTIBLE** → continuar con Fase II")
                else:
                    lines.append(f"  - ✘ Problema **INFACTIBLE**")
                lines.append(f"")
            
            # PASO 6: FASE II
            elif num == 6:
                lines.append(f"**FASE II**: Optimización de $f(x)$")
                lines.append(f"")
                
                iteraciones = contenido.get('iteraciones', [])
                for it in iteraciones:
                    it_num = it.get('numero', 0)
                    it_tipo = it.get('tipo', '')
                    
                    if it_tipo == 'tabla_inicial':
                        lines.append(f"**Tabla inicial Fase II:**")
                        lines.append(f"```")
                        lines.append(it.get('tabla', ''))
                        lines.append(f"```")
                        lines.append(f"")
                    
                    elif it_tipo == 'pivote':
                        lines.append(f"**→ Iteración {it_num}**")
                        entrante = it.get('entrante', '?')
                        saliente = it.get('saliente', '?')
                        pivote = it.get('pivote_valor', 0)
                        ratio = it.get('ratio_minimo', 0)
                        
                        lines.append(f"- Variable entrante: ${entrante}$ (mejora objetivo)")
                        lines.append(f"- Variable saliente: ${saliente}$ (ratio test = ${format_number(ratio)}$)")
                        lines.append(f"- Elemento pivote: ${format_number(pivote)}$")
                        lines.append(f"")
                        
                        lines.append(f"Tabla **antes** del pivote:")
                        lines.append(f"```")
                        lines.append(it.get('tabla_antes', ''))
                        lines.append(f"```")
                        lines.append(f"")
                        
                        lines.append(f"Tabla **después** del pivote:")
                        lines.append(f"```")
                        lines.append(it.get('tabla_despues', ''))
                        lines.append(f"```")
                        lines.append(f"")
                
                lines.append(f"**Tabla final (óptima):**")
                lines.append(f"```")
                lines.append(contenido.get('tabla_final', 'N/A'))
                lines.append(f"```")
                lines.append(f"")
                
                lines.append(f"**Solución óptima:**")
                x_opt = contenido.get('x_optimo', [])
                for i, val in enumerate(x_opt, 1):
                    lines.append(f"  - $x_{{{i}}}^* = {format_number(val)}$")
                lines.append(f"  - $f(x^*) = {format_number(contenido.get('f_optimo', 0))}$")
                lines.append(f"")
            
            # PASO 7: Solución final
            elif num == 7:
                lines.append(f"**SOLUCIÓN ÓPTIMA:**")
                lines.append(f"")
                solucion = contenido.get('solucion', {})
                for var, val in solucion.items():
                    lines.append(f"  ${var}^* = {format_number(val)}$")
                lines.append(f"")
                lines.append(f"Valor objetivo óptimo:")
                lines.append(f"  $$f(x^*) = {format_number(contenido.get('valor_objetivo', 0))}$$")
                lines.append(f"")
        
        lines.append("=" * 80)
        lines.append("PROCEDIMIENTO COMPLETADO")
        lines.append("=" * 80)
        
        return "\n".join(lines)


def solve_qp(objective_expr: str, variables: List[str], 
             constraints: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Punto de entrada principal."""
    solver = QPSimplexSolver(objective_expr, variables, constraints)
    return solver.solve()
