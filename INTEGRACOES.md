# 🔗 PSI API - INTEGRAÇÕES COMPLETAS

## Como Integrar PSI API em 5 Minutos

A PSI API funciona com **QUALQUER** plataforma de chatbot. Basta fazer uma requisição HTTP POST e usar o resultado para direcionar a conversa.

---

## 🚀 INTEGRAÇÃO UNIVERSAL

### Requisição Base:
```http
POST https://psi-api-ve66.onrender.com/detect
Content-Type: application/json
X-API-Key: SUA_API_KEY

{
  "text": "mensagem do cliente"
}
```

### Resposta:
```json
{
  "profile": "INVESTIDOR_EARLY_BIRD",
  "confidence": 0.75,
  "keywords_found": ["vgv", "roi"],
  "suggested_approach": "Foco em números, VGV, potencial de valorização",
  "example_response": "VGV R$120M, 35% vendido. Desconto 12% à vista.",
  "credits_remaining": 1999
}
```

---

## 📱 PLATAFORMA 1: MANYCHAT

### Setup (2 minutos):
1. **Criar Action** → Add Action → External Request
2. **URL:** `https://psi-api-ve66.onrender.com/detect`
3. **Method:** POST
4. **Headers:** 
   - `Content-Type: application/json`
   - `X-API-Key: SUA_API_KEY`
5. **Body:**
```json
{
  "text": "{{last_user_freeform_input}}"
}
```

### Usar Resultado:
```javascript
// Custom Field: psi_profile
{{psi_profile}} = {{external_request.profile}}

// Conditional Logic
IF {{psi_profile}} contains "INVESTIDOR"
  → Redirect to "Flow Investidor"
ELSE IF {{psi_profile}} contains "FAMILIA" 
  → Redirect to "Flow Família"
```

### Flow Exemplo:
```
1. User Message: "Qual o ROI esperado?"
2. PSI Detection Action
3. IF profile = INVESTIDOR → Send: "VGV R$120M, yield 8.5% a.a."
4. IF profile = FAMILIA → Send: "Apartamentos familiares com área de lazer"
```

---

## 🤖 PLATAFORMA 2: DIALOGFLOW

### Setup no Console:
1. **Create Webhook** → Fulfillment → Enable Webhook
2. **URL:** `https://psi-api-ve66.onrender.com/detect` (não usar diretamente)
3. **Create Cloud Function** (recomendado):

```javascript
const functions = require('firebase-functions');
const {WebhookClient} = require('dialogflow-fulfillment');
const axios = require('axios');

exports.dialogflowFirebaseFulfillment = functions.https.onRequest(async (request, response) => {
  const agent = new WebhookClient({ request, response });
  
  async function detectProfile(agent) {
    const userMessage = agent.query;
    
    try {
      const psiResponse = await axios.post('https://psi-api-ve66.onrender.com/detect', {
        text: userMessage
      }, {
        headers: {
          'X-API-Key': 'SUA_API_KEY',
          'Content-Type': 'application/json'
        }
      });
      
      const profile = psiResponse.data.profile;
      const approach = psiResponse.data.suggested_approach;
      const example = psiResponse.data.example_response;
      
      // Set context for next interactions
      agent.setContext({
        name: 'profile-detected',
        lifespan: 10,
        parameters: { profile, approach }
      });
      
      // Resposta personalizada por perfil
      if (profile.includes('INVESTIDOR')) {
        agent.add(`💰 **Oportunidade de Investimento**\n\n${example}\n\nQuer saber mais sobre números e rentabilidade?`);
      } else if (profile.includes('FAMILIA')) {
        agent.add(`🏡 **Perfeito para sua Família**\n\n${example}\n\nGostaria de conhecer as áreas de lazer?`);
      } else {
        agent.add(`${example}\n\nEm que posso ajudar especificamente?`);
      }
      
    } catch (error) {
      agent.add('Como posso ajudar com informações sobre o lançamento?');
    }
  }
  
  // Map intents
  let intentMap = new Map();
  intentMap.set('Default Welcome Intent', detectProfile);
  intentMap.set('detect.profile', detectProfile);
  
  agent.handleRequest(intentMap);
});
```

### Intent Setup:
```
Intent: detect.profile
Training Phrases:
- "Qual o ROI desse lançamento?"
- "Tem escola boa perto?"
- "Aceita proposta à vista?"

Action: profile.detection
Webhook: ENABLED
```

---

## ⚡ PLATAFORMA 3: TYPEBOT

### Flow Visual:
```
1. [Text Input] → Capture message
2. [HTTP Request] → PSI API Call
3. [Conditional Logic] → Route by profile
4. [Text Bubble] → Personalized response
```

### HTTP Request Block:
```yaml
URL: https://psi-api-ve66.onrender.com/detect
Method: POST
Headers:
  X-API-Key: SUA_API_KEY
  Content-Type: application/json
Body:
  {
    "text": "{{user_message}}"
  }
Save Response To: {{psi_result}}
```

### Conditional Logic:
```yaml
IF {{psi_result.profile}} contains "INVESTIDOR"
  → Text: "💰 {{psi_result.example_response}} \n\nQuer ver a planilha de investimento?"
  
ELSE IF {{psi_result.profile}} contains "FAMILIA"
  → Text: "👨‍👩‍👧‍👦 {{psi_result.example_response}} \n\nGostaria de agendar uma visita?"
  
ELSE
  → Text: "{{psi_result.example_response}}"
```

---

## 🔗 PLATAFORMA 4: MAKE.COM (ex-Integromat)

### Cenário Setup:
1. **Webhook Trigger** → Receive data from chatbot
2. **HTTP Request** → Call PSI API
3. **Router** → Route by profile  
4. **Webhook Response** → Send back to chatbot

### HTTP Module Config:
```yaml
URL: https://psi-api-ve66.onrender.com/detect
Method: POST
Headers:
  X-API-Key: SUA_API_KEY
  Content-Type: application/json
Body Type: Raw
Body: 
  {
    "text": "{{trigger.user_message}}"
  }
```

### Router Logic:
```yaml
Route 1: {{http.profile}} contains "INVESTIDOR"
  → Response: {
      "profile": "investidor",
      "message": "{{http.example_response}}",
      "next_flow": "investidor_details"
    }

Route 2: {{http.profile}} contains "FAMILIA"  
  → Response: {
      "profile": "familia", 
      "message": "{{http.example_response}}",
      "next_flow": "family_tour"
    }
```

---

## 📧 PLATAFORMA 5: WHATSAPP BUSINESS API

### Evolution API Integration:
```javascript
const axios = require('axios');

async function handleMessage(message, contact) {
  try {
    // Detectar perfil com PSI
    const psiResponse = await axios.post('https://psi-api-ve66.onrender.com/detect', {
      text: message.body
    }, {
      headers: {
        'X-API-Key': process.env.PSI_API_KEY,
        'Content-Type': 'application/json'
      }
    });
    
    const { profile, example_response, confidence } = psiResponse.data;
    
    // Salvar perfil no banco para próximas interações
    await saveContactProfile(contact, profile, confidence);
    
    // Resposta personalizada
    let response = '';
    let buttons = [];
    
    switch (profile) {
      case 'INVESTIDOR_EARLY_BIRD':
        response = `💰 *Oportunidade Exclusiva*\n\n${example_response}`;
        buttons = [
          { id: 'planilha', title: '📊 Ver Planilha' },
          { id: 'contato_corretor', title: '👨‍💼 Falar com Corretor' }
        ];
        break;
        
      case 'FAMILIA_PLANEJADORA':
        response = `🏡 *Perfeito para sua Família*\n\n${example_response}`;
        buttons = [
          { id: 'agendar_visita', title: '📅 Agendar Visita' },
          { id: 'ver_planta', title: '🏗️ Ver Plantas' }
        ];
        break;
        
      case 'ESPECULADOR_RAPIDO':
        response = `⚡ *Oportunidade Única*\n\n${example_response}`;
        buttons = [
          { id: 'proposta_urgente', title: '💸 Fazer Proposta' },
          { id: 'condicoes', title: '📋 Condições Especiais' }
        ];
        break;
        
      default:
        response = example_response;
        buttons = [
          { id: 'mais_info', title: 'ℹ️ Mais Informações' },
          { id: 'contato', title: '📞 Contato' }
        ];
    }
    
    // Enviar resposta com botões
    await sendWhatsAppMessage(contact, response, buttons);
    
  } catch (error) {
    console.error('Erro PSI Detection:', error);
    await sendWhatsAppMessage(contact, 'Como posso ajudar com o lançamento?');
  }
}

async function sendWhatsAppMessage(contact, text, buttons = []) {
  const payload = {
    number: contact,
    text: text
  };
  
  if (buttons.length > 0) {
    payload.buttons = buttons;
  }
  
  await axios.post(`${process.env.EVOLUTION_API_URL}/message/sendText`, payload, {
    headers: {
      'apikey': process.env.EVOLUTION_API_KEY
    }
  });
}
```

---

## 🛠️ INTEGRAÇÕES AVANÇADAS

### A. Webhook Callback (Recomendado para Alto Volume)

```javascript
// Na requisição PSI, incluir webhook_url
const psiRequest = {
  text: userMessage,
  webhook_url: "https://seu-sistema.com/psi-callback"
};

// Seu endpoint recebe o resultado
app.post('/psi-callback', (req, res) => {
  const { profile, confidence, suggested_approach } = req.body;
  
  // Processar resultado assincronamente
  processProfileResult(userId, profile, confidence);
  
  res.status(200).send('OK');
});
```

### B. Caching para Performance

```javascript
const NodeCache = require('node-cache');
const profileCache = new NodeCache({ stdTTL: 3600 }); // 1 hora

async function getProfileCached(message, userId) {
  const cacheKey = `profile_${userId}_${message.substring(0, 50)}`;
  
  let result = profileCache.get(cacheKey);
  if (!result) {
    result = await callPSIAPI(message);
    profileCache.set(cacheKey, result);
  }
  
  return result;
}
```

### C. Fallback e Error Handling

```javascript
async function robustPSICall(message, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await axios.post('https://psi-api-ve66.onrender.com/detect', {
        text: message
      }, {
        headers: { 'X-API-Key': API_KEY },
        timeout: 5000
      });
      
      return response.data;
      
    } catch (error) {
      if (i === retries - 1) {
        // Último retry - usar resposta padrão
        return {
          profile: 'INDEFINIDO',
          confidence: 0,
          example_response: 'Como posso ajudar com o lançamento?'
        };
      }
      
      // Wait before retry
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

---

## ⚠️ BOAS PRÁTICAS

### 1. **Rate Limiting**
- Máximo 10 requests/segundo por API key
- Use cache para mensagens similares
- Implemente retry com backoff exponencial

### 2. **Monitoramento**
```javascript
// Track API usage
console.log(`PSI Detection - User: ${userId}, Profile: ${profile}, Confidence: ${confidence}, Credits: ${credits_remaining}`);

// Alert quando créditos baixos
if (credits_remaining < 100) {
  sendAlert('PSI API credits running low');
}
```

### 3. **Segurança**
```javascript
// NUNCA exponha sua API key no frontend
const API_KEY = process.env.PSI_API_KEY; // Usar variáveis de ambiente

// Validar entrada
function sanitizeMessage(message) {
  return message.trim().substring(0, 500); // Limitar tamanho
}
```

### 4. **Testing**
```javascript
// Test com diferentes perfis
const testCases = [
  { message: "Qual o VGV?", expected: "INVESTIDOR" },
  { message: "Tem escola perto?", expected: "FAMILIA" },
  { message: "Aceita à vista?", expected: "ESPECULADOR" }
];

for (const test of testCases) {
  const result = await callPSIAPI(test.message);
  console.log(`${test.message} → ${result.profile} (${result.confidence})`);
}
```

---

## 📞 SUPORTE

**Problemas de integração?**
- Email: api@psi.com.br
- WhatsApp: [Seu número]
- Documentação: https://psi-api-ve66.onrender.com/docs

**Status da API:**
- Health Check: https://psi-api-ve66.onrender.com/health
- Uptime: >99.9%
- Response Time: <300ms

---

*PSI API - Transformando chatbots em especialistas desde 2025* 🚀