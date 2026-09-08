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
    return None, None, None

  indice_anterior = max(0, indice_atual - 1)
  data_inicio_geral = PERIODOS[chaves_periodos[indice_anterior]]["inicio"]
  data_hoje_str = hoje.strftime("%Y-%m-%d")

  return periodo_atual, data_inicio_geral, data_hoje_str


def baixar_dados_pdv():
  periodo_atual, data_inicio, data_fim = obter_intervalo_historico()

  if not periodo_atual:
    print("❌ A data atual está fora dos períodos cadastrados.")
    return None, None

  print(
      f"📅 Período vigente: {periodo_atual} | Baixando histórico de {data_inicio}"
      f" até {data_fim}..."
  )

  with sync_playwright() as p:
    # Alterado para True para rodar perfeitamente no GitHub Actions
    browser = p.chromium.launch(headless=True)
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


if __name__ == "__main__":
  arquivo, periodo = baixar_dados_pdv()
