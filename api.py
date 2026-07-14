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

Responda APENAS em JSON (sem markdown, sem preamble):
{{"causa_provavel": "...", "acao_recomendada": "...", "severidade": "alta/media/baixa"}}"""
                }
            ]
        )
        
        resposta = message.content[0].text.strip()
        print(f"📥 Resposta Claude: {resposta[:200]}")
        
        # Remove markdown se existir
        if "```json" in resposta:
            resposta = resposta.split("```json")[1].split("```")[0].strip()
        elif "```" in resposta:
            resposta = resposta.split("```")[1].split("```")[0].strip()
        
        print(f"🧹 Resposta limpa: {resposta[:200]}")
        resultado = json.loads(resposta)
        print(f"✅ Parse bem-sucedido!")
        return resultado
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Decode Error: {e}")
        print(f"Resposta problemática: {resposta[:300]}")
        
        # Fallback: analisa o erro de forma simples
        if "URL" in erro_mensagem and "invalid" in erro_mensagem:
            return {
                "causa_provavel": "URL do endpoint inválida ou mal configurada",
                "acao_recomendada": "Verifique a configuração de URL do componente",
                "severidade": "alta"
            }
        elif "Timeout" in erro_mensagem:
            return {
                "causa_provavel": "Timeout na requisição (servidor lento)",
                "acao_recomendada": "Aumente timeout ou verifique disponibilidade",
                "severidade": "media"
            }
        elif "Connection" in erro_mensagem:
            return {
                "causa_provavel": "Falha na conexão com o servidor",
                "acao_recomendada": "Verifique conectividade e configuração de rede",
                "severidade": "alta"
            }
        else:
            return {
                "causa_provavel": "Erro detectado - análise disponível",
                "acao_recomendada": f"Verifique: {erro_mensagem[:80]}",
                "severidade": "media"
            }
            
    except Exception as e:
        print(f"❌ Exception: {type(e).__name__}: {e}")
        return {
            "causa_provavel": f"Erro ao analisar ({type(e).__name__})",
            "acao_recomendada": "Verifique os logs do servidor",
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