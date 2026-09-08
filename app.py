from datetime import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
import pandas as pd
import streamlit as st

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

st.set_page_config(page_title="Painel de Gestão - PDV Pet", page_icon="🐾", layout="wide")

st.title("📊 Painel de Oportunidades e Auditoria de Preços")
st.write("Execução completa: Login, download, processamento, geração de PDF organizado e envio.")

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

USUARIO_PDV = os.environ.get("USUARIO_PDV", "")
SENHA_PDV = os.environ.get("SENHA_PDV", "")

PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
CAMINHO_CSV_FINAL = os.path.join(PASTA_PROJETO, "historico_p9_p10.csv")

INICIO_P9  = "2026-08-10"
FIM_P9     = "2026-09-06"
INICIO_P10 = "2026-09-07"
FIM_P10    = "2026-10-04"

PRECOS_MAXIMOS = {
    'KiteKat Adulto Mix de Carnes - Small Bags 0,9Kg': 11.90,
    'Whiskas Sabor CARNE - Small Bags 0,5Kg': 14.90,
    'Pedigree CARNE, FRANGO E CEREAIS - Small Bags 0,9Kg': 19.90,
}

CORES_ITENS = {
    'Small Bags': colors.HexColor('#0056b3'),
    'Ponto Extra de Sachês/Petiscos': colors.HexColor('#d97706'),
    'Combos Virtuais Sachês': colors.HexColor('#059669'),
    'Combos Virtuais Petiscos': colors.HexColor('#7c3aed'),
    'Sheba Cremoso - Leve 2 Pague 1': colors.HexColor('#db2777')
}

def baixar_dados_pdvpet():
    if not USUARIO_PDV or not SENHA_PDV:
        return False
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        try:
            page.goto("https://www.pdvpet.com.br/", timeout=60000, wait_until="networkidle")
            page.fill('input[type="text"], input[name*="user"], input[name*="login"]', USUARIO_PDV)
            page.fill('input[type="password"]', SENHA_PDV)
            try:
                page.click('button[type="submit"], input[type="submit"]', timeout=5000)
            except Exception:
                page.keyboard.press("Enter")
            page.wait_for_load_state("networkidle")
            page.wait_for_selector('text=/Questionários|QUESTIONÁRIOS/i', timeout=60000)
            page.click('text=/Questionários|QUESTIONÁRIOS/i')
            page.wait_for_selector('#DataDe', timeout=60000)
            fuso_br = ZoneInfo("America/Sao_Paulo")
            data_hoje = datetime.now(fuso_br).strftime("%Y-%m-%d")
            page.fill('#DataDe', INICIO_P9)
            page.fill('#DataAte', data_hoje)
            page.click('button[type="submit"]:has-text("Buscar")')
            page.wait_for_timeout(8000)
            with page.expect_download(timeout=60000) as download_info:
                page.click('button.btn-outline-success:has-text("Exportar")')
            download_info.value.save_as(CAMINHO_CSV_FINAL)
            return True
        except Exception:
            return False
        finally:
            browser.close()

def gerar_pdf_organizado(filial, df_precos_filial, df_op_filial):
    nome_arquivo = f"Relatorio_{filial.replace(' ', '_').replace('-', '')}.pdf"
    caminho_pdf = os.path.join(PASTA_PROJETO, nome_arquivo)
    
    doc = SimpleDocTemplate(caminho_pdf, pagesize=letter, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=25)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=14, textColor=colors.HexColor('#1f6feb'), spaceAfter=6)
    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#57606a'), spaceAfter=12)
    sec_style = ParagraphStyle('SecStyle', parent=styles['Heading2'], fontSize=11, textColor=colors.HexColor('#24292f'), spaceBefore=10, spaceAfter=6)
    
    elements = []
    elements.append(Paragraph("<b>Relatório Executivo - PDV Pet</b>", title_style))
    elements.append(Paragraph(f"<b>Filial:</b> {filial} | <b>Gerado em:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", sub_style))

    # 1. BLOCO DE PREÇOS FORA DO TETO (PRIMEIRO)
    elements.append(Paragraph("1. Auditoria de Preços Acima do Teto", sec_style))
    if not df_precos_filial.empty:
        dados_preco = [["PDV / Cidade", "Produto", "Lido", "Teto", "Status"]]
        for _, row in df_precos_filial.iterrows():
            dados_preco.append([str(row['Pdv_Com_Cidade']), str(row['Item_Nome']), f"R$ {row['Preco_Lido']:.2f}", f"R$ {row['Preco_Maximo']:.2f}", str(row['Status'])])
        t_preco = Table(dados_preco, colWidths=[150, 160, 55, 55, 140])
        t_preco.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#ffebe9')), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ffc1c0')), ('FONTSIZE', (0,0), (-1,-1), 7.5)]))
        elements.append(t_preco)
    else:
        elements.append(Paragraph("✅ Nenhum preço acima do teto detectado.", ParagraphStyle('OkPreco', fontSize=9, textColor=colors.HexColor('#059669'))))
    
    elements.append(Spacer(1, 10))

    # 2. BLOCO DE OPORTUNIDADES ITEM A ITEM COM CORES DIFERENTES
    elements.append(Paragraph("2. Oportunidades por Categoria (Item a Item)", sec_style))
    if not df_op_filial.empty:
        itens_unicos = df_op_filial['Item'].unique()
        for item in itens_unicos:
            cor = CORES_ITENS.get(item, colors.HexColor('#333333'))
            estilo_item = ParagraphStyle(f'Style_{item}', fontSize=9.5, textColor=cor, fontName='Helvetica-Bold', spaceBefore=4)
            elements.append(Paragraph(f"• Categoria: {item}", estilo_item))
            
            df_sub = df_op_filial[df_op_filial['Item'] == item]
            for _, r in df_sub.iterrows():
                elements.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;- PDV: {r['Pdv_Com_Cidade']}", ParagraphStyle('SubIt', fontSize=8, textColor=colors.HexColor('#4b5563'))))
    else:
        elements.append(Paragraph("🏆 Nenhuma oportunidade pendente encontrada.", ParagraphStyle('OkOp', fontSize=9, textColor=colors.HexColor('#059669'))))

    doc.build(elements)
    return caminho_pdf

st.sidebar.header("⚙️ Configurações")
enviar_apenas_para_mim = st.sidebar.checkbox("Enviar apenas para o meu e-mail (Teste)", value=True)
remetente_email = st.sidebar.text_input("Seu E-mail (Remetente):", value="beneditobandola@gmail.com")
remetente_senha = st.sidebar.text_input("Senha de App do E-mail:", type="password")

if st.button("🚀 Executar Automação Completa e Enviar"):
    if not remetente_email or not remetente_senha:
        st.error("Preencha o e-mail remetente e a senha.")
    else:
        with st.spinner("Baixando dados e gerando relatórios organizados..."):
            sucesso = baixar_dados_pdvpet()
            if not os.path.exists(CAMINHO_CSV_FINAL):
                st.error("❌ Erro ao obter os dados do PDV Pet.")
                st.stop()
            
            df = pd.read_csv(CAMINHO_CSV_FINAL, sep=';', encoding='latin1')
            df['Data_Parsed'] = pd.to_datetime(df['Data'].astype(str).str.split(' ').str[0], format='%d/%m/%Y', errors='coerce')
            df['Preco_Num'] = pd.to_numeric(df['PrecoKg'].astype(str).str.replace('R$', '', regex=False).str.strip().str.replace(',', '.'), errors='coerce')
            df['Cidade_Clean'] = df['Cidade'].fillna('')
            df['Uf_Clean'] = df['Uf'].fillna('')
            df['Pdv_Com_Cidade'] = df.apply(lambda r: f"{r['Pdv']} - {r['Cidade_Clean']}/{r['Uf_Clean']}" if r['Cidade_Clean'] != '' else str(r['Pdv']), axis=1)
            df['OpcaoEmbalagem_Clean'] = df['OpcaoEmbalagem'].fillna('')
            df['Embalagem_Clean'] = df['Embalagem'].fillna('')
            df['Chave_Preco'] = df.apply(lambda r: f"{r['OpcaoEmbalagem_Clean']} - {r['Embalagem_Clean']}".strip(" -"), axis=1)

            df_p9 = df[(df['Data_Parsed'] >= INICIO_P9) & (df['Data_Parsed'] <= FIM_P9)]
            df_p10 = df[(df['Data_Parsed'] >= INICIO_P10) & (df['Data_Parsed'] <= FIM_P10)]

            p9_pares = df_p9[['Distribuidor', 'Cidade_Clean', 'Pdv_Com_Cidade', 'Item', 'Item']].drop_duplicates()
            p10_pares = df_p10[['Distribuidor', 'Cidade_Clean', 'Pdv_Com_Cidade', 'Item', 'Item']].drop_duplicates()
            
            df_oportunidades = pd.merge(p9_pares, p10_pares, on=['Distribuidor', 'Cidade_Clean', 'Pdv_Com_Cidade', 'Item'], how='left', indicator=True)
            df_oportunidades = df_oportunidades[df_oportunidades['_merge'] == 'left_only'].drop(columns=['_merge'])

            alertas_preco = []
            for _, row in df_p10.iterrows():
                chave = row['Chave_Preco']
                preco = row['Preco_Num']
                if chave in PRECOS_MAXIMOS and pd.notnull(preco) and preco > PRECOS_MAXIMOS[chave]:
                    alertas_preco.append({'Distribuidor': row['Distribuidor'], 'Pdv_Com_Cidade': row['Pdv_Com_Cidade'], 'Item_Nome': chave, 'Preco_Lido': preco, 'Preco_Maximo': PRECOS_MAXIMOS[chave], 'Status': row['Status']})
            df_alertas_preco = pd.DataFrame(alertas_preco)

            for filial in EMAILS_PROMOTORES.keys():
                df_op_f = df_oportunidades[df_oportunidades['Distribuidor'] == filial] if not df_oportunidades.empty else pd.DataFrame()
                df_pr_f = df_alertas_preco[df_alertas_preco['Distribuidor'] == filial] if not df_alertas_preco.empty else pd.DataFrame()
                
                caminho_pdf = gerar_pdf_organizado(filial, df_pr_f, df_op_f)
                
                destinatarios = EMAILS_MEUS if enviar_apenas_para_mim else EMAILS_PROMOTORES.get(filial, EMAILS_MEUS)
                
                msg = MIMEMultipart()
                msg["From"] = remetente_email
                msg["To"] = ", ".join(destinatarios)
                msg["Subject"] = f"Relatório Organizado - PDV Pet ({filial})"
                msg.attach(MIMEText(f"<h3>Relatório Executivo</h3><p>Filial: <b>{filial}</b></p>", "html"))
                
                if os.path.exists(caminho_pdf):
                    with open(caminho_pdf, "rb") as f:
                        part = MIMEApplication(f.read(), Name=os.path.basename(caminho_pdf))
                        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(caminho_pdf)}"'
                        msg.attach(part)
                
                try:
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(remetente_email, remetente_senha)
                    server.sendmail(remetente_email, destinatarios, msg.as_string())
                    server.quit()
                except Exception:
                    pass

        st.success("🎉 Processo completo executado com sucesso!")

st.subheader("👁️ Visualização dos Dados Carregados")
if os.path.exists(CAMINHO_CSV_FINAL):
    df_preview = pd.read_csv(CAMINHO_CSV_FINAL, sep=';', encoding='latin1')
    st.dataframe(df_preview.head(100))
else:
    st.info("Nenhum dado carregado ainda. Clique no botão acima para iniciar.")
