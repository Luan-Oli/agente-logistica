import os
from imap_tools import MailBox, AND

# --- ÁREA DE CONFIGURAÇÃO (EDITE AQUI) ---
# Coloque o e-mail que você criou para o robô
EMAIL_USER = "logistica.senai.bot@gmail.com" 

# Coloque a SENHA DE APP de 16 letras (NÃO é a senha normal do Gmail)
# Exemplo: 'abcd efgh ijkl mnop'
EMAIL_PASS = "tizb pefo dfav kqut" 

PASTA_DESTINO = "dados_atualizados.xlsx"

def baixar_anexo_email():
    print(f"🤖 Conectando ao Gmail de: {EMAIL_USER}...")
    try:
        # Tenta conectar
        with MailBox('imap.gmail.com').login(EMAIL_USER, EMAIL_PASS) as mailbox:
            
            # Busca emails com o assunto EXATO "Relatorio Logistica"
            # seen=False busca apenas os NÃO LIDOS. Se quiser ler todos, tire o seen=False
            criterios = AND(subject="Relatorio Logistica")
            
            # Pega o último email encontrado
            for msg in mailbox.fetch(criterios, reverse=True, limit=1):
                print(f"📧 E-mail encontrado! Assunto: {msg.subject}")
                
                encontrou_excel = False
                for att in msg.attachments:
                    if att.filename.endswith('.xlsx'):
                        with open(PASTA_DESTINO, 'wb') as f:
                            f.write(att.payload)
                        print(f"✅ Arquivo salvo com sucesso: {PASTA_DESTINO}")
                        encontrou_excel = True
                        return True
                
                if not encontrou_excel:
                    print("⚠️ O e-mail foi achado, mas não tinha anexo .xlsx.")
            
            print("📭 Nenhum e-mail com assunto 'Relatorio Logistica' encontrado.")
            return False
            
    except Exception as e:
        print(f"❌ Erro de Conexão: {e}")
        print("DICA: Verifique se a 'Senha de App' está correta e se o IMAP está ativado no Gmail.")
        return False

if __name__ == "__main__":
    baixar_anexo_email()
