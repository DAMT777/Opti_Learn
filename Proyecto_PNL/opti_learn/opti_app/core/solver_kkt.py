"""
Solver KKT - Condiciones de Karush-Kuhn-Tucker
Resuelve problemas de optimización con restricciones mediante análisis sistemático de casos.
Sigue el procedimiento pedagógico de 9 pasos.
"""

from __future__ import annotations
import numpy as np
import sympy as sp
from typing import Dict, Any, List, Tuple, Optional
from itertools import product
from fractions import Fraction


def _convert_to_native(obj):
    """Convierte tipos NumPy y SymPy a tipos nativos de Python."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, (sp.Basic, sp.Expr)):
        try:
            return float(obj)
        except:
            return str(obj)
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


class KKTSolver:
    """
    Solver usando Condiciones KKT (Karush-Kuhn-Tucker).
    Resuelve: min/max f(x)
    Sujeto a: g_i(x) <= 0, h_j(x) = 0
    """
    
    def __init__(self, objective_expr: str, variables: List[str], constraints: List[Dict[str, Any]], 
                 is_maximization: bool = False):
        self.objective_expr = objective_expr
        self.var_names = variables
        self.constraints = constraints or []
        self.is_maximization = is_maximization
        
        # Variables simbólicas
        self.sym_vars = {name: sp.Symbol(name, real=True) for name in variables}
        self.n_vars = len(variables)
        
        # Función objetivo simbólica
        self.f_expr = sp.sympify(objective_expr, locals=self.sym_vars)
        
        # Si es maximización, convertir a minimización
        if self.is_maximization:
            self.f_expr = -self.f_expr
        
        # Separar restricciones
        self.g_constraints = []  # Desigualdades g_i(x) <= 0
        self.h_constraints = []  # Igualdades h_j(x) = 0
        
        for c in self.constraints:
            expr_str = c.get('expression', '')
            rhs = c.get('rhs', 0)
            kind = c.get('kind', 'ineq')
            
            # Crear expresión simbólica
            expr_symb = sp.sympify(expr_str, locals=self.sym_vars) - rhs
            
            if kind == 'eq':
                self.h_constraints.append(expr_symb)
            elif kind in ['ineq', 'le']:
                # Convertir a forma g(x) <= 0
                self.g_constraints.append(expr_symb)
            elif kind == 'ge':
                # g(x) >= 0 -> -g(x) <= 0
                self.g_constraints.append(-expr_symb)
        
        self.n_ineq = len(self.g_constraints)
        self.n_eq = len(self.h_constraints)
        
        # Multiplicadores de Lagrange
        self.lambdas = [sp.Symbol(f'lambda_{i}', real=True, nonnegative=True) for i in range(self.n_ineq)]
        self.mus = [sp.Symbol(f'mu_{j}', real=True) for j in range(self.n_eq)]
        
        # Lagrangiana
        self.L = None
        
        # Gradientes
        self.grad_f = None
        self.grad_L = None
        
        # Casos a evaluar
        self.cases = []
        
        # Soluciones candidatas
        self.candidates = []
        
        # Mejor solución
        self.solution = None
        self.optimal_value = None
        
    def solve(self) -> Dict[str, Any]:
        """Ejecuta el procedimiento KKT completo de 9 pasos."""
        try:
            self._step1_present_problem()
            self._step2_build_lagrangian()
            self._step3_compute_gradients()
            self._step4_state_kkt_conditions()
            self._step5_generate_cases()
            self._step6_solve_cases()
            self._step7_evaluate_candidates()
            self._step8_show_solution()
            self._step9_interpretation()
            
            explanation = self._generate_explanation()
            
            return {
                'status': 'success',
                'method': 'kkt',
                'solution': _convert_to_native(self.solution),
                'optimal_value': _convert_to_native(self.optimal_value),
                'explanation': explanation,
                'is_maximization': self.is_maximization,
                'candidates': _convert_to_native(self.candidates),
            }
            
        except Exception as e:
            import traceback
            return {
                'status': 'error',
                'method': 'kkt',
                'message': f"Error en solver KKT: {str(e)}",
                'traceback': traceback.format_exc()
            }
    
    def _step1_present_problem(self):
        """🟦 PASO 1 — Presentación del Problema."""
        pass
    
    def _step2_build_lagrangian(self):
        """🟩 PASO 2 — Construcción de la Función Lagrangiana."""
        # L(x, λ, μ) = f(x) + Σλᵢ·gᵢ(x) + Σμⱼ·hⱼ(x)
        self.L = self.f_expr.copy()
        
        for i, g_i in enumerate(self.g_constraints):
            self.L += self.lambdas[i] * g_i
        
        for j, h_j in enumerate(self.h_constraints):
            self.L += self.mus[j] * h_j
    
    def _step3_compute_gradients(self):
        """🟧 PASO 3 — Derivar (Gradiente de la Lagrangiana)."""
        var_list = [self.sym_vars[name] for name in self.var_names]
        
        # Gradiente de f
        self.grad_f = [sp.diff(self.f_expr, v) for v in var_list]
        
        # Gradiente de L
        self.grad_L = [sp.diff(self.L, v) for v in var_list]
        
        # Calcular Hessiana de f (para análisis de convexidad)
        self._compute_hessian()
    
    def _compute_hessian(self):
        """Calcula la matriz Hessiana de la función objetivo."""
        var_list = [self.sym_vars[name] for name in self.var_names]
        n = len(var_list)
        
        # Matriz Hessiana H[i,j] = ∂²f/∂xᵢ∂xⱼ
        self.hessian = sp.Matrix([[sp.diff(self.f_expr, var_i, var_j) 
                                   for var_j in var_list] 
                                  for var_i in var_list])
        
        # Analizar definitud
        try:
            eigenvals = self.hessian.eigenvals()
            self.hessian_eigenvals = list(eigenvals.keys())
            
            # Clasificar
            all_positive = all(ev > 0 for ev in self.hessian_eigenvals if ev.is_real)
            all_negative = all(ev < 0 for ev in self.hessian_eigenvals if ev.is_real)
            all_non_negative = all(ev >= 0 for ev in self.hessian_eigenvals if ev.is_real)
            all_non_positive = all(ev <= 0 for ev in self.hessian_eigenvals if ev.is_real)
            
            if all_positive:
                self.hessian_type = "definida positiva"
                self.convexity = "convexa estricta"
            elif all_negative:
                self.hessian_type = "definida negativa"
                self.convexity = "cóncava estricta"
            elif all_non_negative:
                self.hessian_type = "semidefinida positiva"
                self.convexity = "convexa"
            elif all_non_positive:
                self.hessian_type = "semidefinida negativa"
                self.convexity = "cóncava"
            else:
                self.hessian_type = "indefinida"
                self.convexity = "no convexa"
                
        except:
            self.hessian_type = "no determinada"
            self.convexity = "no analizada"
            self.hessian_eigenvals = []
    
    def _step4_state_kkt_conditions(self):
        """🟥 PASO 4 — Imponer Condiciones KKT."""
        # Las 4 condiciones KKT:
        # 1. Estacionariedad: ∇L = 0
        # 2. Factibilidad primal: g_i(x) <= 0, h_j(x) = 0
        # 3. Factibilidad dual: λ_i >= 0
        # 4. Complementariedad: λ_i * g_i(x) = 0
        pass
    
    def _step5_generate_cases(self):
        """🟪 PASO 5 — Clasificación de Casos (Prueba de activación)."""
        # Para cada restricción de desigualdad, generar dos casos:
        # Caso A: λᵢ = 0 (restricción NO activa)
        # Caso B: gᵢ(x) = 0 (restricción ACTIVA)
        
        n = self.n_ineq
        if n == 0:
            # Sin restricciones de desigualdad, un solo caso
            self.cases = [{}]
            return
        
        # Generar todas las combinaciones posibles (2^n casos)
        # 0 = restricción no activa (λ=0)
        # 1 = restricción activa (g=0)
        
        for config in product([0, 1], repeat=n):
            case = {
                'config': config,
                'active_constraints': [i for i, val in enumerate(config) if val == 1],
                'inactive_constraints': [i for i, val in enumerate(config) if val == 0]
            }
            self.cases.append(case)
    
    def _step6_solve_cases(self):
        """🟫 PASO 6 — Resolver el sistema (por casos)."""
        var_list = [self.sym_vars[name] for name in self.var_names]
        
        for case_idx, case in enumerate(self.cases):
            try:
                # Sistema de ecuaciones
                equations = []
                
                # 1. Estacionariedad: ∇L = 0
                equations.extend(self.grad_L)
                
                # 2. Restricciones de igualdad: h_j(x) = 0
                equations.extend(self.h_constraints)
                
                # 3. Restricciones activas: g_i(x) = 0
                active = case.get('active_constraints', [])
                for i in active:
                    equations.append(self.g_constraints[i])
                
                # 4. Restricciones inactivas: λ_i = 0
                inactive = case.get('inactive_constraints', [])
                for i in inactive:
                    equations.append(self.lambdas[i])
                
                # Variables a resolver
                unknowns = var_list + self.lambdas + self.mus
                
                # Resolver sistema
                solutions = sp.solve(equations, unknowns, dict=True)
                
                if not solutions:
                    case['status'] = 'no_solution'
                    continue
                
                # Procesar cada solución
                for sol in solutions:
                    candidate = {
                        'case_index': case_idx,
                        'case_config': case.get('config', ()),
                        'variables': {},
                        'lambdas': {},
                        'mus': {},
                        'active_constraints': active.copy(),
                        'status': 'pending_verification'
                    }
                    
                    # Extraer valores de variables
                    for name in self.var_names:
                        var = self.sym_vars[name]
                        candidate['variables'][name] = float(sol.get(var, 0))
                    
                    # Extraer lambdas
                    for i, lam in enumerate(self.lambdas):
                        candidate['lambdas'][i] = float(sol.get(lam, 0))
                    
                    # Extraer mus
                    for j, mu in enumerate(self.mus):
                        candidate['mus'][j] = float(sol.get(mu, 0))
                    
                    # Verificar KKT
                    is_valid = self._verify_kkt_candidate(candidate)
                    candidate['kkt_valid'] = is_valid
                    
                    if is_valid:
                        # Calcular valor objetivo
                        x_vals = {self.sym_vars[name]: candidate['variables'][name] for name in self.var_names}
                        f_val = float(self.f_expr.subs(x_vals))
                        
                        # Si era maximización, devolver signo original
                        if self.is_maximization:
                            f_val = -f_val
                        
                        candidate['objective_value'] = f_val
                        candidate['status'] = 'valid'
                        
                        self.candidates.append(candidate)
                
            except Exception as e:
                case['status'] = 'error'
                case['error'] = str(e)
    
    def _verify_kkt_candidate(self, candidate: Dict) -> bool:
        """Verifica las 4 condiciones KKT para un candidato."""
        x_vals = {self.sym_vars[name]: candidate['variables'][name] for name in self.var_names}
        
        # 1. Factibilidad primal - Desigualdades: g_i(x) <= 0
        for i, g_i in enumerate(self.g_constraints):
            g_val = float(g_i.subs(x_vals))
            if g_val > 1e-6:  # Tolerancia numérica
                return False
        
        # 2. Factibilidad primal - Igualdades: h_j(x) = 0
        for j, h_j in enumerate(self.h_constraints):
            h_val = float(h_j.subs(x_vals))
            if abs(h_val) > 1e-6:
                return False
        
        # 3. Factibilidad dual: λ_i >= 0
        for i, lam_val in candidate['lambdas'].items():
            if lam_val < -1e-6:
                return False
        
        # 4. Complementariedad: λ_i * g_i(x) = 0
        for i, g_i in enumerate(self.g_constraints):
            lam_val = candidate['lambdas'].get(i, 0)
            g_val = float(g_i.subs(x_vals))
            if abs(lam_val * g_val) > 1e-6:
                return False
        
        return True
    
    def _step7_evaluate_candidates(self):
        """🟨 PASO 7 — Evaluación y selección del punto óptimo."""
        if not self.candidates:
            raise ValueError("No se encontraron candidatos válidos que cumplan KKT")
        
        # Ordenar por valor objetivo (minimización)
        self.candidates.sort(key=lambda c: c['objective_value'])
        
        # Mejor candidato
        best = self.candidates[0]
        
        self.solution = best['variables'].copy()
        self.optimal_value = best['objective_value']
        self.best_candidate = best
    
    def _step8_show_solution(self):
        """🟦 PASO 8 — Mostrar la solución final."""
        pass
    
    def _step9_interpretation(self):
        """🟣 PASO 9 — Interpretación final (Resumen pedagógico)."""
        pass
    
    def _generate_explanation(self) -> str:
        """Genera la explicación completa en formato Markdown con LaTeX."""
        lines = []
        
        # Encabezado principal
        lines.append("# 🎯 CONDICIONES KKT — MÉTODO ANALÍTICO")
        lines.append("")
        
        # PASO 1
        lines.append("## PASO 1: PRESENTACIÓN DEL PROBLEMA")
        lines.append("")
        lines.append("**Resolvamos este problema paso a paso usando condiciones KKT:**")
        lines.append("")
        
        obj_type = "Maximizar" if self.is_maximization else "Minimizar"
        lines.append(f"**Función objetivo ({obj_type}):**")
        lines.append("")
        lines.append(f"$$f(x) = {sp.latex(self.f_expr if not self.is_maximization else -self.f_expr)}$$")
        lines.append("")
        
        lines.append(f"**Variables de decisión:** ${', '.join(self.var_names)}$")
        lines.append("")
        
        if self.g_constraints or self.h_constraints:
            lines.append("**Restricciones:**")
            lines.append("")
            
            for i, g_i in enumerate(self.g_constraints):
                lines.append(f"  - Desigualdad {i+1}: ${sp.latex(g_i)} \\leq 0$")
            
            for j, h_j in enumerate(self.h_constraints):
                lines.append(f"  - Igualdad {j+1}: ${sp.latex(h_j)} = 0$")
            
            lines.append("")
        
        # PASO 2
        lines.append("---")
        lines.append("")
        lines.append("## PASO 2: CONSTRUCCIÓN DE LA LAGRANGIANA")
        lines.append("")
        lines.append("**Combinamos la función objetivo con las restricciones:**")
        lines.append("")
        lines.append("$$\\mathcal{L}(x, \\lambda, \\mu) = f(x) + \\sum_{i} \\lambda_i g_i(x) + \\sum_{j} \\mu_j h_j(x)$$")
        lines.append("")
        lines.append("**Lagrangiana completa:**")
        lines.append("")
        lines.append(f"$$\\mathcal{{L}} = {sp.latex(self.L)}$$")
        lines.append("")
        
        if self.lambdas:
            lambda_str = ', '.join([f"$\\lambda_{{{i}}}$" for i in range(len(self.lambdas))])
            lines.append(f"Multiplicadores de desigualdad: {lambda_str}")
            lines.append("")
        
        if self.mus:
            mu_str = ', '.join([f"$\\mu_{{{j}}}$" for j in range(len(self.mus))])
            lines.append(f"Multiplicadores de igualdad: {mu_str}")
            lines.append("")
        
        # PASO 3
        lines.append("---")
        lines.append("")
        lines.append("## PASO 3: GRADIENTE DE LA LAGRANGIANA")
        lines.append("")
        lines.append("**Calculamos las derivadas parciales (condiciones de primer orden):**")
        lines.append("")
        
        for i, name in enumerate(self.var_names):
            lines.append(f"$$\\frac{{\\partial \\mathcal{{L}}}}{{\\partial {name}}} = {sp.latex(self.grad_L[i])} = 0$$")
            lines.append("")
        
        # PASO 4
        lines.append("---")
        lines.append("")
        lines.append("## PASO 4: CONDICIONES KKT")
        lines.append("")
        lines.append("**Las cuatro condiciones que debe cumplir toda solución óptima:**")
        lines.append("")
        
        lines.append("### (1) Estacionariedad")
        lines.append("")
        lines.append("El gradiente de la Lagrangiana debe ser cero:")
        lines.append("")
        lines.append("$$\\nabla \\mathcal{L} = 0$$")
        lines.append("")
        lines.append("*Es el punto donde objetivo y restricciones se compensan exactamente.*")
        lines.append("")
        
        lines.append("### (2) Factibilidad Primal")
        lines.append("")
        lines.append("El punto debe respetar las restricciones originales:")
        lines.append("")
        if self.g_constraints:
            lines.append("$$g_i(x) \\leq 0 \\quad \\forall i$$")
            lines.append("")
        if self.h_constraints:
            lines.append("$$h_j(x) = 0 \\quad \\forall j$$")
            lines.append("")
        lines.append("*La solución debe estar en la región factible.*")
        lines.append("")
        
        lines.append("### (3) Factibilidad Dual")
        lines.append("")
        lines.append("Los multiplicadores de desigualdades deben ser no negativos:")
        lines.append("")
        lines.append("$$\\lambda_i \\geq 0 \\quad \\forall i$$")
        lines.append("")
        lines.append("*Representan fuerzas de presión; no pueden ser negativas.*")
        lines.append("")
        
        lines.append("### (4) Complementariedad")
        lines.append("")
        lines.append("Solo actúan las restricciones que tocan el límite:")
        lines.append("")
        lines.append("$$\\lambda_i \\cdot g_i(x) = 0 \\quad \\forall i$$")
        lines.append("")
        lines.append("*Si una restricción no está activa ($g_i(x) < 0$), su multiplicador debe ser cero ($\\lambda_i = 0$).*")
        lines.append("")
        
        # PASO 5
        lines.append("---")
        lines.append("")
        lines.append("## PASO 5: CLASIFICACIÓN DE CASOS")
        lines.append("")
        lines.append(f"**Probamos {len(self.cases)} configuraciones posibles de restricciones activas/inactivas:**")
        lines.append("")
        lines.append("Para cada restricción de desigualdad $g_i(x) \\leq 0$, exploramos dos escenarios:")
        lines.append("")
        lines.append("- **Restricción NO activa**: $\\lambda_i = 0$ (no presiona la solución)")
        lines.append("- **Restricción ACTIVA**: $g_i(x) = 0$ (toca el límite)")
        lines.append("")
        
        # Mostrar detalle de algunos casos importantes
        cases_to_show = min(6, len(self.cases))
        for idx in range(cases_to_show):
            case = self.cases[idx]
            active = case.get('active_constraints', [])
            inactive = case.get('inactive_constraints', [])
            
            lines.append(f"**Caso {idx+1}:**")
            if not active and inactive:
                lines.append("  - Todas las restricciones inactivas ($\\lambda_i = 0$ para todo $i$)")
                lines.append("  - Buscamos solución en el interior de la región factible")
            elif active and not inactive:
                lines.append(f"  - Todas las restricciones activas ($g_i(x) = 0$ para todo $i$)")
                lines.append("  - Buscamos solución en la frontera (todas tocando límites)")
            else:
                if active:
                    lines.append(f"  - Activas: restricciones {', '.join([str(i+1) for i in active])} → $g_i(x) = 0$")
                if inactive:
                    lines.append(f"  - Inactivas: restricciones {', '.join([str(i+1) for i in inactive])} → $\\lambda_i = 0$")
            lines.append("")
        
        if len(self.cases) > cases_to_show:
            lines.append(f"*(Y {len(self.cases) - cases_to_show} casos adicionales...)*")
            lines.append("")
        
        # PASO 6
        lines.append("---")
        lines.append("")
        lines.append("## PASO 6: RESOLUCIÓN POR CASOS")
        lines.append("")
        lines.append("**Para cada caso, resolvemos el sistema de ecuaciones:**")
        lines.append("")
        lines.append("1. Ecuaciones de estacionariedad: $\\nabla \\mathcal{L} = 0$")
        lines.append("2. Restricciones de igualdad: $h_j(x) = 0$")
        lines.append("3. Restricciones activas: $g_i(x) = 0$ (para las marcadas como activas)")
        lines.append("4. Multiplicadores inactivos: $\\lambda_i = 0$ (para las marcadas como inactivas)")
        lines.append("")
        
        # Mostrar ejemplo de resolución de un caso si hay candidatos
        if self.candidates:
            lines.append("**Ejemplo de resolución (primer caso válido):**")
            lines.append("")
            first_valid = self.candidates[0]
            case_idx = first_valid.get('case_index', 0)
            active = first_valid.get('active_constraints', [])
            
            if not active:
                lines.append("- Caso interior (sin restricciones activas):")
                lines.append("  - Resolver: $\\nabla f(x) = 0$")
            else:
                lines.append(f"- Caso con restricciones activas {active}:")
                lines.append("  - Resolver sistema combinado de estacionariedad y restricciones activas")
            
            lines.append("  - Solución candidata: $" + ", ".join([f"{name}={format_number(val)}" for name, val in first_valid['variables'].items()]) + "$")
            lines.append("  - Verificar condiciones KKT... ✓")
            lines.append("")
        
        valid_count = len([c for c in self.candidates if c.get('kkt_valid', False)])
        invalid_count = len(self.cases) - valid_count
        lines.append(f"**Resultado del análisis:**")
        lines.append("")
        lines.append(f"- Casos válidos (cumplen las 4 condiciones KKT): **{valid_count}**")
        lines.append(f"- Casos descartados (violan alguna condición): {invalid_count}")
        lines.append("")
        
        # PASO 7
        lines.append("---")
        lines.append("")
        lines.append("## PASO 7: EVALUACIÓN DE CANDIDATOS")
        lines.append("")
        lines.append("**Comparamos todos los candidatos válidos y seleccionamos el óptimo:**")
        lines.append("")
        
        if self.candidates:
            lines.append("| Candidato | Variables | Valor Objetivo | Estado |")
            lines.append("|-----------|-----------|----------------|--------|")
            
            for idx, cand in enumerate(self.candidates[:5]):
                vars_str = ', '.join([f"{name}={format_number(val)}" for name, val in cand['variables'].items()])
                f_val = format_number(cand['objective_value'])
                status = "✅ ÓPTIMO" if idx == 0 else "✓ Válido"
                lines.append(f"| {idx+1} | {vars_str} | {f_val} | {status} |")
            
            lines.append("")
        
        # PASO 8
        lines.append("---")
        lines.append("")
        lines.append("## PASO 8: SOLUCIÓN FINAL")
        lines.append("")
        lines.append("**Solución óptima que cumple todas las condiciones KKT:**")
        lines.append("")
        
        if self.solution:
            lines.append("### Variables óptimas")
            lines.append("")
            for name, val in self.solution.items():
                lines.append(f"- ${name}^* = {format_number(val)}$")
            lines.append("")
            
            lines.append("### Valor óptimo")
            lines.append("")
            obj_word = "Máximo" if self.is_maximization else "Mínimo"
            lines.append(f"$$f(x^*) = {format_number(self.optimal_value)}$$")
            lines.append("")
            lines.append(f"*{obj_word} alcanzado.*")
            lines.append("")
            
            # Restricciones activas
            best = self.best_candidate
            active_idx = best.get('active_constraints', [])
            if active_idx:
                lines.append("### Restricciones activas")
                lines.append("")
                for i in active_idx:
                    lines.append(f"- Restricción {i+1}: ${sp.latex(self.g_constraints[i])} = 0$")
                    lam_val = best['lambdas'].get(i, 0)
                    lines.append(f"  - $\\lambda_{{{i}}} = {format_number(lam_val)}$")
                lines.append("")
            
            # Multiplicadores
            if best['lambdas'] or best['mus']:
                lines.append("### Multiplicadores de Lagrange")
                lines.append("")
                for i, lam_val in best['lambdas'].items():
                    status = "activa" if i in active_idx else "inactiva"
                    lines.append(f"- $\\lambda_{{{i}}} = {format_number(lam_val)}$ ({status})")
                
                for j, mu_val in best['mus'].items():
                    lines.append(f"- $\\mu_{{{j}}} = {format_number(mu_val)}$")
                lines.append("")
            
            # Análisis de convexidad (Hessiana)
            self._add_hessian_analysis(lines)
        
        # PASO 9
        lines.append("---")
        lines.append("")
        lines.append("## PASO 9: INTERPRETACIÓN PEDAGÓGICA")
        lines.append("")
        
        conclusion = self._generate_conclusion()
        lines.append(conclusion)
        
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("### ✓ Procedimiento KKT completado exitosamente")
        lines.append("")
        
        return '\n'.join(lines)
    
    def _add_hessian_analysis(self, lines: List[str]):
        """Agrega análisis de la Hessiana para verificar convexidad."""
        if not hasattr(self, 'hessian') or self.hessian is None:
            return
        
        lines.append("### 📐 Análisis de Convexidad (Hessiana)")
        lines.append("")
        lines.append("Para garantizar que el punto hallado es óptimo, analizamos la matriz Hessiana:")
        lines.append("")
        
        # Mostrar matriz Hessiana
        lines.append("**Matriz Hessiana** $H = \\nabla^2 f(x)$:")
        lines.append("")
        
        # Convertir a LaTeX
        try:
            hessian_latex = sp.latex(self.hessian)
            lines.append(f"$$H = {hessian_latex}$$")
            lines.append("")
        except:
            lines.append("*(Matriz Hessiana calculada simbólicamente)*")
            lines.append("")
        
        # Tipo de Hessiana
        if hasattr(self, 'hessian_type'):
            lines.append(f"**Clasificación:** La Hessiana es *{self.hessian_type}*.")
            lines.append("")
        
        # Valores propios si están disponibles
        if hasattr(self, 'hessian_eigenvals') and self.hessian_eigenvals:
            try:
                eigenvals_str = ', '.join([f"{format_number(float(ev))}" if ev.is_real else str(ev) 
                                           for ev in self.hessian_eigenvals])
                lines.append(f"**Valores propios:** $\\lambda = [{eigenvals_str}]$")
                lines.append("")
            except:
                pass
        
        # Interpretación
        if hasattr(self, 'convexity'):
            lines.append(f"**Interpretación:** La función objetivo es *{self.convexity}*.")
            lines.append("")
            
            if self.convexity == "convexa estricta":
                opt_type = "mínimo global" if not self.is_maximization else "máximo global"
                lines.append(f"✓ Como la función es estrictamente convexa y se cumplen las condiciones KKT, ")
                lines.append(f"el punto hallado es un **{opt_type} único**.")
            elif self.convexity == "convexa":
                opt_type = "mínimo global" if not self.is_maximization else "máximo global"
                lines.append(f"✓ Como la función es convexa y se cumplen las condiciones KKT, ")
                lines.append(f"el punto hallado es un **{opt_type}** (puede no ser único).")
            elif self.convexity == "cóncava estricta":
                opt_type = "máximo global" if self.is_maximization else "mínimo global"
                lines.append(f"✓ La función es cóncava. El punto hallado es un **{opt_type}**.")
            else:
                lines.append("⚠️ La función no es convexa. El punto hallado cumple KKT pero podría ser un óptimo local.")
            
            lines.append("")
    
    def _generate_conclusion(self) -> str:
        """Genera conclusión interpretativa según el contexto del problema."""
        lines = []
        
        lines.append("🌟 **Conclusión:**")
        lines.append("")
        lines.append("Encontramos el punto donde la función objetivo y las restricciones conviven en **perfecto equilibrio**.")
        lines.append("")
        
        if self.best_candidate:
            active_idx = self.best_candidate.get('active_constraints', [])
            
            if active_idx:
                lines.append(f"Las restricciones **activas** (que tocan el límite) son: {', '.join([str(i+1) for i in active_idx])}")
                lines.append("")
                lines.append("Estas restricciones están **presionando** la solución óptima. Sus multiplicadores λ indican:")
                lines.append("")
                for i in active_idx:
                    lam_val = self.best_candidate['lambdas'].get(i, 0)
                    lines.append(f"- $\\lambda_{{{i}}} = {format_number(lam_val)}$: Sensibilidad del objetivo ante cambios en esta restricción")
                lines.append("")
            else:
                lines.append("✨ No hay restricciones activas: la solución está en el **interior** de la región factible.")
                lines.append("")
            
            lines.append("**¿Por qué es válida la solución?**")
            lines.append("")
            lines.append("Cumple las **4 condiciones KKT**:")
            lines.append("1. ✅ Gradiente en equilibrio (estacionariedad)")
            lines.append("2. ✅ Respeta todas las restricciones (factibilidad primal)")
            lines.append("3. ✅ Multiplicadores no negativos (factibilidad dual)")
            lines.append("4. ✅ Complementariedad perfecta (solo actúan las restricciones presionadas)")
            lines.append("")
        
        return '\n'.join(lines)


# Alias de compatibilidad
def resolver_kkt(objective_expr: str, variables: List[str], constraints: List[Dict[str, Any]], 
                 is_maximization: bool = False) -> Dict[str, Any]:
    """Interfaz compatible para el solver KKT."""
    solver = KKTSolver(objective_expr, variables, constraints, is_maximization)
    return solver.solve()


def solve(objective_expr: str, variables: List[str], constraints: List[Dict[str, Any]], 
          is_maximization: bool = False) -> Dict[str, Any]:
    """Alias principal del solver."""
    return resolver_kkt(objective_expr, variables, constraints, is_maximization)
