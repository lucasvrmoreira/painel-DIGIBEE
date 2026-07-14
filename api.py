import os
import json
from flask import Flask, request, jsonify, render_template
from anthropic import Anthropic

app = Flask(__name__)

TOKEN_SECRETO = os.environ.get("DIGIBEE_API_TOKEN", "Saopaulo@@2026")
CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

print(f"🔑 Chave configurada ao iniciar? {bool(CLAUDE_API_KEY)}")

erros_logs = []
client = Anthropic()

def analisar_erro_com_claude(erro_mensagem, pipeline_name):
    """Usa Claude pra analisar o erro e sugerir solução"""
    try:
        print(f"🔑 DEBUG: Chave existe? {bool(CLAUDE_API_KEY)}")
        
        if not CLAUDE_API_KEY:
            print("❌ ERRO: ANTHROPIC_API_KEY NÃO CONFIGURADA!")
            return {
                "causa_provavel": "⚠️ Chave da API não configurada",
                "acao_recomendada": "Configure ANTHROPIC_API_KEY no Render",
                "severidade": "alta"
            }
        
        print(f"✅ Chamando Claude API...")
        
        message = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"""Você é especialista em Digibee e Protheus.

Pipeline: {pipeline_name}
Erro: {erro_mensagem}

Responda APENAS em JSON:
{{
    "causa_provavel": "...",
    "acao_recomendada": "...",
    "severidade": "alta/media/baixa"
}}"""
                }
            ]
        )
        
        resposta = message.content[0].text
        print(f"✅ Claude respondeu: {resposta[:100]}...")
        return json.loads(resposta)
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        return {
            "causa_provavel": "Erro ao parsear",
            "acao_recomendada": "Verifique logs",
            "severidade": "media"
        }
    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {str(e)}")
        return {
            "causa_provavel": f"Erro: {type(e).__name__}",
            "acao_recomendada": str(e),
            "severidade": "media"
        }

@app.route('/webhook-erro', methods=['POST'])
def receber_erro():
    print("📥 POST recebido em /webhook-erro")
    
    token_recebido = request.headers.get('X-Digibee-Token')
    if not token_recebido:
        token_recebido = request.args.get('X-Digibee-Token')
    
    print(f"🔑 Token recebido: {token_recebido}")
    
    if token_recebido != TOKEN_SECRETO:
        print(f"❌ Token inválido!")
        return jsonify({"erro": "Acesso negado"}), 403
    
    if not request.is_json:
        return jsonify({"erro": "Formato inválido"}), 400
    
    dados = request.json
    erro_msg = dados.get('erro_mensagem', 'Erro desconhecido')
    pipeline = dados.get('pipeline_name', 'N/A')
    
    print(f"🔍 Analisando erro: {pipeline} - {erro_msg[:50]}...")
    analise = analisar_erro_com_claude(erro_msg, pipeline)
    
    dados['causa_provavel'] = analise.get('causa_provavel')
    dados['acao_recomendada'] = analise.get('acao_recomendada')
    dados['severidade'] = analise.get('severidade')
    
    erros_logs.insert(0, dados)
    print(f"✅ Erro salvo! Total: {len(erros_logs)}")
    
    return jsonify({"status": "sucesso"}), 200

@app.route('/listar-erros', methods=['GET'])
def listar():
    return jsonify(erros_logs)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))