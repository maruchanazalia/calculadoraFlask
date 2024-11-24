from flask import Flask, render_template, request, jsonify
from lark import Lark, Transformer, v_args, Tree

grammar = """
start: expr
?expr: term
     | expr "+" term   -> suma
     | expr "-" term   -> resta
?term: factor
     | term "*" factor -> multiplicacion
     | term "/" factor -> division
?factor: NUMBER        -> numero
       | "-" factor    -> negativo
       | "(" expr ")"
%import common.WS_INLINE
%import common.CNAME
%import common.NUMBER   // Se asegura que "NUMBER" incluye decimales y números científicos
%ignore WS_INLINE
"""


parser = Lark(grammar, parser='lalr')

@v_args(inline=True)
class CalculateTree(Transformer):
    def suma(self, a, b):
        return float(a) + float(b)

    def resta(self, a, b):
        return float(a) - float(b)

    def multiplicacion(self, a, b):
        print(f"Multiplicación: {a} * {b}")  # Depuración
        return float(a) * float(b)

    def division(self, a, b):
        print(f"División: {a} / {b}")  # Depuración
        if b == 0:
            return "Error: División por cero"
        return float(a) / float(b)

    def numero(self, n):
        print(f"Número: {n}")  # Depuración
        return float(n)

    def negativo(self, n):
        print(f"Negativo: -{n}")  # Depuración
        return -float(n)


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')
@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        expression = request.json['expression']
        tree = parser.parse(expression)
        transformer = CalculateTree()
        result = transformer.transform(tree)

        # Asegurarnos de que el resultado es un número (float o int)
        if isinstance(result, (int, float)):
            result = float(result)  # Convertir a float explícitamente
            return jsonify({
                "result": str(result),  # Convertir el resultado a cadena para JSON
                "success": True
            })
        else:
            print(f"Error: El resultado no es un número válido. Tipo recibido: {type(result)}")
            # Intentamos acceder a la raíz del árbol si es necesario
            if isinstance(result, Tree) and len(result.children) > 0:
                result = result.children[0]  # Extraemos el primer hijo (el valor)
                return jsonify({
                    "result": str(result),
                    "success": True
                })
            return jsonify({
                "error": "El resultado no es un número válido",
                "success": False
            })
    except Exception as e:
        print(f"Error en calculate: {str(e)}")
        return jsonify({
            "error": f"Error al procesar la expresión: {str(e)}",
            "success": False
        })
    
@app.route('/get_tokens', methods=['POST'])
def get_tokens():
    try:
        expression = request.json['expression']
        
        # Analizar los tokens de la expresión
        tokens = []
        for token in parser.lex(expression):
            token_type = "Número entero" if token.type == "NUMBER" else "Operador " + token.type
            tokens.append({"token": token.value, "tipo": token_type})

        return jsonify({
            "tokens": tokens,
            "success": True
        })
    except Exception as e:
        print(f"Error al procesar tokens: {str(e)}")
        return jsonify({
            "error": f"Error al procesar la expresión: {str(e)}",
            "success": False
        })



@app.route('/generate_tree', methods=['POST'])
def generate_tree():
    try:
        expression = request.json['expression']
        tree = parser.parse(expression)
        
        def tree_to_dict(tree):
            if isinstance(tree, Tree):
                return {
                    "name": str(tree.data),
                    "children": [tree_to_dict(child) for child in tree.children]
                }
            return {"name": str(tree)}
        
        tree_dict = tree_to_dict(tree)
        return jsonify({
            "tree": tree_dict,
            "success": True
        })
    except Exception as e:
        print(f"Error en generate_tree: {str(e)}") 
        return jsonify({
            "error": str(e),
            "success": False
        })

if __name__ == '__main__':
    app.run(debug=True)
