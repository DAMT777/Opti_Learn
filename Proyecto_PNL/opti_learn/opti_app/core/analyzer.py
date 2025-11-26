from __future__ import annotations

from typing import Dict, List, Any

import sympy as sp


FUNCIONES_PERMITIDAS = {
    'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
    'exp': sp.exp, 'log': sp.log, 'sqrt': sp.sqrt,
    'abs': sp.Abs,
}


def _a_expresion_sympy(expresion: str, simbolos: Dict[str, sp.Symbol]) -> sp.Expr:
    return sp.sympify(expresion, locals={**FUNCIONES_PERMITIDAS, **simbolos})


def analizar_problema(entrada: Dict[str, Any]) -> Dict[str, Any]:
    expresion_objetivo = entrada.get('objective_expr')
    nombres_variables = entrada.get('variables') or []
    restricciones = entrada.get('constraints') or []

    # Variables: usar aportadas o detectar por símbolos libres
    if nombres_variables:
        simbolos = {nombre: sp.Symbol(nombre, real=True) for nombre in nombres_variables}
    else:
        # Intento de parseo preliminar para detectar variables
        expr_temporal = sp.sympify(expresion_objetivo, locals=FUNCIONES_PERMITIDAS)
        libres = sorted([str(s) for s in expr_temporal.free_symbols])
        nombres_variables = libres
        simbolos = {nombre: sp.Symbol(nombre, real=True) for nombre in nombres_variables}

    funcion = _a_expresion_sympy(expresion_objetivo, simbolos)

    # Normalizar restricciones
    restricciones_normalizadas: List[Dict[str, Any]] = []
    hay_igualdades = False
    hay_desigualdades = False
    restricciones_lineales = True
    for restr in restricciones:
        tipo = restr.get('kind')
        expr = restr.get('expr')
        if tipo not in ('eq', 'le', 'ge'):
            continue
        if tipo == 'eq':
            hay_igualdades = True
        else:
            hay_desigualdades = True
        g = _a_expresion_sympy(expr, simbolos)
        restricciones_normalizadas.append({'kind': tipo, 'expr': expr, 'normalized': str(g)})
        # Lineal si el grado total es <= 1
        try:
            polinomio = sp.Poly(g, *[simbolos[v] for v in nombres_variables])
            if polinomio.total_degree() > 1:
                restricciones_lineales = False
        except Exception:
            restricciones_lineales = False

    # ¿Cuadrática?
    es_cuadratica = False
    try:
        sp.quadraticform.quadratic_form(funcion, [simbolos[v] for v in nombres_variables])
        es_cuadratica = True
    except Exception:
        try:
            polinomio = sp.Poly(funcion, *[simbolos[v] for v in nombres_variables])
            es_cuadratica = polinomio.total_degree() == 2
        except Exception:
            es_cuadratica = False

    pista_convexidad = None
    try:
        hessiano = sp.hessian(funcion, [simbolos[v] for v in nombres_variables])
        pista_convexidad = str(hessiano)
    except Exception:
        pista_convexidad = None

    return {
        'variables': nombres_variables,
        'objective_expr': str(funcion),
        'constraints_normalized': restricciones_normalizadas,
        'has_equalities': hay_igualdades,
        'has_inequalities': hay_desigualdades,
        'has_constraints': bool(restricciones_normalizadas),
        'constraints_are_linear': restricciones_lineales if restricciones_normalizadas else False,
        'is_quadratic': es_cuadratica,
        'convexity_hint': pista_convexidad,
    }


def construir_funciones_numericas_sympy(expresion_objetivo: str, nombres_variables: List[str]):
    simbolos = [sp.Symbol(v, real=True) for v in nombres_variables]
    funcion = sp.sympify(expresion_objetivo, locals=FUNCIONES_PERMITIDAS | {v.name: v for v in simbolos})
    gradiente = [sp.diff(funcion, v) for v in simbolos]
    f_numerica = sp.lambdify([simbolos], funcion, modules='numpy')
    grad_numerica = sp.lambdify([simbolos], sp.Matrix(gradiente), modules='numpy')
    return f_numerica, grad_numerica


# Alias de compatibilidad
analyze_problem = analizar_problema
build_sympy_functions = construir_funciones_numericas_sympy
