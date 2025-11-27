"""Script para actualizar el prompt del AI Extractor con las reglas correctas de QP"""

import re

file_path = 'opti_learn/opti_app/consumers_ai.py'

# Leer el archivo
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# El nuevo prompt del AI Extractor
new_prompt = '''def _extract_payload_with_ai(text: str) -> Dict[str, Any] | None:
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "Eres el asistente de OptiLearn. Recibes problemas de Programacion No Lineal en lenguaje natural. "
                    "Debes extraer informacion estructurada en JSON.\\n\\n"
                    "TAREAS:\\n"
                    "1) Escribir la funcion objetivo en notacion SymPy (usa ** para potencias, * para productos).\\n"
                    "2) Listar las variables. Si no se declaran, deducelas de la funcion.\\n"
                    "3) Extraer TODAS las restricciones. Separa cotas dobles en DOS restricciones:\\n"
                    "   - 'A >= 20' → {\\"kind\\": \\"ge\\", \\"expr\\": \\"(A) - (20)\\"}\\n"
                    "   - '10 <= F <= 40' → DOS: {\\"kind\\": \\"ge\\", \\"expr\\": \\"(F) - (10)\\"} Y {\\"kind\\": \\"le\\", \\"expr\\": \\"(F) - (40)\\"}\\n"
                    "   - 'A + B + F = 100' → {\\"kind\\": \\"eq\\", \\"expr\\": \\"(A + B + F) - (100)\\"}\\n"
                    "4) Detectar el metodo aplicando ESTAS REGLAS EN ORDEN:\\n"
                    "   REGLA 1: Menciona proceso iterativo → gradient\\n"
                    "   REGLA 2: Restricciones NO LINEALES → kkt\\n"
                    "   REGLA 3: Funcion CUADRATICA + restricciones LINEALES + MEZCLA (>=1 igualdad Y >=1 desigualdad) → qp\\n"
                    "   REGLA 4: SOLO igualdades → lagrange\\n"
                    "   REGLA 5: Hay desigualdades → kkt\\n"
                    "   REGLA 6: Sin restricciones → gradient o differential\\n"
                    "   CRITICO QP: Requiere al menos UNA igualdad Y al menos UNA desigualdad. Solo igualdades → lagrange. Solo desigualdades → kkt.\\n\\n"
                    "CAMPOS JSON:\\n"
                    "- objective_expr: string\\n"
                    "- variables: [lista de strings]\\n"
                    "- constraints: [lista de {kind: eq|le|ge, expr: string}]\\n"
                    "- x0, tol, max_iter: opcionales\\n"
                    "- method: gradient|lagrange|kkt|qp|differential\\n"
                    "- method_hint: mismo valor que method\\n"
                    "- derivative_only: bool\\n\\n"
                    "Responde SOLO con el JSON, sin texto adicional."
                ),
            },
            {"role": "user", "content": text},
        ]'''

# Buscar el patrón de la función _extract_payload_with_ai
pattern = r'def _extract_payload_with_ai\(text: str\) -> Dict\[str, Any\] \| None:\s*try:\s*messages = \[\s*\{[^}]+\{[^}]+\}[^}]+\}[^}]+\{[^}]+\}[^}]+\]'

# Encontrar la posición
match = re.search(pattern, content, re.DOTALL)

if match:
    print("Patrón encontrado")
    # Reemplazar desde el inicio de la función hasta después de messages = [...]
    start = match.start()
    end = match.end()
    
    # Buscar el cierre de messages
    bracket_count = 0
    in_messages = False
    for i in range(start, len(content)):
        if content[i] == '[' and 'messages = [' in content[max(0, i-15):i+1]:
            in_messages = True
            bracket_count = 1
            continue
        if in_messages:
            if content[i] == '[':
                bracket_count += 1
            elif content[i] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end = i + 1
                    break
    
    new_content = content[:start] + new_prompt + content[end:]
    
    # Guardar el archivo
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Archivo actualizado correctamente")
    print(f"Reemplazado desde posición {start} hasta {end}")
else:
    print("❌ No se encontró el patrón de la función")
    print("Buscando función manualmente...")
    idx = content.find('def _extract_payload_with_ai')
    if idx != -1:
        print(f"Función encontrada en posición {idx}")
        print("Contexto:", content[idx:idx+200])
