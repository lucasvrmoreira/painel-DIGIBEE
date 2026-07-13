import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# O token deve vir de uma variável de ambiente no Render (não deixe exposto no código!)
TOKEN_SECRETO = os.environ.get("DIGIBEE_API_TOKEN", "um_token_padrao_para_testes")

# Em memória (substitua por banco de dados futuramente)
erros_logs = []

@app.route('/webhook-erro', methods=['POST'])
def receber_erro():
    # 1. Segurança: Verifica se o token está no Header
    token_recebido = request.headers.get('X-Digibee-Token')
    if token_recebido != TOKEN_SECRETO:
        return jsonify({"erro": "Acesso negado"}), 403
    
    # 2. Validação básica: Garante que é JSON
    if not request.is_json:
        return jsonify({"erro": "Formato inválido"}), 400
    
    dados = request.json
    
    # 3. Adiciona o erro na lista
    erros_logs.insert(0, dados)
    
    print(f"Erro recebido do pipeline {dados.get('pipeline_name')}: {dados.get('causa_provavel')}")
    
    return jsonify({"status": "sucesso"}), 200

@app.route('/listar-erros', methods=['GET'])
def listar():
    return jsonify(erros_logs)

if __name__ == '__main__':
    # O Render define a porta via variável de ambiente, por isso usamos int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))