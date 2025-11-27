"""
Test del formato ludico del solver QP.
"""

from opti_learn.opti_app.core.solver_qp_numerical import solve_qp


def test_formato_ludico():
    """Prueba el nuevo formato ludico y visual."""
    
    print("="*80)
    print("TEST: Formato Ludico del Solver QP")
    print("="*80)
    
    # Problema simple
    objective = "A**2 + B**2"
    variables = ["A", "B"]
    constraints = [
        {'expr': 'A + B', 'kind': 'eq', 'rhs': 100.0},
        {'expr': 'A', 'kind': 'ineq', 'rhs': 20.0}
    ]
    
    result = solve_qp(objective, variables, constraints)
    
    print(f"\nEstado: {result['status']}")
    
    if result['status'] == 'success':
        print("[OK] Solver ejecutado exitosamente")
        print(f"[OK] Pasos generados: {len(result.get('steps', []))}")
        print(f"[OK] Explicacion generada: {len(result.get('explanation', ''))} caracteres")
        
        # Verificar que tiene emojis
        explanation = result.get('explanation', '')
        has_emojis = any(emoji in explanation for emoji in ['🎮', '📘', '🧩', '🔍', '🔧', '📊', '⭐', '🚀', '🏆'])
        
        if has_emojis:
            print("[OK] Formato ludico con emojis detectado")
        else:
            print("[WARN] No se detectaron emojis en la explicacion")
        
        # Verificar estructura
        if '# 🎮' in explanation:
            print("[OK] Encabezado ludico presente")
        if '## 📘' in explanation:
            print("[OK] Seccion de presentacion presente")
        if '## 🧩' in explanation:
            print("[OK] Seccion de matrices presente")
        if '## 🏆' in explanation:
            print("[OK] Seccion de solucion final presente")
        
        # Guardar en archivo UTF-8
        with open('output_qp_ludico.md', 'w', encoding='utf-8') as f:
            f.write(explanation)
        print("\n[OK] Explicacion guardada en: output_qp_ludico.md")
        
        return True
    else:
        print(f"[ERROR] Solver fallo: {result.get('message', '')}")
        return False


if __name__ == "__main__":
    success = test_formato_ludico()
    print("\n" + "="*80)
    if success:
        print("RESULTADO: EXITO")
        print("Abre 'output_qp_ludico.md' para ver el formato completo")
    else:
        print("RESULTADO: FALLO")
    print("="*80)
