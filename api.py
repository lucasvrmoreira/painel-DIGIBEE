import os
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# O token deve vir de uma variável de ambiente no Render (não deixe exposto no código!)
TOKEN_SECRETO = os.environ.get("DIGIBEE_API_TOKEN", "um_token_padrao_para_testes")

# Em memória (substitua por banco de dados futuramente)
erros_logs = []

@app.route('/webhook-erro', methods=['POST'])
def receber_erro():
    # 1. Tenta pegar do Header PRIMEIRO
    token_recebido = request.headers.get('X-Digibee-Token')
    
    # 2. Se não achar, tenta na Query String
    if not token_recebido:
        token_recebido = request.args.get('X-Digibee-Token')
    
    if token_recebido != TOKEN_SECRETO:
        return jsonify({"erro": "Acesso negado"}), 403
    
    if not request.is_json:
        return jsonify({"erro": "Formato inválido"}), 400
    
    dados = request.json
    erros_logs.insert(0, dados)
    
    print(f"✅ Erro recebido: {dados.get('pipeline_name')}")
    
    return jsonify({"status": "sucesso"}), 200

@app.route('/listar-erros', methods=['GET'])
def listar():
    return jsonify(erros_logs)





# Nova rota para servir o painel
@app.route('/')
def index():
    return render_template('index.html')

# ... mantenha suas outras rotas abaixo ...

if __name__ == '__main__':
    # O Render define a porta via variável de ambiente, por isso usamos int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))