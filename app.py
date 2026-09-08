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
    "Gerencie oportunidades de leitura, pontos extras e auditoria de preços diretamente por aqui."
)

EMAILS_PROMOTORES = {
    "MINASSAL LTDA - POCOS DE CALDAS": ["pamelaalmeida5@hotmail.com"],
    "MINASSAL LTDA - SAO JOAO DA BOA VISTA": ["crbruno27123@gmail.com"],
    "MINASSAL LTDA - SAO JOSE DO RIO PRETO": ["saruetesjrp79@gmail.com"],
    "MINASSAL LTDA - JUIZ DE FORA": ["fernandaferreira_jf@yahoo.com.br", "madallareis66@gmail.com"]
}

EMAILS_MEUS = [
    "beneditobandola@gmail.com",
    "benedito.bandola@minassal.com.br"
]


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

    st.sidebar.subheader("2. Seleção de Filial")
    coluna_distribuidor = 'Distribuidor' if 'Distribuidor' in df.columns else None
    lista_filiais = ["Todas"] + list(df[coluna_distribuidor].dropna().unique()) if coluna_distribuidor else ["Todas"] + list(EMAILS_PROMOTORES.keys())
    filial_escolhida = st.sidebar.selectbox("Filial:", lista_filiais)

    st.sidebar.subheader("3. Destinatários")
    enviar_apenas_para_mim = st.sidebar.checkbox("Enviar apenas para o meu e-mail (Teste)", value=True)

    st.sidebar.subheader("4. Credenciais de E-mail (Remetente)")
    remetente_email = st.sidebar.text_input("Seu E-mail:", value="beneditobandola@gmail.com")
    remetente_senha = st.sidebar.text_input(
        "Senha de App do E-mail:", type="password"
    )

    if st.sidebar.button("🚀 Enviar Relatório por E-mail"):
        if not remetente_email or not remetente_senha:
            st.sidebar.error("Preencha o e-mail remetente e a senha.")
        else:
            try:
                if enviar_apenas_para_mim:
                    destinatarios = EMAILS_MEUS
                else:
                    if filial_escolhida == "Todas":
                        destinatarios = []
                        for lista in EMAILS_PROMOTORES.values():
                            destinatarios.extend(lista)
                        destinatarios = list(set(destinatarios))
                    else:
                        destinatarios = EMAILS_PROMOTORES.get(filial_escolhida, EMAILS_MEUS)

                msg = MIMEMultipart()
                msg["From"] = remetente_email
                msg["To"] = ", ".join(destinatarios)
                msg["Subject"] = f"Relatório Automatizado - PDV Pet ({filial_escolhida})"

                corpo_html = (
                    f"<h3>Relatório Executivo - PDV Pet</h3>"
                    f"<p>Filial selecionada: <b>{filial_escolhida}</b></p>"
                    f"<p>Dados processados via painel Streamlit.</p>"
                )
                msg.attach(MIMEText(corpo_html, "html"))

                servidor = smtplib.SMTP("smtp.gmail.com", 587)
                servidor.starttls()
                servidor.login(remetente_email, remetente_senha)
                servidor.sendmail(msg["From"], destinatarios, msg.as_string())
                servidor.quit()

                st.success(f"✅ E-mail enviado com sucesso para: {', '.join(destinatarios)}!")
            except Exception as e:
                st.error(f"❌ Erro ao enviar: {e}")

    st.subheader("👁️ Visualização dos Dados Carregados")
    st.dataframe(df.head(100))
