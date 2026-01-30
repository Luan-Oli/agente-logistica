import os
from imap_tools import MailBox, AND

# --- CONFIGURAÇÃO DIRETA (Preencha aqui!) ---
# Coloque o seu email do robô entre as aspas
EMAIL_USER = "logistica.senai.bot@gmail.com" 

# Coloque a SENHA DE APP (aquela de 16 letras) entre as aspas
# NÃO USE A SENHA NORMAL DO GMAIL!
EMAIL_PASS = "tizb pefo dfav kqut" 

PASTA_DESTINO = "dados_atualizados.xlsx"

def baixar_anexo_email():
    print(f"🤖 Conectando ao Gmail: {EMAIL_USER}...")
    try:
        with MailBox('imap.gmail.com').login(EMAIL_USER, EMAIL_PASS) as mailbox:
            
            # Busca emails com assunto exato "Relatorio Logistica"
            criterios = AND(subject="Relatorio Logistica")
            
            # Pega o último email encontrado
            for msg in mailbox.fetch(criterios, reverse=True, limit=1):
                print(f"📧 E-mail encontrado! Assunto: {msg.subject}")
                
                for att in msg.attachments:
                    if att.filename.endswith('.xlsx'):
                        with open(PASTA_DESTINO, 'wb') as f:
                            f.write(att.payload)
                        print(f"✅ Arquivo salvo: {PASTA_DESTINO}")
                        return True
            
            print("⚠️ E-mail encontrado, mas sem anexo Excel (.xlsx).")
            return False
            
    except Exception as e:
        print(f"❌ Erro de Conexão: {e}")
        return False

if __name__ == "__main__":
    sucesso = baixar_anexo_email()
    if not sucesso:
        exit(1) # Avisa o GitHub que falhou
