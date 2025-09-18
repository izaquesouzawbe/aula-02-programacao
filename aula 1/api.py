from flask import Flask, request, jsonify

app = Flask(__name__)

IDADE_ADULTA = 18

@app.route('/verificar_idade', methods=['POST'])
def verificar_idade():    
    data = request.get_json()

    nome = data.get('nome')
    idade = data.get('idade')

    idade_int = int(idade)

    is_adulto = (idade_int >= IDADE_ADULTA)

    return jsonify({
        "nome": str(nome).strip(),
        "idade": idade_int,
        "mensagem": "Maior de idade" if is_adulto else "Menor de idade"
    }), 200


if __name__ == '__main__':
    # roda localmente em http://127.0.0.1:5000
    app.run(debug=True)