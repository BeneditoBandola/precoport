from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Painel de Gestão - PDV Pet", page_icon="🐾", layout="wide"
)

st.title("📊 Painel de Oportunidades e Auditoria de Preços")
st.write(
    "Gerencie oportunidades de leitura, pontos extras e auditoria de preços"
    " diretamente por aqui."
)


@st.cache_data
def carregar_dados():
  try:
    df = pd.read_csv("historico_p9_p10.csv", sep=";", encoding="latin1")
    return df
  except FileNotFoundError:
    return None


df = carregar_dados()

if df is None:
  st.error(
      "⚠️ Arquivo 'historico_p9_p10.csv' não encontrado. Por favor, certifique-se"
      " de que o arquivo de dados está na raiz do repositório."
  )
else:
  st.sidebar.header("⚙️ Configurações e Filtros")

  # Filtros de Relatórios
  st.sidebar.subheader("1. Selecione os Blocos do Relatório")
  enviar_sb = st.sidebar.checkbox("📦 Oportunidades Small Bags", value=True)
  enviar_pe = st.sidebar.checkbox(
      "⭐ Oportunidades Ponto Extra", value=True
  )
  enviar_preco = st.sidebar.checkbox(
      "💰 Alertas de Preços Acima do Teto", value=True
  )
  enviar_esp = st.sidebar.checkbox(
      "🔥 Oportunidades Itens Especiais", value=True
  )

  # Configuração de Destinatários
  st.sidebar.subheader("2. Destinatários")
  modo_envio = st.sidebar.radio(
      "Enviar para:",
      ["Somente para o meu e-mail (Teste)", "Para todos os interessados"],
  )
  email_destino_usuario = st.sidebar.text_input(
      "E-mail de Destino / Seu E-mail:", "seu_email@dominio.com"
  )

  # Configurações SMTP
  st.sidebar.subheader("3. Credenciais de E-mail (Remetente)")
  remetente_email = st.sidebar.text_input("Seu E-mail:")
  remetente_senha = st.sidebar.text_input(
      "Senha de App do E-mail:", type="password"
  )

  if st.sidebar.button("🚀 Enviar Relatório por E-mail"):
    if not remetente_email or not remetente_senha:
      st.sidebar.error("Preencha o e-mail remetente e a senha.")
    else:
      try:
        msg = MIMEMultipart()
        msg["From"] = remetente_email
        msg["To"] = email_destino_usuario
        msg["Subject"] = "Relatório Automatizado - PDV Pet"

        corpo_html = (
            "<h3>Relatório Executivo - PDV Pet</h3><p>Dados processados via"
            " painel Streamlit.</p>"
        )
        msg.attach(MIMEText(corpo_html, "html"))

        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(remetente_email, remetente_senha)
        servidor.sendmail(msg["From"], msg["To"], msg.as_string())
        servidor.quit()

        st.success(f"✅ E-mail enviado com sucesso para **{msg['To']}**!")
      except Exception as e:
        st.error(f"❌ Erro ao enviar: {e}")

  st.subheader("👁️ Visualização dos Dados Carregados")
  st.dataframe(df.head(100))
