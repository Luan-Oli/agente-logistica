import os
import pandas as pd
from imap_tools import MailBox, AND
import time

# Configurações
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
PASTA_DESTINO = "dados_atualizados.xlsx" # Nome do arquivo que o App vai ler

def baixar_anexo_email():
    print("🤖 Iniciando verificação de e-mails...")
    
    # Conecta ao Gmail
    try:
        with MailBox('imap.gmail.com').login(EMAIL_USER, EMAIL_PASS) as mailbox:
            
            # CRITÉRIO: Busca emails NÃO LIDOS com o assunto "Relatorio Logistica"
            # Você deve enviar o email com este assunto exato!
            criterios = AND(subject="Relatorio Logistica", seen=False)
            
            emails_encontrados = list(mailbox.fetch(criterios, reverse=True))
            
            if not emails_encontrados:
                print("📭 Nenhum e-mail novo com o assunto 'Relatorio Logistica' encontrado.")
                return False
            
            print(f"📧 Encontrados {len(emails_encontrados)} e-mails novos.")
            
            # Pega o e-mail mais recente
            msg = emails_encontrados[0]
            
            for att in msg.attachments:
                print(f"📎 Analisando anexo: {att.filename}")
                
                if att.filename.endswith('.xlsx'):
                    # Salva o arquivo no disco
                    with open(PASTA_DESTINO, 'wb') as f:
                        f.write(att.payload)
                    print(f"✅ Arquivo salvo com sucesso como '{PASTA_DESTINO}'!")
                    return True
                    
            print("⚠️ E-mail encontrado, mas sem anexo .xlsx válido.")
            return False
            
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        return False

if __name__ == "__main__":
    sucesso = baixar_anexo_email()
    if not sucesso:
        exit(1) # Informa ao GitHub que falhou (opcional)
