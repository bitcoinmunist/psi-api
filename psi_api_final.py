"""
PSI API - Detecção de Perfis para Chatbots Imobiliários
API as a Service modelo créditos pré-pagos
"""

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import redis
import hashlib
import re
from datetime import datetime
from typing import Optional, List
import json
import asyncio
import httpx

# Configuração
app = FastAPI(
    title="PSI API - Detecção de Perfis",
    version="1.0.0",
    description="API que detecta o perfil do cliente em 0.3 segundos"
)

# CORS para permitir chamadas do browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis connection (usar Redis Cloud grátis em produção)
try:
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        decode_responses=True
    )
    redis_client.ping()
except:
    # Fallback para desenvolvimento sem Redis
    redis_client = None
    print("⚠️ Redis não disponível - usando memória local")
    LOCAL_STORAGE = {}

# Models
class DetectRequest(BaseModel):
    text: str
    context: str = "lancamento_sp"
    webhook_url: Optional[str] = None

class DetectResponse(BaseModel):
    profile: str
    confidence: float
    keywords_found: List[str]
    suggested_approach: str
    example_response: str
    credits_remaining: int

class CheckoutRequest(BaseModel):
    plan: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

# Perfis Ultra-Específicos para Lançamentos SP
PROFILES_LANCAMENTO = {
    "INVESTIDOR_EARLY_BIRD": {
        "patterns": [
            r"vgv|pre[-\s]?lan[çc]amento|tabela|permuta",
            r"rentabiliza|yield|retorno|roi|valoriza",
            r"desconto|entrada|parcela|financiamento",
            r"metragem|m2|metros|area"
        ],
        "approach": "Foco em números, VGV, potencial de valorização e condições especiais",
        "example": "VGV R$120M, 35% vendido. Desconto 12% à vista. Yield 8.5% a.a. Últimas unidades lote atual."
    },
    "FAMILIA_PLANEJADORA": {
        "patterns": [
            r"escola|filho|crian[çc]a|pet|cachorro|gato",
            r"planta|quarto|suite|varanda|sacada",
            r"lazer|piscina|playground|churrasqueira",
            r"entrega|obra|acabamento|condominio"
        ],
        "approach": "Qualidade de vida, segurança, futuro da família e comodidades",
        "example": "4 aptos/andar, máxima privacidade. Graded School 400m. Lazer completo entregue. Pet place exclusivo."
    },
    "ESPECULADOR_RAPIDO": {
        "patterns": [
            r"revend|distrato|repasse|flip|especula",
            r"vista|a vista|avista|desconto|negocia",
            r"rapido|urgente|hoje|agora|já",
            r"oportunidade|chance|imperdivel"
        ],
        "approach": "Oportunidade única, ganho rápido e decisão imediata",
        "example": "Distrato R$50k abaixo da tabela. Próximo lote +18%. Precisa decisão hoje. Repasse permitido."
    },
    "ESTRANGEIRO_GOLDEN_VISA": {
        "patterns": [
            r"golden|visa|investment|euro|dollar|usd",
            r"rental|rent|guarantee|yield|return",
            r"management|administra|property",
            r"foreign|estrangeiro|international"
        ],
        "approach": "Processo simplificado, garantias e retorno em moeda forte",
        "example": "Golden Visa qualified. 6% guaranteed yield. Full management. USD payment accepted."
    },
    "PRIMEIRA_COMPRA": {
        "patterns": [
            r"primeira|primeiro|nunca comprei|inexperiente",
            r"duvida|pergunta|como funciona|explica",
            r"medo|receio|seguro|garantia",
            r"subsidio|minha casa|fgts|caixa"
        ],
        "approach": "Educativo, segurança, passo a passo simplificado",
        "example": "Entrada facilitada em 24x. FGTS aceito. Assessoria completa gratruita. Garantia de entrega."
    }
}

def detect_profile_advanced(text: str) -> tuple:
    """
    Detecção avançada com scoring e patterns regex
    Retorna: (profile_name, confidence, keywords_found)
    """
    text_lower = text.lower()
    scores = {}
    
    for profile_name, profile_data in PROFILES_LANCAMENTO.items():
        score = 0
        keywords_found = []
        
        for pattern in profile_data["patterns"]:
            matches = re.findall(pattern, text_lower)
            if matches:
                score += len(matches) * 10
                keywords_found.extend(matches)
        
        # Bonus points para combinações
        if len(keywords_found) > 2:
            score += 20
        
        scores[profile_name] = (score, list(set(keywords_found))[:5])
    
    # Pegar perfil com maior score
    best_profile = max(scores.items(), key=lambda x: x[1][0])
    profile_name = best_profile[0]
    score, keywords = best_profile[1]
    
    # Se nenhum match forte, retorna INDEFINIDO
    if score < 10:
        return "INDEFINIDO", 0.0, []
    
    # Calcular confiança (0.3 a 0.95)
    confidence = min(0.95, 0.3 + (score / 100))
    
    return profile_name, confidence, keywords

def get_credits(api_key: str) -> int:
    """Retorna créditos disponíveis"""
    if redis_client:
        credits = redis_client.hget(f"key:{api_key}", "credits")
        return int(credits) if credits else 0
    else:
        return LOCAL_STORAGE.get(api_key, {}).get("credits", 0)

def use_credit(api_key: str) -> bool:
    """Consome 1 crédito se disponível"""
    if redis_client:
        credits = redis_client.hget(f"key:{api_key}", "credits")
        if credits and int(credits) > 0:
            redis_client.hincrby(f"key:{api_key}", "credits", -1)
            redis_client.hincrby(f"key:{api_key}", "total_used", 1)
            return True
        return False
    else:
        if api_key in LOCAL_STORAGE and LOCAL_STORAGE[api_key]["credits"] > 0:
            LOCAL_STORAGE[api_key]["credits"] -= 1
            LOCAL_STORAGE[api_key]["total_used"] = LOCAL_STORAGE[api_key].get("total_used", 0) + 1
            return True
        return False

def add_credits(api_key: str, amount: int, email: str = ""):
    """Adiciona créditos a uma API key"""
    if redis_client:
        redis_client.hset(f"key:{api_key}", mapping={
            "credits": amount,
            "email": email,
            "created": str(datetime.now()),
            "total_used": 0
        })
    else:
        LOCAL_STORAGE[api_key] = {
            "credits": amount,
            "email": email,
            "created": str(datetime.now()),
            "total_used": 0
        }

async def send_webhook(url: str, data: dict):
    """Envia resultado para webhook do cliente (async)"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(url, json=data, timeout=5.0)
    except:
        pass  # Falha silenciosa em webhooks

# API Endpoints

@app.get("/")
async def root():
    """Landing page da API"""
    return {
        "name": "PSI API",
        "description": "Detecção de perfis para chatbots imobiliários",
        "version": "1.0.0",
        "documentation": "/docs",
        "pricing": {
            "trial": "100 detecções grátis",
            "starter": "R$ 197 = 2.000 detecções",
            "pro": "R$ 497 = 6.000 detecções"
        },
        "contact": "api@psi.com.br"
    }

@app.post("/detect", response_model=DetectResponse)
async def detect(request: DetectRequest, x_api_key: str = Header(None)):
    """
    Endpoint principal - Detecta perfil do cliente
    
    Headers:
        X-API-Key: Sua chave de API
    
    Body:
        text: Mensagem do cliente
        context: Contexto (default: lancamento_sp)
        webhook_url: URL para callback (opcional)
    """
    
    # Validar API key
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API Key required. Get one at psi.com.br"
        )
    
    # API key trial para teste
    if x_api_key == "TRIAL_PSI_7DIAS":
        # Trial tem limite mas não consome créditos do Redis
        pass
    else:
        # Verificar e consumir crédito
        if not use_credit(x_api_key):
            raise HTTPException(
                status_code=402,
                detail="No credits. Buy at psi.com.br/creditos"
            )
    
    # Detectar perfil
    profile, confidence, keywords = detect_profile_advanced(request.text)
    
    # Buscar dados do perfil
    profile_data = PROFILES_LANCAMENTO.get(
        profile,
        {
            "approach": "Abordagem padrão para atendimento",
            "example": "Posso ajudar com informações sobre o lançamento."
        }
    )
    
    # Créditos restantes
    remaining = get_credits(x_api_key) if x_api_key != "TRIAL_PSI_7DIAS" else 99
    
    # Preparar resposta
    response = DetectResponse(
        profile=profile,
        confidence=round(confidence, 2),
        keywords_found=keywords,
        suggested_approach=profile_data["approach"],
        example_response=profile_data["example"],
        credits_remaining=remaining
    )
    
    # Log para analytics (async, não bloqueia)
    if redis_client:
        redis_client.hincrby("stats:daily", datetime.now().strftime("%Y-%m-%d"), 1)
        redis_client.hincrby("stats:profiles", profile, 1)
    
    # Webhook callback se fornecido (async, não bloqueia)
    if request.webhook_url:
        asyncio.create_task(send_webhook(request.webhook_url, response.dict()))
    
    return response

@app.post("/api/generate-key")
async def generate_api_key(email: str, credits: int = 100, package: str = "manual"):
    """
    Gera nova API key (endpoint admin, proteger em produção)
    Query params: ?email=teste@test.com&credits=100&package=starter
    """
    # Gerar chave única
    raw = f"{email}{datetime.now()}{credits}"
    api_key = "psi_" + hashlib.sha256(raw.encode()).hexdigest()[:28]
    
    # Adicionar créditos
    add_credits(api_key, credits, email)
    
    return {
        "api_key": api_key,
        "credits": credits,
        "email": email,
        "package": package,
        "created": datetime.now().isoformat()
    }

@app.get("/stats")
async def get_stats(key: str = None, x_api_key: str = Header(None)):
    """
    Retorna estatísticas de uso da API key
    Aceita key via query param ou header: /stats?key=API_KEY ou Header X-API-Key
    """
    api_key = key or x_api_key
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key required via ?key= or X-API-Key header")
    
    if redis_client:
        data = redis_client.hgetall(f"key:{api_key}")
        if not data:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {
            "credits_remaining": int(data.get("credits", 0)),
            "total_detections": int(data.get("total_used", 0)),
            "created": data.get("created", ""),
            "email": data.get("email", "")
        }
    else:
        data = LOCAL_STORAGE.get(api_key)
        if not data:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {
            "credits_remaining": data["credits"],
            "total_detections": data["total_used"],
            "created": data["created"],
            "email": data["email"]
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_ok = False
    try:
        if redis_client:
            redis_client.ping()
            redis_ok = True
    except:
        pass
    
    return {
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "redis": "connected" if redis_ok else "using local storage",
        "profiles_available": list(PROFILES_LANCAMENTO.keys())
    }

@app.get("/test")
async def test_detection():
    """
    Página de teste interativa (HTML)
    """
    html = """
    <html>
    <head>
        <title>PSI API - Teste</title>
        <style>
            body { font-family: Arial; max-width: 800px; margin: 0 auto; padding: 20px; }
            input { width: 100%; padding: 10px; margin: 10px 0; }
            button { background: #10b981; color: white; padding: 10px 20px; border: none; cursor: pointer; }
            .result { background: #f3f4f6; padding: 15px; margin-top: 20px; border-radius: 5px; }
            .confidence { font-size: 24px; font-weight: bold; }
        </style>
    </head>
    <body>
        <h1>🎯 PSI API - Teste de Detecção</h1>
        <p>Digite uma mensagem de cliente para detectar o perfil:</p>
        
        <input type="text" id="message" placeholder="Ex: Qual o ROI desse lançamento?" />
        <button onclick="detectProfile()">Detectar Perfil</button>
        
        <div id="result"></div>
        
        <script>
            async function detectProfile() {
                const text = document.getElementById('message').value;
                
                const response = await fetch('/detect', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': 'TRIAL_PSI_7DIAS'
                    },
                    body: JSON.stringify({ text })
                });
                
                const data = await response.json();
                
                document.getElementById('result').innerHTML = `
                    <div class="result">
                        <h3>Perfil Detectado: ${data.profile}</h3>
                        <p class="confidence">Confiança: ${(data.confidence * 100).toFixed(0)}%</p>
                        <p><strong>Palavras-chave:</strong> ${data.keywords_found.join(', ')}</p>
                        <p><strong>Abordagem sugerida:</strong> ${data.suggested_approach}</p>
                        <p><strong>Exemplo de resposta:</strong> ${data.example_response}</p>
                    </div>
                `;
            }
        </script>
        
        <hr style="margin-top: 40px;">
        <p>Exemplos para testar:</p>
        <ul>
            <li>"Qual o VGV do empreendimento e o yield esperado?"</li>
            <li>"Tem escola boa perto? Meus filhos estudam no Graded"</li>
            <li>"Preciso vender rápido, aceita proposta à vista?"</li>
            <li>"I need information about Golden Visa properties"</li>
            <li>"É meu primeiro apartamento, como funciona?"</li>
        </ul>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)

# =================== STRIPE PAYMENT SYSTEM ===================

# Stripe configuration (usar env vars em produção)
STRIPE_PUBLISHABLE_KEY = "pk_test_51234567890"  # Colocar sua chave aqui
STRIPE_SECRET_KEY = "sk_test_51234567890"  # Colocar sua chave secreta aqui
STRIPE_WEBHOOK_SECRET = "whsec_1234567890"  # Webhook secret

# Price IDs do Stripe (criar no dashboard)
STRIPE_PRICES = {
    "starter": "price_starter_197",  # R$ 197 - 2000 créditos
    "pro": "price_pro_497"           # R$ 497 - 6000 créditos
}

@app.get("/pricing")
async def get_pricing():
    """Retorna informações de pricing para a landing page"""
    return {
        "packages": {
            "trial": {
                "name": "Trial",
                "price": 0,
                "credits": 100,
                "description": "100 detecções grátis por 7 dias"
            },
            "starter": {
                "name": "Starter", 
                "price": 197,
                "original_price": 297,
                "credits": 2000,
                "description": "2.000 detecções (~2 meses uso)",
                "stripe_price_id": STRIPE_PRICES.get("starter")
            },
            "pro": {
                "name": "Pro",
                "price": 497, 
                "original_price": 697,
                "credits": 6000,
                "description": "6.000 detecções (~6 meses uso)",
                "stripe_price_id": STRIPE_PRICES.get("pro")
            }
        }
    }

@app.post("/checkout/create-session")
async def create_checkout_session(request: CheckoutRequest):
    """
    Cria sessão de checkout do Stripe
    Body: {"plan": "starter", "success_url": "https://...", "cancel_url": "https://..."}
    """
    
    if request.plan not in STRIPE_PRICES:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {request.plan}")
    
    try:
        # Import stripe here para não dar erro se não estiver instalado
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': STRIPE_PRICES[request.plan],
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.success_url or 'https://psi-api.com/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.cancel_url or 'https://psi-api.com/cancel',
            metadata={
                'plan': request.plan
            }
        )
        
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
        
    except ImportError:
        # Se Stripe não estiver instalado, simular checkout
        return {
            "checkout_url": f"https://checkout.stripe.com/pay/test#{request.plan}",
            "session_id": "cs_test_123",
            "message": "⚠️ Stripe não instalado - checkout simulado"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")

@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """
    Webhook do Stripe para processar pagamentos confirmados
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        # Import stripe here para não dar erro se não estiver instalado
        import stripe
        stripe.api_key = STRIPE_SECRET_KEY
        
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ImportError:
        return {"status": "error", "message": "Stripe não instalado"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Processar evento de pagamento confirmado
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Extrair informações do pagamento
        customer_email = session.get('customer_details', {}).get('email', 'unknown@email.com')
        plan = session.get('metadata', {}).get('plan', 'starter')
        
        # Mapear planos para créditos
        credits_map = {
            'starter': 2000,
            'pro': 6000
        }
        credits = credits_map.get(plan, 2000)
        
        # Gerar API key única
        raw = f"{customer_email}{datetime.now()}{credits}"
        api_key = "psi_" + hashlib.sha256(raw.encode()).hexdigest()[:28]
        
        # Adicionar créditos ao sistema
        add_credits(api_key, credits, customer_email)
        
        # Log do pagamento
        print(f"💰 PAGAMENTO CONFIRMADO:")
        print(f"   Email: {customer_email}")
        print(f"   Plano: {plan}")
        print(f"   Créditos: {credits}")
        print(f"   API Key: {api_key}")
        
        # TODO: Enviar email com API key
        # send_api_key_email(customer_email, api_key, credits)
        
        return {"status": "success", "api_key": api_key}
    
    return {"status": "ignored", "event_type": event['type']}

def send_api_key_email(email: str, api_key: str, credits: int):
    """
    Envia email com API key após pagamento
    TODO: Implementar com SendGrid, Mailgun ou similar
    """
    email_content = f"""
    🎉 Pagamento confirmado! Sua PSI API está pronta.
    
    API KEY: {api_key}
    CRÉDITOS: {credits:,}
    
    Como usar:
    1. Acesse: https://psi-api-ve66.onrender.com/docs
    2. Use o header: X-API-Key: {api_key}
    3. Endpoint: POST /detect
    
    Suporte: api@psi.com.br
    """
    
    print(f"📧 EMAIL para {email}:")
    print(email_content)
    
    # TODO: Implementar envio real
    # import sendgrid
    # sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    # ...

@app.get("/success")
async def payment_success(session_id: str = None):
    """Página de sucesso após pagamento"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pagamento Confirmado - PSI API</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
            .success {{ background: #d1fae5; padding: 20px; border-radius: 10px; margin: 20px auto; max-width: 500px; }}
            .api-key {{ background: #f3f4f6; padding: 15px; border-radius: 5px; font-family: monospace; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="success">
            <h1>🎉 Pagamento Confirmado!</h1>
            <p>Sua PSI API está pronta para uso.</p>
            
            <div class="api-key">
                Session ID: {session_id or 'Processando...'}
            </div>
            
            <p><strong>Próximos passos:</strong></p>
            <ol>
                <li>Verifique seu email com a API key</li>
                <li>Acesse a <a href="/docs">documentação</a></li>
                <li>Integre em 5 minutos</li>
                <li>Triplique suas conversões!</li>
            </ol>
            
            <p>Suporte: <a href="mailto:api@psi.com.br">api@psi.com.br</a></p>
        </div>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)

# Inicialização
if __name__ == "__main__":
    import uvicorn
    
    # Criar API key de teste se não existir
    if not get_credits("TRIAL_PSI_7DIAS"):
        add_credits("TRIAL_PSI_7DIAS", 100, "trial@psi.com.br")
        print("✅ API Key de teste criada: TRIAL_PSI_7DIAS")
    
    print("🚀 PSI API iniciando...")
    print("📝 Documentação: http://localhost:8000/docs")
    print("🧪 Teste: http://localhost:8000/test")
    print("🌐 Acesse: http://127.0.0.1:8000/test")
    
    uvicorn.run(
        "psi_chatbot.psi_api_final:app",  # Import string para reload funcionar
        host="0.0.0.0",
        port=8000,
        reload=False  # Desabilitar reload por enquanto
    )