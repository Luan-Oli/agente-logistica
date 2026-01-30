import os
from imap_tools import MailBox, AND

# Configurações do GitHub Secrets
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
PASTA_DESTINO = "dados_atualizados.xlsx"

def baixar_anexo_email():
    print("🤖 Conectando ao Gmail...")
    try:
        with MailBox('imap.gmail.com').login(EMAIL_USER, EMAIL_PASS) as mailbox:
            # Busca emails com assunto exato
            criterios = AND(subject="Relatorio Logistica")
            
            for msg in mailbox.fetch(criterios, reverse=True, limit=1):
                print(f"📧 E-mail encontrado: {msg.subject}")
                for att in msg.attachments:
                    if att.filename.endswith('.xlsx'):
                        with open(PASTA_DESTINO, 'wb') as f:
                            f.write(att.payload)
                        print(f"✅ Arquivo salvo: {PASTA_DESTINO}")
                        return True
            print("⚠️ Nenhum anexo .xlsx encontrado no último e-mail.")
            return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    baixar_anexo_email()
