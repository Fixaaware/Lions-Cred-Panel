# ============================================================
#  Lions Cred  |  Script de Inicialização
#  Execute: python start.py
# ============================================================

import subprocess
import sys

print("=" * 50)
print("  Lions Cred — Iniciando sistema...")
print("=" * 50)

# Instala dependências
print("\n[1/2] Verificando dependências...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"])
print("      ✔ Dependências OK")

# Inicia o servidor
print("\n[2/2] Iniciando servidor Flask...")
print("\n  Acesse: http://localhost:5000\n")
subprocess.run([sys.executable, "app.py"])
