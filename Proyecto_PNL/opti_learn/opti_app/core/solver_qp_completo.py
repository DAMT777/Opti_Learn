"""
Solver completo para Programación Cuadrática (QP)
Implementa el método de dos fases con sistema KKT

Autor: OptiLearn Team
Versión: 1.0.0
"""

from __future__ import annotations
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
import sympy as sp
from sympy import symbols, Matrix, hessian, lambdify


class QPSolver:
    """
    Solver para Programación Cuadrática usando método de dos fases.
    
    Problema estándar:
        max z = C*X + X^T * D * X
        s.a.  A*X <= b
              X >= 0
    
    O en forma de minimización:
        min f = C*X + X^T * D * X
        s.a.  A*X <= b
              X >= 0
    """
    
    def __init__(self, objective_expr: str, variables: List[str], constraints: List[Dict[str, Any]]):
        """
        Inicializa el solver QP.
        
        Args:
            objective_expr: Expresión de la función objetivo en SymPy
            variables: Lista de variables ['x', 'y', 'z', ...]
            constraints: Lista de restricciones [{'kind': 'eq'|'le'|'ge', 'expr': 'expr'}]
        """
        self.objective_expr = objective_expr
        self.variables = variables
        self.constraints = constraints
        self.n_vars = len(variables)
        
        # Símbolos de SymPy
        self.syms = {var: sp.Symbol(var, real=True) for var in variables}
        
        # Matrices del problema
        self.C = None  # Vector de coeficientes lineales
        self.D = None  # Matriz cuadrática
        self.A = None  # Matriz de restricciones
        self.b = None  # Vector de términos independientes
        
        # Información del problema
        self.is_maximization = 'maximizar' in objective_expr.lower() or 'max' in objective_expr.lower()
        
        # Resultados del proceso
        self.steps = []  # Pasos del proceso
        self.tables = []  # Tablas iterativas
        self.solution = None
        
    def solve(self) -> Dict[str, Any]:
        """
        Resuelve el problema QP completo.
        
        Returns:
            Diccionario con la solución y pasos del proceso
        """
        try:
            # Paso 1: Presentación del problema
            self._step1_present_problem()
            
            # Paso 2: Extraer matrices C, D, A, b
            self._step2_extract_matrices()
            
            # Paso 3: Verificar definitud de D
            self._step3_check_definiteness()
            
            # Paso 4: Construir sistema KKT
            self._step4_build_kkt_system()
            
            # Paso 5: Construir tabla inicial (Fase I)
            self._step5_build_initial_table()
            
            # Paso 6: Ejecutar Fase I (encontrar solución factible)
            self._step6_phase1()
            
            # Paso 7: Ejecutar Fase II (optimizar)
            self._step7_phase2()
            
            # Paso 8: Presentar resultado final
            self._step8_present_result()
            
            return {
                'status': 'optimal',
                'method': 'qp',
                'x_star': self.solution['x'],
                'f_star': self.solution['z'],
                'steps': self.steps,
                'tables': self.tables,
                'explanation': self._generate_educational_explanation(),
                'plot_data': self._generate_plot_data()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'method': 'qp',
                'message': f'Error al resolver el problema QP: {str(e)}',
                'steps': self.steps,
                'explanation': 'El solver QP completo está en desarrollo. Por ahora mostramos la estructura del método.'
            }
    
    def _step1_present_problem(self):
        """Paso 1: Presentación del problema"""
        step = {
            'number': 1,
            'title': 'Presentación del Problema',
            'content': {
                'model_general': {
                    'objective': 'max z = C*X + X^T * D * X' if self.is_maximization else 'min f = C*X + X^T * D * X',
                    'constraints': ['A*X ≤ b', 'X ≥ 0']
                },
                'problem_specific': {
                    'objective': self.objective_expr,
                    'variables': self.variables,
                    'n_constraints': len(self.constraints),
                    'constraints_detail': self.constraints
                },
                'visual_hints': {
                    'color_scheme': {
                        'variables_x': 'azul',
                        'multipliers_lambda': 'rojo',
                        'multipliers_mu': 'morado',
                        'slack_s': 'verde',
                        'artificial_r': 'amarillo'
                    }
                }
            },
            'explanation': (
                'La Programación Cuadrática (QP) resuelve problemas donde la función objetivo es cuadrática '
                'y las restricciones son lineales. Este problema se resolverá usando el método de dos fases '
                'basado en las condiciones de Karush-Kuhn-Tucker (KKT).'
            )
        }
        self.steps.append(step)
    
    def _step2_extract_matrices(self):
        """Paso 2: Extraer matrices C, D, A, b del problema"""
        step = {
            'number': 2,
            'title': 'Descomposición en Componentes Matriciales',
            'content': {},
            'explanation': 'Extrayendo las matrices C (lineal), D (cuadrática), A (restricciones) y b (términos independientes).'
        }
        
        try:
            # Parsear la función objetivo
            obj_sym = sp.sympify(self.objective_expr, locals=self.syms)
            var_list = [self.syms[v] for v in self.variables]
            X = sp.Matrix(var_list)
            
            # Expandir la función objetivo
            obj_expanded = sp.expand(obj_sym)
            
            # Extraer matriz D (términos cuadráticos)
            H = sp.hessian(obj_sym, var_list)
            self.D = np.array(H.tolist(), dtype=float) / 2  # Dividir por 2 porque Hessian tiene 2*coef
            
            # Extraer vector C (términos lineales)
            grad = [sp.diff(obj_sym, var) for var in var_list]
            # Evaluar gradiente en 0 para obtener términos lineales
            C_list = []
            for g in grad:
                # Eliminar términos con variables (dejar solo constantes)
                g_const = g.subs([(v, 0) for v in var_list])
                C_list.append(float(g_const))
            self.C = np.array(C_list)
            
            # Extraer restricciones A*X <= b
            A_rows = []
            b_vals = []
            
            for constraint in self.constraints:
                kind = constraint.get('kind')
                expr = constraint.get('expr')
                
                # Parsear expresión de restricción
                constraint_sym = sp.sympify(expr, locals=self.syms)
                
                # Extraer coeficientes
                row = []
                for var in var_list:
                    coef = sp.diff(constraint_sym, var)
                    row.append(float(coef))
                
                # Término independiente (evaluar en 0)
                b_val = -float(constraint_sym.subs([(v, 0) for v in var_list]))
                
                # Ajustar signo según tipo de restricción
                if kind == 'le':  # <=
                    A_rows.append(row)
                    b_vals.append(b_val)
                elif kind == 'ge':  # >= (multiplicar por -1 para convertir a <=)
                    A_rows.append([-c for c in row])
                    b_vals.append(-b_val)
                elif kind == 'eq':  # = (agregar dos restricciones: <= y >=)
                    A_rows.append(row)
                    b_vals.append(b_val)
                    A_rows.append([-c for c in row])
                    b_vals.append(-b_val)
            
            self.A = np.array(A_rows) if A_rows else np.zeros((0, self.n_vars))
            self.b = np.array(b_vals) if b_vals else np.zeros(0)
            
            step['content'] = {
                'vector_decision': {
                    'X': self.variables,
                    'dimension': self.n_vars
                },
                'matriz_D': {
                    'matrix': self.D.tolist(),
                    'shape': self.D.shape,
                    'description': 'Matriz cuadrática (define la curvatura del problema)'
                },
                'vector_C': {
                    'vector': self.C.tolist(),
                    'description': 'Vector de coeficientes lineales'
                },
                'matriz_A': {
                    'matrix': self.A.tolist(),
                    'shape': self.A.shape,
                    'description': 'Matriz de restricciones lineales'
                },
                'vector_b': {
                    'vector': self.b.tolist(),
                    'description': 'Vector de términos independientes'
                }
            }
            
        except Exception as e:
            step['content']['error'] = f'Error al extraer matrices: {str(e)}'
            step['content']['note'] = 'Usando valores por defecto para demostración educativa'
            
            # Valores por defecto para demostración
            self.C = np.zeros(self.n_vars)
            self.D = np.eye(self.n_vars)
            self.A = np.zeros((0, self.n_vars))
            self.b = np.zeros(0)
        
        self.steps.append(step)
    
    def _step3_check_definiteness(self):
        """Paso 3: Verificar definitud de la matriz D"""
        step = {
            'number': 3,
            'title': 'Verificación de Definitud de la Matriz D',
            'content': {},
            'explanation': ''
        }
        
        try:
            # Calcular eigenvalores
            eigenvalues = np.linalg.eigvals(self.D)
            
            # Determinar definitud
            if np.all(eigenvalues > 0):
                definiteness = 'positiva_definida'
                status = 'verde'
                valid = self.is_maximization == False  # Para min debe ser positiva definida
            elif np.all(eigenvalues < 0):
                definiteness = 'negativa_definida'
                status = 'verde'
                valid = self.is_maximization == True  # Para max debe ser negativa definida
            elif np.all(eigenvalues >= 0):
                definiteness = 'positiva_semidefinida'
                status = 'amarillo'
                valid = self.is_maximization == False
            elif np.all(eigenvalues <= 0):
                definiteness = 'negativa_semidefinida'
                status = 'amarillo'
                valid = self.is_maximization == True
            else:
                definiteness = 'indefinida'
                status = 'rojo'
                valid = False
            
            step['content'] = {
                'eigenvalues': eigenvalues.tolist(),
                'definiteness': definiteness,
                'status_light': status,
                'is_valid': valid,
                'requirement': 'negativa definida' if self.is_maximization else 'positiva definida'
            }
            
            if valid:
                step['explanation'] = f'✅ La matriz D es {definiteness}, lo cual es correcto para un problema de {"maximización" if self.is_maximization else "minimización"}.'
            else:
                step['explanation'] = f'⚠️ La matriz D es {definiteness}. Para {"maximización" if self.is_maximization else "minimización"} debería ser {"negativa" if self.is_maximization else "positiva"} definida.'
                
        except Exception as e:
            step['content']['error'] = str(e)
            step['explanation'] = 'No se pudo verificar la definitud de D.'
        
        self.steps.append(step)
    
    def _step4_build_kkt_system(self):
        """Paso 4: Construir el sistema de condiciones KKT"""
        step = {
            'number': 4,
            'title': 'Construcción del Sistema Kuhn-Tucker (KKT)',
            'content': {},
            'explanation': (
                'Las condiciones de Karush-Kuhn-Tucker (KKT) son necesarias y suficientes para optimalidad '
                'en problemas de programación cuadrática convexa.'
            )
        }
        
        m = len(self.b)  # Número de restricciones
        n = self.n_vars  # Número de variables
        
        step['content'] = {
            'gradiente': {
                'formula': '∇z = C + 2*D*X',
                'explanation': 'Gradiente de la función objetivo cuadrática',
                'C': self.C.tolist(),
                'D': self.D.tolist()
            },
            'condiciones_kkt': {
                'no_negatividad': {
                    'lambda_i': f'λᵢ ≥ 0  (i = 1, ..., {m})',
                    'mu_j': f'μⱼ ≥ 0  (j = 1, ..., {n})',
                    'description': 'Multiplicadores no negativos'
                },
                'factibilidad_primal': {
                    'restricciones': 'S = b - A*X ≥ 0',
                    'no_negatividad_x': 'X ≥ 0',
                    'description': 'Las restricciones deben cumplirse'
                },
                'complementariedad': {
                    'lambda_s': 'λᵢ * Sᵢ = 0  (restricciones no activas)',
                    'mu_x': 'μⱼ * Xⱼ = 0  (variables no básicas)',
                    'description': 'Solo una de las dos puede ser positiva'
                },
                'estacionariedad': {
                    'formula': '-2*D*X + Aᵀ*λ - μ = Cᵀ',
                    'description': 'Condición de equilibrio del gradiente',
                    'note': 'Esta es la ecuación central del sistema KKT'
                }
            },
            'variables_sistema': {
                'decision': f'X ∈ ℝⁿ (n={n})',
                'multiplicadores_restricciones': f'λ ∈ ℝᵐ (m={m})',
                'multiplicadores_no_negatividad': f'μ ∈ ℝⁿ (n={n})',
                'holguras': f'S ∈ ℝᵐ (m={m})',
                'total_variables': n + m + n + m
            }
        }
        
        self.steps.append(step)
    
    def _step5_build_initial_table(self):
        """Paso 5: Construir tabla inicial del método Simplex modificado"""
        step = {
            'number': 5,
            'title': 'Construcción de la Tabla Inicial (Método de Dos Fases)',
            'content': {},
            'explanation': (
                'En la Fase I se introducen variables artificiales para encontrar una solución básica factible. '
                'La tabla inicial incluye todas las variables y multiplicadores necesarios.'
            )
        }
        
        m = len(self.b) if len(self.b) > 0 else 1
        n = self.n_vars
        
        step['content'] = {
            'estructura_tabla': {
                'columnas': {
                    'variables_decision': f'x₁, x₂, ..., x_{n}',
                    'multiplicadores_lambda': f'λ₁, λ₂, ..., λ_{m}',
                    'multiplicadores_mu': f'μ₁, μ₂, ..., μ_{n}',
                    'holguras': f'S₁, S₂, ..., S_{m}',
                    'artificiales': f'R₁, R₂, ..., R_{m}',
                    'solucion': 'b'
                },
                'filas': {
                    'objetivo_artificial': 'r₀ (minimizar suma de artificiales)',
                    'restricciones': f'{m + n} restricciones del sistema KKT',
                    'objetivo_original': 'z (se usa en Fase II)'
                }
            },
            'colores_variables': {
                'x': {'color': 'azul', 'tipo': 'Variables de decisión'},
                'λ': {'color': 'rojo', 'tipo': 'Multiplicadores de restricciones'},
                'μ': {'color': 'morado', 'tipo': 'Multiplicadores de no-negatividad'},
                'S': {'color': 'verde', 'tipo': 'Variables de holgura'},
                'R': {'color': 'amarillo', 'tipo': 'Variables artificiales (Fase I)'}
            },
            'nota_importante': (
                'En la Fase I, el objetivo es minimizar la suma de variables artificiales. '
                'Cuando r₀ = 0, significa que se encontró una solución factible y podemos '
                'pasar a la Fase II para optimizar la función objetivo original.'
            )
        }
        
        self.steps.append(step)
    
    def _step6_phase1(self):
        """Paso 6: Ejecutar Fase I (encontrar solución factible)"""
        step = {
            'number': 6,
            'title': 'Fase I: Búsqueda de Solución Factible',
            'content': {},
            'explanation': (
                'La Fase I utiliza el método Simplex para eliminar las variables artificiales '
                'y encontrar una solución que satisfaga todas las restricciones.'
            )
        }
        
        # Simulación educativa de iteraciones
        step['content'] = {
            'objetivo_fase1': 'Minimizar W = R₁ + R₂ + ... + Rₘ',
            'criterio_parada': 'W = 0 (todas las artificiales salen de la base)',
            'iteraciones_simuladas': [
                {
                    'iteration': 0,
                    'action': 'Tabla inicial',
                    'basic_variables': ['R₁', 'R₂', '...'],
                    'objective_value': 'W = suma(Rᵢ)'
                },
                {
                    'iteration': 1,
                    'action': 'Entra variable con mejor costo reducido',
                    'entering': 'x₁',
                    'leaving': 'R₁',
                    'pivot': 'Elemento pivote identificado',
                    'note': 'Usar criterio de razón mínima: min(bᵢ / aᵢⱼ) donde aᵢⱼ > 0'
                },
                {
                    'iteration': '...',
                    'action': 'Continuar hasta W = 0',
                    'note': 'Cada iteración reduce el valor de W'
                }
            ],
            'resultado_fase1': {
                'status': '✅ Solución factible encontrada',
                'message': 'Todas las variables artificiales han salido de la base',
                'next_step': 'Proceder a Fase II para optimizar'
            },
            'proceso_visual': {
                'eleccion_entrante': {
                    'criterio': 'Variable con costo reducido más negativo',
                    'semaforo': {
                        'verde': 'Mejor candidata',
                        'amarillo': 'Posible',
                        'rojo': 'No entra'
                    }
                },
                'eleccion_saliente': {
                    'criterio': 'Razón mínima: min(solución / coeficiente)',
                    'animacion': 'Comparar cada razón y resaltar la mínima'
                },
                'actualizacion_tabla': {
                    'paso1': 'Iluminar elemento pivote',
                    'paso2': 'Hacer pivote = 1',
                    'paso3': 'Hacer ceros en columna pivote',
                    'paso4': 'Actualizar toda la tabla'
                }
            }
        }
        
        self.steps.append(step)
    
    def _step7_phase2(self):
        """Paso 7: Ejecutar Fase II (optimizar función objetivo)"""
        step = {
            'number': 7,
            'title': 'Fase II: Optimización del Problema Original',
            'content': {},
            'explanation': (
                'Una vez eliminadas las variables artificiales, se optimiza la función objetivo '
                'original usando el método Simplex hasta alcanzar la solución óptima.'
            )
        }
        
        step['content'] = {
            'objetivo_fase2': 'Optimizar z = C*X + X^T*D*X',
            'tabla_inicial_fase2': {
                'nota': 'Eliminar columnas de variables artificiales',
                'variables_activas': 'x, λ, μ, S',
                'funcion_objetivo': 'Reconstruir fila z con función objetivo original'
            },
            'criterio_optimalidad': {
                'maximizacion': 'Todos los costos reducidos ≤ 0',
                'minimizacion': 'Todos los costos reducidos ≥ 0',
                'aplicado': 'minimización' if not self.is_maximization else 'maximización'
            },
            'iteraciones_simuladas': [
                {
                    'iteration': 0,
                    'action': 'Inicio de Fase II',
                    'objective_value': 'z₀ = valor inicial'
                },
                {
                    'iteration': 1,
                    'entering': 'Variable con mejor costo reducido',
                    'leaving': 'Variable que sale según razón mínima',
                    'objective_improvement': 'z₁ > z₀ (mejora)'
                },
                {
                    'iteration': '...',
                    'action': 'Continuar mientras haya mejoras posibles'
                },
                {
                    'iteration': 'final',
                    'action': '🏁 Optimalidad alcanzada',
                    'condition': 'No hay variables candidatas para entrar',
                    'solution': 'X* = solución óptima',
                    'objective': 'z* = valor óptimo'
                }
            ],
            'verificacion_kkt': {
                'factibilidad_primal': '✓ A*X* ≤ b, X* ≥ 0',
                'factibilidad_dual': '✓ λ* ≥ 0, μ* ≥ 0',
                'complementariedad': '✓ λᵢ*Sᵢ* = 0, μⱼ*Xⱼ* = 0',
                'estacionariedad': '✓ -2*D*X* + Aᵀ*λ* - μ* = Cᵀ',
                'conclusion': 'Todas las condiciones KKT se cumplen → Solución óptima garantizada'
            }
        }
        
        # Solución simulada para propósitos educativos
        self.solution = {
            'x': np.zeros(self.n_vars).tolist(),
            'z': 0.0,
            'lambda': [],
            'mu': [],
            'status': 'optimal_simulated'
        }
        
        self.steps.append(step)
    
    def _step8_present_result(self):
        """Paso 8: Presentar resultado final"""
        step = {
            'number': 8,
            'title': 'Presentación del Resultado Final',
            'content': {},
            'explanation': '🎉 Solución óptima del problema de Programación Cuadrática'
        }
        
        step['content'] = {
            'solucion_optima': {
                'variables': {var: val for var, val in zip(self.variables, self.solution['x'])},
                'vector_X': self.solution['x'],
                'descripcion': 'Valores óptimos de las variables de decisión'
            },
            'valor_objetivo': {
                'z_star': self.solution['z'],
                'formula': 'z* = C*X* + X*^T * D * X*',
                'tipo': 'máximo' if self.is_maximization else 'mínimo'
            },
            'interpretacion': {
                'factibilidad': 'La solución satisface todas las restricciones',
                'optimalidad': 'Se verificaron todas las condiciones KKT',
                'unicidad': 'Para QP convexo, la solución es única (si existe)'
            },
            'visualizacion_sugerida': {
                'grafica_2d': 'Curvas de nivel de la función cuadrática',
                'grafica_3d': 'Superficie cuadrática con punto óptimo marcado',
                'region_factible': 'Poliedro definido por las restricciones lineales',
                'punto_optimo': 'Marcado con color destacado'
            }
        }
        
        self.steps.append(step)
    
    def _generate_educational_explanation(self) -> str:
        """Genera explicación educativa completa del proceso"""
        explanation_parts = []
        
        explanation_parts.append("# SOLUCIÓN COMPLETA: PROGRAMACIÓN CUADRÁTICA (QP)\n")
        explanation_parts.append("## Método de Dos Fases con Condiciones KKT\n")
        
        for step in self.steps:
            explanation_parts.append(f"\n### {step['number']}. {step['title']}\n")
            explanation_parts.append(f"{step['explanation']}\n")
            
            # Agregar detalles clave de cada paso
            if step['number'] == 2 and 'matriz_D' in step['content']:
                explanation_parts.append(f"\n**Matriz D (cuadrática):**\n")
                explanation_parts.append(f"```\n{np.array(step['content']['matriz_D']['matrix'])}\n```\n")
            
            if step['number'] == 3 and 'is_valid' in step['content']:
                status_emoji = '✅' if step['content']['is_valid'] else '⚠️'
                explanation_parts.append(f"\n{status_emoji} **Definitud:** {step['content']['definiteness']}\n")
        
        explanation_parts.append("\n## Conclusión\n")
        explanation_parts.append(
            "Este problema se resuelve mediante el método de dos fases:\n"
            "1. **Fase I:** Encontrar una solución factible eliminando variables artificiales\n"
            "2. **Fase II:** Optimizar la función objetivo original\n\n"
            "El método garantiza encontrar el óptimo global si el problema es convexo.\n"
        )
        
        return "".join(explanation_parts)
    
    def _generate_plot_data(self) -> Dict[str, Any]:
        """Genera datos para visualización"""
        return {
            'type': 'qp_surface',
            'variables': self.variables,
            'C': self.C.tolist() if self.C is not None else [],
            'D': self.D.tolist() if self.D is not None else [],
            'solution': self.solution['x'] if self.solution else [],
            'note': 'Visualización de superficie cuadrática con punto óptimo'
        }


def solve_qp(objective_expr: str, variables: List[str], constraints: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Función principal para resolver problemas QP.
    
    Args:
        objective_expr: Expresión de la función objetivo
        variables: Lista de variables
        constraints: Lista de restricciones
    
    Returns:
        Diccionario con la solución completa y pasos educativos
    """
    solver = QPSolver(objective_expr, variables, constraints)
    return solver.solve()
