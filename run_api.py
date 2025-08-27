#!/usr/bin/env python3
"""
Script simplificado para rodar a PSI API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from psi_api_final import app, add_credits, get_credits
import uvicorn

# Setup inicial
if not get_credits("TRIAL_PSI_7DIAS"):
    add_credits("TRIAL_PSI_7DIAS", 100, "trial@psi.com.br")
    print("✅ API Key de teste criada: TRIAL_PSI_7DIAS")

print("\n" + "="*50)
print("🚀 PSI API - Detecção de Perfis")
print("="*50)
print("\n📍 Acesse no navegador:")
print("   http://127.0.0.1:8000/test")
print("\n📚 Documentação:")
print("   http://127.0.0.1:8000/docs")
print("\n🔑 API Key de teste: TRIAL_PSI_7DIAS")
print("="*50 + "\n")

# Rodar servidor (pega porta do ambiente ou usa 8000)
port = int(os.environ.get("PORT", 8000))
uvicorn.run(app, host="0.0.0.0", port=port)