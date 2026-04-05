import sys
import os

# Adaptador para permitir a invocação do root direto do sistema de janelas do usuário para este standalone tester.
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core.security import encrypt_sensitive_data, decrypt_sensitive_data
from app.core.config import settings

def main():
    print(f"\n=========================================================")
    print(f"[!] TESTE ISOLADO: MOTOR CRIPTOGRÁFICO AES-GCM-256")
    print(f"=========================================================\n")
    print(f"[*] VALIDAÇÃO DE CHAVE: A chave foi lida do `.env` com Pydantic com sucesso!")
    print(f"[*] HASH ENCONTRADO: {settings.ENCRYPTION_KEY[:8]}.......................{settings.ENCRYPTION_KEY[-8:]}\n")
    
    # Inciando fluxo AES
    texto_original = "Teste de Segurança Brasília"
    print(f"[>] Etapa 1 - Target Data: '{texto_original}'")
    
    try:
        texto_cifrado = encrypt_sensitive_data(texto_original)
        print(f"[>] Etapa 2 - Cifragem Concluída (Estado Banco de Dados): {texto_cifrado[:50]}...")
        print(f"    - Carga Gerada: {len(texto_cifrado)} bytes do algoritmo\n")
        
        texto_decifrado = decrypt_sensitive_data(texto_cifrado)
        print(f"[>] Etapa 3 - Decifração (Lido na Memória RAM Web): '{texto_decifrado}'\n")
        
        if texto_original == texto_decifrado:
             print(f"=========================================================")
             print("[✔] ESTADO DO TESTE: SUCESSO VERDE (PASS). ")
             print("A criptografia In/Out acoplou os Noncers aleatórios e descriptografou sem corromper nenhuma string.")
             print(f"=========================================================\n")
        else:
             print("[X] FALHA CRÍTICA. Os textos decodificados não representam o bit original.")
             
    except Exception as e:
        print(f"\n[X] Ocorreu uma interrupção da thread durante manipulação dos algoritmos: {e}")

if __name__ == "__main__":
    main()
