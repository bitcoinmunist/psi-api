# PSI API - Detecção de Perfis para Chatbots

API que detecta o perfil do cliente em 0.3 segundos para chatbots imobiliários.

## Demo
https://psi-api.onrender.com/test

## Como usar

```bash
curl -X POST https://psi-api.onrender.com/detect \
  -H "X-API-Key: TRIAL_PSI_7DIAS" \
  -H "Content-Type: application/json" \
  -d '{"text": "Qual o ROI desse lançamento?"}'
```

## Resposta
```json
{
  "profile": "INVESTIDOR_EARLY_BIRD",
  "confidence": 0.4,
  "keywords_found": ["roi"],
  "suggested_approach": "Foco em números e valorização",
  "example_response": "VGV R$120M, yield 8.5% a.a."
}
```

## Perfis detectados
- INVESTIDOR_EARLY_BIRD
- FAMILIA_PLANEJADORA
- ESPECULADOR_RAPIDO
- ESTRANGEIRO_GOLDEN_VISA
- PRIMEIRA_COMPRA

## Preços
- Trial: 100 detecções grátis
- Starter: R$ 197 = 2.000 detecções
- Pro: R$ 497 = 6.000 detecções

Contato: api@psi.com.br