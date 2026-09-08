from datetime import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import pandas as pd
import streamlit as st

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

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

PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("historico_p9_p10.csv", sep=";", encoding="latin1")
        return df
    except FileNotFoundError:
        return None

def gerar_pdf_relatorio(filial, df_subset):
    nome_arquivo = f"Relatorio_PDV_Pet_{filial.replace(' ', '_').replace('-', '')}.pdf"
    caminho_pdf = os.path.join(PASTA_PROJETO, nome_arquivo)
    
    doc = SimpleDocTemplate(caminho_pdf, pagesize=letter, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#1f6feb'), spaceAfter=6)
    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#57606a'), spaceAfter=12)
    
    elements = []
    elements.append(Paragraph(f"<b>Relatório Executivo - PDV Pet</b>", title_style))
    elements.append(Paragraph(f"<b>Filial:</b> {filial} | <b>Gerado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", sub_style))

    if not df_subset.empty:
        # Monta uma tabela simples com os primeiros registros para o PDF
        colunas_exibir = [c for c in ['Pdv', 'Item', 'PrecoKg', 'Status'] if c in df_subset.columns]
        if not colunas_exibir:
            colunas_exibir = df_subset.columns[:4]
            
        dados_tabela = [[str(c) for c in colunas_exibir]]
        for _, row in df_subset.head(30).iterrows():
            dados_tabela.append([str(row.get(c, '')) for c in colunas_exibir])

        t = Table(dados_tabela)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f6f8fa')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d0d7de')),
            ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("Nenhum dado encontrado para os filtros selecionados.", styles['Normal']))

    doc.build(elements)
    return caminho_pdf

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
    enviar_pe = st.sidebar.checkbox("⭐ Oportunidades Ponto Extra", value=True)
    enviar_preco = st.sidebar.checkbox("💰 Alertas de Preços Acima do Teto", value=True)
    enviar_esp = st.sidebar.checkbox("🔥 Oportunidades Itens Especiais", value=True)

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
            st.sidebar.error("Preencha o e-mail remetente e a senha de aplicativo.")
        else:
            try:
                filiais_alvo = list(EMAILS_PROMOTORES.keys()) if filial_escolhida == "Todas" else [filial_escolhida]
                
                for f_atual in filiais_alvo:
                    if enviar_apenas_para_mim:
                        destinatarios = EMAILS_MEUS
                    else:
                        destinatarios = EMAILS_PROMOTORES.get(f_atual, EMAILS_MEUS)

                    # Filtra os dados da filial se a coluna existir
                    if coluna_distribuidor and coluna_distribuidor in df.columns:
                        df_filial = df[df[coluna_distribuidor] == f_atual]
                    else:
                        df_filial = df

                    # Gera o PDF específico para essa filial
                    caminho_pdf = gerar_pdf_relatorio(f_atual, df_filial)

                    msg = MIMEMultipart()
                    msg["From"] = remetente_email
                    msg["To"] = ", ".join(destinatarios)
                    msg["Subject"] = f"Relatório Automatizado - PDV Pet ({f_atual})"

                    corpo_html = (
                        f"<h3>Relatório Executivo - PDV Pet</h3>"
                        f"<p>Filial: <b>{f_atual}</b></p>"
                        f"<p>Segue em anexo o relatório em PDF gerado pelo painel.</p>"
                    )
                    msg.attach(MIMEText(corpo_html, "html"))

                    if os.path.exists(caminho_pdf):
                        with open(caminho_pdf, "rb") as arquivo_f:
                            parte_anexo = MIMEApplication(arquivo_f.read(), Name=os.path.basename(caminho_pdf))
                            parte_anexo['Content-Disposition'] = f'attachment; filename="{os.path.basename(caminho_pdf)}"'
                            msg.attach(parte_anexo)

                    servidor = smtplib.SMTP("smtp.gmail.com", 587)
                    servidor.starttls()
                    servidor.login(remetente_email, remetente_senha)
                    servidor.sendmail(msg["From"], destinatarios, msg.as_string())
                    servidor.quit()

                st.success(f"✅ Relatórios em PDF gerados e enviados com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao gerar/enviar: {e}")

    st.subheader("👁️ Visualização dos Dados Carregados")
    st.dataframe(df.head(100))
