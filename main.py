from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from playwright.sync_api import sync_playwright

PERIODOS = {
    "P9": {"inicio": "2026-08-09", "fim": "2026-09-05"},
    "P10": {"inicio": "2026-09-06", "fim": "2026-10-03"},
    "P11": {"inicio": "2026-10-04", "fim": "2026-10-31"},
    "P12": {"inicio": "2026-11-01", "fim": "2026-11-28"},
    "P13": {"inicio": "2026-11-29", "fim": "2027-01-02"},
}

PRECOS_MAXIMOS = {
    'KiteKat Adulto Mix de Carnes - Small Bags 0,9Kg': 11.90,
    'Whiskas Sabor CARNE - Small Bags 0,5Kg': 14.90,
    'Whiskas Sabor CARNE CASTRADOS - Small Bags 0,5Kg': 14.90,
    'Whiskas Sabor PEIXE - Small Bags 0,5Kg': 14.90,
    'Whiskas Sabor FILHOTE CARNE - Small Bags 0,5Kg': 14.90,
    'Champ Adulto Carne e Cereal - Small Bags 0,9Kg': 11.90,
    'Champ Filhotes Carne e Cereal - Small Bags 0,9Kg': 11.90,
    'Pedigree CARNE, FRANGO E CEREAIS - Small Bags 0,9Kg': 19.90,
    'Pedigree FILHOTES - Small Bags 0,9Kg': 19.90,
    'Pedigree RG CARNE E VEGETAIS - Small Bags 0,9Kg': 19.90,
    'Pedigree RP CARNE E VEGETAIS - Small Bags 0,9Kg': 19.90,
    'Pedigree NE AO LEITE - Small Bags 0,9Kg': 19.90,
    'Pedigree NE Carne - Small Bags 0,9Kg': 15.90,
    'Whiskas Sabor CARNE - Small Bags 0,9Kg': 20.90,
    'Whiskas Sabor CARNE CASTRADOS - Small Bags 0,9Kg': 20.90,
    'Whiskas Sabor FRANGO - Small Bags 0,9Kg': 20.90,
    'Whiskas Sabor PEIXE - Small Bags 0,9Kg': 20.90,
    'Whiskas Sabor PEIXE CASTRADOS - Small Bags 0,9Kg': 20.90,
    'Whiskas Sabor FILHOTE CARNE - Small Bags 0,9Kg': 20.90,
    'Pedigree CARNE, FRANGO E CEREAIS - Small Bags 2,7Kg': 54.90,
    'Pedigree FILHOTES - Small Bags 2,7Kg': 54.90,
    'Pedigree RG CARNE E VEGETAIS - Small Bags 2,7Kg': 54.90,
    'Pedigree RP CARNE E VEGETAIS - Small Bags 2,7Kg': 54.90,
}


def obter_intervalo_historico():
  fuso_br = ZoneInfo("America/Sao_Paulo")
  hoje = datetime.now(fuso_br).date()

  chaves_periodos = list(PERIODOS.keys())
  periodo_atual = None
  indice_atual = 0

  for i, nome_periodo in enumerate(chaves_periodos):
    datas = PERIODOS[nome_periodo]
    inicio = datetime.strptime(datas["inicio"], "%Y-%m-%d").date()
    fim = datetime.strptime(datas["fim"], "%Y-%m-%d").date()

    if inicio <= hoje <= fim:
      periodo_atual = nome_periodo
      indice_atual = i
      break

  if not periodo_atual:
    return None, None, None, None

  indice_anterior = max(0, indice_atual - 1)
  data_inicio_geral = PERIODOS[chaves_periodos[indice_anterior]]["inicio"]
  data_hoje_str = hoje.strftime("%Y-%m-%d")

  return periodo_atual, data_inicio_geral, data_hoje_str


def baixar_dados_pdv():
  periodo_atual, data_inicio, data_fim = obter_intervalo_historico()

  if not periodo_atual:
    print("❌ A data atual está fora dos períodos cadastrados.")
    return None

  print(
      f"📅 Período vigente: {periodo_atual} | Baixando histórico de {data_inicio}"
      f" até {data_fim}..."
  )

  with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    print("🔗 Acessando a página de login...")
    page.goto("https://www.pdvpet.com.br/login?ReturnUrl=%2F", timeout=90000)

    print("🔑 Preenchendo as credenciais...")
    page.fill(
        'input[type="text"], input[name*="user"], input[name*="login"]',
        "13731800640",
    )
    page.fill('input[type="password"]', "Fizzvini1234@")

    print("🚀 Enviando o formulário...")
    page.click(
        'button[type="submit"], input[type="submit"], button:has-text("Entrar")'
    )
    page.wait_for_load_state("networkidle")

    print("📋 Navegando até a aba de Questionários...")
    page.wait_for_selector("text=/Questionários|QUESTIONÁRIOS/i", timeout=90000)
    page.click("text=/Questionários|QUESTIONÁRIOS/i")

    print(
        "⏳ Preenchendo o intervalo de datas"
        f" ({data_inicio} até {data_fim})..."
    )
    page.wait_for_selector("#DataDe", timeout=90000)
    page.fill("#DataDe", data_inicio)
    page.fill("#DataAte", data_fim)

    page.click('button[type="submit"]:has-text("Buscar")')
    print("⏳ Aguardando o carregamento dos dados...")
    page.wait_for_timeout(10000)

    print("⏳ Iniciando o download do relatório consolidado...")
    with page.expect_download(timeout=90000) as download_info:
      page.click('button.btn-outline-success:has-text("Exportar")')
      try:
        page.wait_for_selector('a:has-text("Abrir")', timeout=10000)
        page.click('a:has-text("Abrir")')
      except Exception:
        pass

    caminho_arquivo = "historico_p9_p10.csv"
    download_info.value.save_as(caminho_arquivo)
    print(
        "✅ Planilha consolidada baixada e salva com sucesso em:"
        f" {caminho_arquivo}"
    )

    browser.close()
    return caminho_arquivo, periodo_atual


def processar_analise_completa(caminho_csv, periodo_atual):
  print(
      "\n--- PROCESSANDO ANÁLISE COMPLETA (OPORTUNIDADES + PREÇOS + ITENS"
      f" ESPECIAIS) PARA {periodo_atual} ---"
  )
  df = pd.read_csv(caminho_csv, sep=";", encoding="latin1")

  df["Data_Parsed"] = pd.to_datetime(
      df["Data"].astype(str).str.split(" ").str[0],
      format="%d/%m/%Y",
      errors="coerce",
  )

  p_info = PERIODOS[periodo_atual]
  inicio_atual = pd.to_datetime(p_info["inicio"])
  fim_atual = pd.to_datetime(p_info["fim"])

  df_p_atual = df[
      (df["Data_Parsed"] >= inicio_atual) & (df["Data_Parsed"] <= fim_atual)
  ]

  chaves_periodos = list(PERIODOS.keys())
  idx = chaves_periodos.index(periodo_atual)
  if idx > 0:
    p_ant_info = PERIODOS[chaves_periodos[idx - 1]]
    inicio_ant = pd.to_datetime(p_ant_info["inicio"])
    fim_ant = pd.to_datetime(p_ant_info["fim"])
    df_p_anterior = df[
        (df["Data_Parsed"] >= inicio_ant) & (df["Data_Parsed"] <= fim_ant)
    ]
  else:
    print("⚠️ Não há período anterior cadastrado para comparativo.")
    return

  # 1. ANÁLISE DE SMALL BAGS (Oportunidades)
  print("\n📦 === 1. OPORTUNIDADES DE SMALL BAGS ===")
  colunas_sb = ["Distribuidor", "Usuario", "Pdv", "Cidade", "Embalagem", "OpcaoEmbalagem"]
  sb_ant = df_p_anterior[df_p_anterior["Embalagem"].notna() & df_p_anterior["Embalagem"].str.contains("Small Bags", case=False, na=False)][colunas_sb].drop_duplicates()
  sb_atual = df_p_atual[df_p_atual["Embalagem"].notna() & df_p_atual["Embalagem"].str.contains("Small Bags", case=False, na=False)][colunas_sb].drop_duplicates()

  op_sb = pd.merge(sb_ant, sb_atual, on=colunas_sb, how="left", indicator=True)
  op_sb = op_sb[op_sb["_merge"] == "left_only"].drop(columns=["_merge"])

  for filial, g_filial in op_sb.groupby("Distribuidor"):
    print(f"\n🏢 FILIAL: {filial} (Small Bags Pendentes)")
    for promotor, g_prom in g_filial.groupby("Usuario"):
      print(f"  👤 Promotor: {promotor} ({len(g_prom)} pendências)")
      for _, row in g_prom.iterrows():
        print(f"     - PDV: {row['Pdv']} | Cidade: {row['Cidade']} | Embalagem: {row['Embalagem']} | Sabor/Tipo: {row['OpcaoEmbalagem']}")

  # 2. ANÁLISE DE PONTO EXTRA DE SACHÊS/PETISCOS (Oportunidades e Contagem)
  print("\n⭐ === 2. ANÁLISE DE PONTO EXTRA DE SACHÊS/PETISCOS ===")
  colunas_pe = ["Distribuidor", "Usuario", "Pdv", "Cidade", "Item"]
  pe_ant = df_p_anterior[df_p_anterior["Item"].str.contains("Ponto Extra", case=False, na=False)][colunas_pe].drop_duplicates()
  pe_atual = df_p_atual[df_p_atual["Item"].str.contains("Ponto Extra", case=False, na=False)][colunas_pe].drop_duplicates()

  contagem_atual = df_p_atual[df_p_atual["Item"].str.contains("Ponto Extra", case=False, na=False)].groupby(["Distribuidor", "Usuario", "Pdv", "Cidade"]).size().reset_index(name="Total_Leituras_Atuais")
  print("\n📊 Contagem de Leituras de Ponto Extra no Período Atual por PDV:")
  print(contagem_atual.to_string(index=False))

  op_pe = pd.merge(pe_ant, pe_atual, on=colunas_pe, how="left", indicator=True)
  op_pe = op_pe[op_pe["_merge"] == "left_only"].drop(columns=["_merge"])

  for filial, g_filial in op_pe.groupby("Distribuidor"):
    print(f"\n🏢 FILIAL: {filial} (Ponto Extra Oportunidades)")
    for promotor, g_prom in g_filial.groupby("Usuario"):
      print(f"  👤 Promotor: {promotor} ({len(g_prom)} pendências)")
      for _, row in g_prom.iterrows():
        print(f"     - PDV: {row['Pdv']} | Cidade: {row['Cidade']} | Item/Ponto Extra: {row['Item']}")

  # 3. AUDITORIA DE PREÇOS ACIMA DO TETO POR TIPO/PESO (Small Bags)
  print("\n💰 === 3. AUDITORIA DE PREÇOS ACIMA DO TETO (SMALL BAGS POR TIPO/PESO) ===")
  df_p_atual['PrecoKg_Num'] = pd.to_numeric(df_p_atual['PrecoKg'].astype(str).str.replace(',', '.'), errors='coerce')
  df_sb_atual = df_p_atual[df_p_atual["Embalagem"].notna() & df_p_atual["Embalagem"].str.contains("Small Bags", case=False, na=False)].copy()

  alertas_preco = []
  for _, row in df_sb_atual.iterrows():
    opcao = str(row['OpcaoEmbalagem']).strip()
    embalagem = str(row['Embalagem']).strip()
    chave_produto = f"{opcao} - {embalagem}"
    
    if chave_produto in PRECOS_MAXIMOS:
      teto = PRECOS_MAXIMOS[chave_produto]
      preco_praticado = row['PrecoKg_Num']
      if pd.notna(preco_praticado) and preco_praticado > teto:
        alertas_preco.append({
            "Distribuidor": row["Distribuidor"],
            "Usuario": row["Usuario"],
            "Pdv": row["Pdv"],
            "Cidade": row["Cidade"],
            "Produto": chave_produto,
            "PrecoPraticado": preco_praticado,
            "PrecoMaximoTeto": teto
        })

  if alertas_preco:
    df_alertas = pd.DataFrame(alertas_preco)
    for filial, g_filial in df_alertas.groupby("Distribuidor"):
      print(f"\n🏢 FILIAL: {filial} (Alertas de Preço Acima do Teto)")
      for _, row in g_filial.iterrows():
        print(f"  ⚠️ PDV: {row['Pdv']} | Cidade: {row['Cidade']} | Promotor: {row['Usuario']}")
        print(f"     Produto: {row['Produto']} | Preço Lido: R$ {row['PrecoPraticado']:.2f} | Teto Permitido: R$ {row['PrecoMaximoTeto']:.2f}")
  else:
    print("✅ Nenhum preço acima do teto foi encontrado nas Small Bags do período atual.")

  # 4. ANÁLISE DE ITENS ESPECIAIS (Combos e Sheba) - Passado vs Atual
  print("\n📦 === 4. OPORTUNIDADES EM ITENS ESPECIAIS (Combos e Sheba) ===")
  itens_especiais = [
      "Combos Virtuais Sachês",
      "Combos Virtuais Petiscos",
      "Sheba Cremoso - Leve 2 Pague 1",
  ]
  colunas_esp = ["Distribuidor", "Usuario", "Pdv", "Cidade", "Item"]

  esp_ant = df_p_anterior[df_p_anterior["Item"].isin(itens_especiais)][colunas_esp].drop_duplicates()
  esp_atual = df_p_atual[df_p_atual["Item"].isin(itens_especiais)][colunas_esp].drop_duplicates()

  op_esp = pd.merge(esp_ant, esp_atual, on=colunas_esp, how="left", indicator=True)
  op_esp = op_esp[op_esp["_merge"] == "left_only"].drop(columns=["_merge"])

  if not op_esp.empty:
    for filial, g_filial in op_esp.groupby("Distribuidor"):
      print(f"\n🏢 FILIAL: {filial} (Itens Especiais Pendentes)")
      for promotor, g_prom in g_filial.groupby("Usuario"):
        print(f"  👤 Promotor: {promotor} ({len(g_prom)} pendências)")
        for _, row in g_prom.iterrows():
          print(f"     - PDV: {row['Pdv']} | Cidade: {row['Cidade']} | Item: {row['Item']}")
  else:
    print("✅ Nenhuma pendência encontrada para estes itens especiais no período atual.")


if __name__ == "__main__":
  arquivo, periodo = baixar_dados_pdv()
  if arquivo:
    processar_analise_completa(arquivo, periodo)

  input("\nPressione ENTER para fechar a janela...")