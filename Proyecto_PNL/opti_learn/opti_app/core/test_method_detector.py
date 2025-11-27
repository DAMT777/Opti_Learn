"""
Script de prueba para el detector automático de métodos.

Ejemplos de problemas que demuestran cada una de las 5 reglas.
"""

from message_parser import parse_and_determine_method
import json


# ============================================================================
# EJEMPLOS DE PRUEBA
# ============================================================================

ejemplos = [
    # REGLA 1: Proceso iterativo → GRADIENTE
    {
        "nombre": "GRADIENTE - Proceso iterativo explícito",
        "texto": """
        Minimizar f(x,y) = x^2 + y^2 + 2*x*y
        usando el método del descenso del gradiente.
        Punto inicial: x0 = [1, 1]
        Tasa de aprendizaje: α = 0.1
        Realizar 100 iteraciones.
        """
    },
    
    # REGLA 2: Restricciones no lineales → KKT
    {
        "nombre": "KKT - Restricción con cuadrado",
        "texto": """
        Minimizar f(x,y) = x + y
        sujeto a:
        x^2 + y^2 <= 10
        x >= 0
        y >= 0
        """
    },
    
    {
        "nombre": "KKT - Restricción con producto de variables",
        "texto": """
        Maximizar f(x,y) = 2*x + 3*y
        sujeto a:
        x*y <= 100
        x + y <= 20
        """
    },
    
    # REGLA 3: Solo igualdades → LAGRANGE
    {
        "nombre": "LAGRANGE - Solo igualdades",
        "texto": """
        Minimizar f(x,y,z) = x^2 + y^2 + z^2
        sujeto a:
        x + y + z = 100
        2*x - y = 10
        """
    },
    
    # REGLA 4: Cuadrática + restricciones lineales → QP
    {
        "nombre": "QP - Función cuadrática con restricciones lineales",
        "texto": """
        Minimizar f(x,y) = x^2 + y^2 + x*y - 4*x - 5*y
        sujeto a:
        x + y <= 10
        2*x + y <= 15
        x >= 0
        y >= 0
        """
    },
    
    # REGLA 5a: Sin restricciones + derivadas → DIFERENCIAL
    {
        "nombre": "DIFERENCIAL - Puntos críticos",
        "texto": """
        Encontrar los puntos críticos de la función:
        f(x,y) = x^3 - 3*x*y + y^2
        
        Calcular las derivadas parciales e igualar a cero.
        """
    },
    
    # REGLA 5b: Sin restricciones + optimización → GRADIENTE
    {
        "nombre": "GRADIENTE - Sin restricciones, optimización",
        "texto": """
        Minimizar f(x,y) = x^2 + 2*y^2 - 4*x - 6*y + 10
        """
    },
]


# ============================================================================
# EJECUTAR PRUEBAS
# ============================================================================

def run_tests():
    """Ejecuta todos los ejemplos y muestra los resultados."""
    
    print("=" * 80)
    print("PRUEBAS DEL DETECTOR AUTOMÁTICO DE MÉTODOS")
    print("=" * 80)
    print()
    
    for i, ejemplo in enumerate(ejemplos, 1):
        print(f"\n{'='*80}")
        print(f"EJEMPLO {i}: {ejemplo['nombre']}")
        print('='*80)
        print(f"\nPROBLEMA:")
        print(ejemplo['texto'])
        print()
        
        # Analizar el problema
        resultado = parse_and_determine_method(ejemplo['texto'])
        
        if resultado:
            print(f"MÉTODO DETECTADO: {resultado['method'].upper()}")
            print(f"\nRAZÓN:")
            print(f"  {resultado['method_explanation']['reason']}")
            print(f"  (Regla {resultado['method_explanation']['rule_applied']})")
            
            print(f"\nPARÁMETROS DEL SOLVER:")
            print(json.dumps(resultado['solver_params'], indent=2, ensure_ascii=False))
            
        else:
            print("❌ No se pudo analizar el problema")
        
        print()


def test_specific_case(texto: str):
    """Prueba un caso específico."""
    
    print("=" * 80)
    print("ANÁLISIS DE PROBLEMA ESPECÍFICO")
    print("=" * 80)
    print(f"\nPROBLEMA:")
    print(texto)
    print()
    
    resultado = parse_and_determine_method(texto)
    
    if resultado:
        print(f"MÉTODO DETECTADO: {resultado['method'].upper()}")
        print(f"\nEXPLICACIÓN:")
        print(f"  {resultado['method_explanation']['reason']}")
        print(f"  (Aplicando Regla {resultado['method_explanation']['rule_applied']})")
        
        print(f"\nPARÁMETROS JSON:")
        print(json.dumps(resultado['solver_params'], indent=2, ensure_ascii=False))
        
        print(f"\nDATOS PARSEADOS:")
        print(json.dumps(resultado['raw_data'], indent=2, ensure_ascii=False))
        
    else:
        print("❌ No se pudo analizar el problema")
    
    print()
    return resultado


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    # Ejecutar todos los ejemplos
    run_tests()
    
    # Ejemplo de uso directo
    print("\n" + "=" * 80)
    print("EJEMPLO DE USO DIRECTO")
    print("=" * 80)
    
    mi_problema = """
    Minimizar C(x,y) = 50*x + 80*y
    sujeto a:
    x^2 + y <= 100
    x + y >= 10
    x >= 0, y >= 0
    """
    
    test_specific_case(mi_problema)
