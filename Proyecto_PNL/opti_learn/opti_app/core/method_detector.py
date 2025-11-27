"""
Módulo para detección automática del método de optimización correcto.

Implementa las 5 reglas en orden estricto para determinar qué método usar:
1. GRADIENTE - Si hay proceso iterativo
2. KKT - Si hay restricciones no lineales
3. LAGRANGE - Si solo hay restricciones de igualdad
4. QP - Si función cuadrática con restricciones lineales
5. DIFERENCIAL - Si no hay restricciones pero pide derivadas
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

import sympy as sp

from . import analyzer


# ============================================================================
# PALABRAS CLAVE PARA DETECCIÓN DE MÉTODOS
# ============================================================================

# REGLA 1: Proceso iterativo → GRADIENTE
ITERATIVE_KEYWORDS = [
    'iterar',
    'iterativo',
    'iterativa',
    'iteracion',
    'iteraciones',
    'método iterativo',
    'algoritmo iterativo',
    'descenso del gradiente',
    'gradient descent',
    'actualizar',
    'paso α',
    'paso alpha',
    'tasa de aprendizaje',
    'learning rate',
    'entrenamiento',
    'training',
    'varias iteraciones',
    'repetir el cálculo',
    'repetir cálculo',
    'line search',
    'búsqueda de línea',
    'backtracking',
    'tamaño de paso',
    'epoch',
    'aprendizaje',
    'ajuste de parámetros',
]

# REGLA 5: Derivadas sin restricciones → DIFERENCIAL
DERIVATIVE_KEYWORDS = [
    'punto crítico',
    'puntos críticos',
    'critical point',
    'critical points',
    'derivada',
    'derivadas',
    'derivar',
    'diferencial',
    'diferenciar',
    'calcular derivadas',
    'gradiente igual a cero',
    'máximo',
    'mínimo',
    'máximos',
    'mínimos',
    'punto de equilibrio',
    'puntos de equilibrio',
    'equilibrio',
    'equilibrium',
    'estable',
    'estables',
    'inestable',
    'inestables',
    'stability',
    'curvatura',
    'hessiano',
    'hessiana',
    '∂',  # símbolo parcial
]


# ============================================================================
# FUNCIONES DE NORMALIZACIÓN
# ============================================================================

def _normalize_text(text: str) -> str:
    """Normaliza texto para búsqueda insensible a mayúsculas/acentos."""
    import unicodedata
    
    normalized = unicodedata.normalize('NFD', text or '')
    stripped = ''.join(ch for ch in normalized if unicodedata.category(ch) != 'Mn')
    return stripped.lower()


# ============================================================================
# REGLA 1: DETECCIÓN DE PROCESO ITERATIVO
# ============================================================================

def _detect_iterative_process(text: str) -> bool:
    """
    REGLA 1: Si el problema menciona pasos repetidos → GRADIENTE
    
    Busca palabras clave como "iterar", "actualizar", "paso α", etc.
    """
    normalized = _normalize_text(text)
    return any(keyword in normalized for keyword in ITERATIVE_KEYWORDS)


# ============================================================================
# REGLA 2: DETECCIÓN DE RESTRICCIONES NO LINEALES
# ============================================================================

def _is_nonlinear_expression(expr_str: str) -> bool:
    """
    Determina si una expresión es no lineal.
    
    No lineal = tiene cuadrados (x²), productos de variables (xy), 
    raíces, divisiones entre variables, etc.
    """
    try:
        expr = sp.sympify(expr_str, locals=analyzer.FUNCIONES_PERMITIDAS)
        
        # Si tiene grado > 1, es no lineal
        if expr.is_polynomial():
            # Obtener todas las variables
            variables = list(expr.free_symbols)
            if not variables:
                return False
            
            # Verificar el grado total del polinomio
            for var in variables:
                degree = sp.degree(expr, gen=var)
                if degree > 1:
                    return True
            
            # Verificar productos cruzados (xy, x*y, etc.)
            if len(variables) > 1:
                # Expandir y buscar términos con múltiples variables
                expanded = sp.expand(expr)
                for term in sp.Add.make_args(expanded):
                    # Contar cuántas variables aparecen en este término
                    term_vars = term.free_symbols
                    if len(term_vars) > 1:
                        return True  # Producto de variables → no lineal
        
        # Buscar funciones no lineales (sqrt, log, exp, sin, cos, etc.)
        for func_type in [sp.sqrt, sp.log, sp.exp, sp.sin, sp.cos, sp.tan, sp.Pow]:
            if expr.has(func_type):
                return True
        
        # Buscar divisiones con variables en denominador
        for atom in expr.atoms(sp.Pow):
            if atom.exp.is_negative and atom.base.free_symbols:
                return True  # x^-1 = 1/x → no lineal
        
        return False
        
    except Exception:
        # Si no se puede parsear, asumir que podría ser no lineal
        # Buscar patrones comunes: x², x^2, sqrt, *, /, etc.
        patterns = [
            r'[a-zA-Z]\s*\^?\s*[2-9]',  # x^2, x2, y^3
            r'[a-zA-Z]\*\*[2-9]',  # x**2
            r'[a-zA-Z]\s*\*\s*[a-zA-Z]',  # x*y
            r'sqrt|log|exp|sin|cos|tan',  # funciones no lineales
            r'[a-zA-Z]\s*/\s*[a-zA-Z]',  # x/y
        ]
        return any(re.search(pattern, expr_str, re.IGNORECASE) for pattern in patterns)


def _has_nonlinear_constraints(constraints: List[Dict[str, Any]]) -> bool:
    """
    REGLA 2: Si hay restricciones no lineales → KKT
    
    Una restricción es no lineal si tiene cuadrados, productos de variables,
    raíces, divisiones entre variables, etc.
    """
    for constraint in constraints:
        expr = constraint.get('expr', '')
        if _is_nonlinear_expression(expr):
            return True
    return False


# ============================================================================
# REGLA 3: DETECCIÓN DE SOLO IGUALDADES
# ============================================================================

def _has_only_equality_constraints(constraints: List[Dict[str, Any]]) -> bool:
    """
    REGLA 3: Si solo hay restricciones de igualdad → LAGRANGE
    
    Verifica que:
    - Hay al menos una restricción
    - Todas las restricciones son de igualdad (kind='eq')
    - No hay desigualdades (kind='le' o 'ge')
    """
    if not constraints:
        return False
    
    # Verificar que todas sean igualdades
    for constraint in constraints:
        kind = constraint.get('kind', '')
        if kind != 'eq':
            return False
    
    return True


# ============================================================================
# REGLA 4: DETECCIÓN DE PROGRAMACIÓN CUADRÁTICA
# ============================================================================

def _is_quadratic_objective(expr_str: str) -> bool:
    """
    Determina si una función objetivo es cuadrática.
    
    Cuadrática = tiene términos x², y², xy pero NO términos de grado > 2
    """
    try:
        expr = sp.sympify(expr_str, locals=analyzer.FUNCIONES_PERMITIDAS)
        
        # Verificar que sea polinomio
        if not expr.is_polynomial():
            return False
        
        # Obtener variables
        variables = list(expr.free_symbols)
        if not variables:
            return False
        
        # El grado total debe ser exactamente 2
        expanded = sp.expand(expr)
        max_degree = 0
        
        for term in sp.Add.make_args(expanded):
            # Calcular el grado de este término
            term_degree = 0
            for var in variables:
                term_degree += sp.degree(term, gen=var)
            
            max_degree = max(max_degree, term_degree)
        
        # Debe tener al menos un término de grado 2
        return max_degree == 2
        
    except Exception:
        # Buscar patrones de cuadrados en el texto
        patterns = [
            r'[a-zA-Z]\s*\^?\s*2',  # x^2, x2
            r'[a-zA-Z]\*\*2',  # x**2
        ]
        return any(re.search(pattern, expr_str) for pattern in patterns)


def _has_only_linear_constraints(constraints: List[Dict[str, Any]]) -> bool:
    """
    Verifica que todas las restricciones sean lineales.
    
    Lineal = solo sumas, restas y multiplicaciones por constantes.
    """
    for constraint in constraints:
        expr = constraint.get('expr', '')
        if _is_nonlinear_expression(expr):
            return False
    
    return True


def _is_qp_problem(objective_expr: str, constraints: List[Dict[str, Any]]) -> bool:
    """
    Verifica si es un problema de Programación Cuadrática.
    
    Verifica que:
    - La función objetivo tiene términos cuadráticos
    - Todas las restricciones son lineales
    - Hay al menos una restricción
    """
    if not constraints:
        return False
    
    # La función debe ser cuadrática
    if not _is_quadratic_objective(objective_expr):
        return False
    
    # Todas las restricciones deben ser lineales
    if not _has_only_linear_constraints(constraints):
        return False
    
    return True


def _has_any_inequalities(constraints: List[Dict[str, Any]]) -> bool:
    """
    Verifica si hay al menos una desigualdad en las restricciones.
    
    Una desigualdad es kind='le' o kind='ge'.
    """
    for constraint in constraints:
        kind = constraint.get('kind', '')
        if kind in ('le', 'ge'):
            return True
    return False


def _is_explicit_qp(text: str, objective_expr: str, constraints: List[Dict[str, Any]]) -> bool:
    """
    REGLA 3: Determina si el problema es de Programación Cuadrática.
    
    QP se identifica cuando se cumple UNA de estas condiciones:
    
    A) Menciona explícitamente QP:
       - El texto contiene "Programación Cuadrática", "QP", "quadratic programming"
       Y cumple estructura básica (cuadrática + lineal)
    
    B) Tiene estructura QP CON mezcla de igualdades Y desigualdades:
       - Función objetivo cuadrática (grado 2)
       - TODAS las restricciones lineales (grado 1)
       - Hay al menos UNA restricción de igualdad
       - Hay al menos UNA restricción de desigualdad
    
    IMPORTANTE: 
    - Si SOLO hay igualdades → NO es QP, es Lagrange (Regla 4)
    - Si SOLO hay desigualdades → NO es QP, es KKT (Regla 5)
    """
    # Verificar estructura básica primero
    if not _is_qp_problem(objective_expr, constraints):
        return False
    
    # Verificar mención explícita de QP
    normalized = _normalize_text(text)
    qp_keywords = [
        'programacion cuadratica',
        'programación cuadrática',
        'quadratic programming',
        ' qp ',
        'forma cuadratica',
        'forma cuadrática',
    ]
    
    if any(keyword in normalized for keyword in qp_keywords):
        return True
    
    # Si no menciona QP, verificar que haya MEZCLA de igualdades y desigualdades
    has_equality = any(c.get('kind') == 'eq' for c in constraints)
    has_inequality = any(c.get('kind') in ('le', 'ge') for c in constraints)
    
    # QP requiere AMBAS: al menos una igualdad Y al menos una desigualdad
    return has_equality and has_inequality


# ============================================================================
# REGLA 5: DETECCIÓN DE CÁLCULO DIFERENCIAL
# ============================================================================

def _asks_for_derivatives(text: str) -> bool:
    """
    REGLA 5: Si pide derivadas/puntos críticos → DIFERENCIAL
    
    Busca palabras como "punto crítico", "derivada", "máximo", "mínimo", etc.
    """
    normalized = _normalize_text(text)
    return any(keyword in normalized for keyword in DERIVATIVE_KEYWORDS)


# ============================================================================
# FUNCIÓN PRINCIPAL: DETERMINAR MÉTODO
# ============================================================================

def determine_method(
    text: str,
    objective_expr: Optional[str] = None,
    constraints: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Determina el método correcto siguiendo las reglas EN ORDEN.
    
    Args:
        text: Texto completo del problema
        objective_expr: Expresión de la función objetivo (opcional)
        constraints: Lista de restricciones parseadas (opcional)
    
    Returns:
        Uno de: 'gradient', 'kkt', 'lagrange', 'qp', 'differential'
    
    Reglas aplicadas en orden:
    1. Si menciona proceso iterativo → GRADIENTE
    2. Si hay restricciones no lineales → KKT
    3. Si función cuadrática + restricciones lineales + mezcla igualdades/desigualdades → QP
    4. Si solo hay restricciones de igualdad → LAGRANGE
    5. Si hay desigualdades (lineales o mixtas) → KKT
    6. Si no hay restricciones:
       - Si pide derivadas → DIFERENCIAL
       - Si no → GRADIENTE
    """
    constraints = constraints or []
    
    # REGLA 1: Proceso iterativo → GRADIENTE
    if _detect_iterative_process(text):
        return 'gradient'
    
    # REGLA 2: Restricciones no lineales → KKT
    if constraints and _has_nonlinear_constraints(constraints):
        return 'kkt'
    
    # REGLA 3: QP si tiene estructura cuadrática + restricciones lineales + igualdad
    if objective_expr and constraints and _is_explicit_qp(text, objective_expr, constraints):
        return 'qp'
    
    # REGLA 4: Solo igualdades (sin función cuadrática o sin igualdad estructural) → LAGRANGE
    if _has_only_equality_constraints(constraints):
        return 'lagrange'
    
    # REGLA 5: Si hay desigualdades (con o sin igualdades) → KKT
    if constraints and _has_any_inequalities(constraints):
        return 'kkt'
    
    # REGLA 6: Sin restricciones
    if not constraints:
        # Si pide derivadas → DIFERENCIAL
        if _asks_for_derivatives(text):
            return 'differential'
        # Si no, por defecto → GRADIENTE
        return 'gradient'
    
    # Por defecto → GRADIENTE
    return 'gradient'


# ============================================================================
# FUNCIÓN: EXPLICAR POR QUÉ SE ELIGIÓ EL MÉTODO
# ============================================================================

def explain_method_choice(
    text: str,
    objective_expr: Optional[str] = None,
    constraints: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Determina el método y explica por qué se eligió.
    
    Returns:
        {
            'method': str,
            'reason': str,
            'rule_applied': int  # 1-5
        }
    """
    constraints = constraints or []
    
    # REGLA 1
    if _detect_iterative_process(text):
        return {
            'method': 'gradient',
            'reason': 'El problema menciona un proceso iterativo (palabras como "iterar", "actualizar", "paso α", etc.)',
            'rule_applied': 1
        }
    
    # REGLA 2
    if constraints and _has_nonlinear_constraints(constraints):
        return {
            'method': 'kkt',
            'reason': 'El problema tiene al menos una restricción no lineal (con cuadrados, productos de variables, raíces, etc.)',
            'rule_applied': 2
        }
    
    # REGLA 3 - QP por estructura matemática (requiere mezcla de igualdades y desigualdades)
    if objective_expr and constraints and _is_explicit_qp(text, objective_expr, constraints):
        return {
            'method': 'qp',
            'reason': 'El problema tiene función objetivo cuadrática con restricciones lineales, combinando igualdades y desigualdades (Programación Cuadrática)',
            'rule_applied': 3
        }
    
    # REGLA 4
    if _has_only_equality_constraints(constraints):
        return {
            'method': 'lagrange',
            'reason': 'El problema tiene solo restricciones de igualdad (sin desigualdades)',
            'rule_applied': 4
        }
    
    # REGLA 5 - Si hay desigualdades → KKT
    if constraints and _has_any_inequalities(constraints):
        return {
            'method': 'kkt',
            'reason': 'El problema tiene restricciones con desigualdades (≤ o ≥), requiere condiciones KKT',
            'rule_applied': 5
        }
    
    # REGLA 6 - Sin restricciones
    if not constraints:
        if _asks_for_derivatives(text):
            return {
                'method': 'differential',
                'reason': 'No hay restricciones y el problema pide calcular derivadas, puntos críticos o extremos',
                'rule_applied': 6
            }
        else:
            return {
                'method': 'gradient',
                'reason': 'No hay restricciones y se busca optimizar (minimizar/maximizar)',
                'rule_applied': 6
            }
    
    # Por defecto
    return {
        'method': 'gradient',
        'reason': 'Caso por defecto para problemas de optimización',
        'rule_applied': 6
    }


# ============================================================================
# FUNCIÓN: EXTRAER PARÁMETROS PARA CADA SOLVER
# ============================================================================

def extract_solver_parameters(
    method: str,
    objective_expr: str,
    constraints: List[Dict[str, Any]],
    variables: List[str],
    x0: Optional[List[float]] = None,
    tol: Optional[float] = None,
    max_iter: Optional[int] = None
) -> Dict[str, Any]:
    """
    Extrae los parámetros necesarios para cada solver en formato JSON.
    
    Args:
        method: Método detectado ('gradient', 'kkt', 'lagrange', 'qp', 'differential')
        objective_expr: Expresión de la función objetivo
        constraints: Lista de restricciones
        variables: Lista de nombres de variables
        x0: Punto inicial (opcional)
        tol: Tolerancia (opcional)
        max_iter: Máximo de iteraciones (opcional)
    
    Returns:
        Diccionario con los parámetros específicos del solver
    """
    # Parámetros base comunes
    params: Dict[str, Any] = {
        'method': method,
        'objective': objective_expr,
        'variables': variables,
    }
    
    # Agregar restricciones si las hay
    if constraints:
        params['constraints'] = constraints
    
    # Parámetros específicos por método
    if method == 'gradient':
        params['x0'] = x0 or [0.0] * len(variables)
        params['tol'] = tol or 1e-6
        params['max_iter'] = max_iter or 1000
        params['alpha'] = 0.01  # Tasa de aprendizaje por defecto
        
    elif method == 'kkt':
        # KKT no necesita x0, pero puede ser útil
        if x0:
            params['x0'] = x0
        params['tol'] = tol or 1e-6
        
    elif method == 'lagrange':
        # Lagrange puede beneficiarse de x0 para método numérico
        if x0:
            params['x0'] = x0
        params['tol'] = tol or 1e-6
        
    elif method == 'qp':
        # QP necesita matrices Q, c, A, b
        # Por ahora solo marcamos que es QP
        params['x0'] = x0 or [0.0] * len(variables)
        params['tol'] = tol or 1e-6
        
    elif method == 'differential':
        # Cálculo diferencial no necesita x0 normalmente
        if x0:
            params['x0'] = x0
    
    return params


# ============================================================================
# FUNCIÓN COMPLETA: ANALIZAR PROBLEMA Y GENERAR JSON
# ============================================================================

def analyze_problem(text: str, parsed_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analiza un problema completo y genera el JSON para el solver.
    
    Args:
        text: Texto completo del problema
        parsed_data: Datos ya parseados (opcional, si no se proveen se parsea el texto)
    
    Returns:
        {
            'method': str,
            'method_explanation': {
                'reason': str,
                'rule_applied': int
            },
            'solver_params': {...},
            'raw_data': {...}  # Datos parseados originales
        }
    """
    # Si no hay datos parseados, usar los del message_parser
    if parsed_data is None:
        from . import message_parser
        parsed_data = message_parser.parse_structured_payload(text, allow_partial=True) or {}
    
    # Extraer datos
    objective_expr = parsed_data.get('objective_expr')
    constraints = parsed_data.get('constraints', [])
    variables = parsed_data.get('variables', [])
    x0 = parsed_data.get('x0')
    tol = parsed_data.get('tol')
    max_iter = parsed_data.get('max_iter')
    
    # Determinar método y obtener explicación
    explanation = explain_method_choice(text, objective_expr, constraints)
    method = explanation['method']
    
    # Extraer parámetros para el solver
    solver_params = extract_solver_parameters(
        method=method,
        objective_expr=objective_expr or '',
        constraints=constraints,
        variables=variables,
        x0=x0,
        tol=tol,
        max_iter=max_iter
    )
    
    return {
        'method': method,
        'method_explanation': {
            'reason': explanation['reason'],
            'rule_applied': explanation['rule_applied']
        },
        'solver_params': solver_params,
        'raw_data': parsed_data
    }
