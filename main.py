import httpx
from decouple import config


def buscar_dados_brutos(data_inicial, data_final, empresa_codigo):
    wp_base_url = config("WP_BASE_URL")

    wp_api_key = config("WP_API_KEY")

    wp_mapa_desempenho_url = (
        f"{wp_base_url}/INTEGRACAO/MAPA_DESEMPENHO"
        f"?CHAVE={wp_api_key}&dataInicial={data_inicial}"
        f"&dataFinal={data_final}&empresaCodigo={empresa_codigo}"
    )

    with httpx.Client() as client:
        resposta = client.get(wp_mapa_desempenho_url)

        resposta.raise_for_status()

        return resposta.json()


def somar_por_criterio(dados, campo_filtro, valores_filtro, campo_soma):
    total = 0.0

    if isinstance(valores_filtro, str):
        valores_filtro = [valores_filtro]

    for item in dados:
        valor_no_item = item.get(campo_filtro)

        if valor_no_item in valores_filtro:
            valor_para_somar = item.get(campo_soma) or 0

            total += float(valor_para_somar)

    return total


def gerar_relatorios(data_inicial, data_final, empresa_codigo, tipo_relatorio):
    dados_brutos = buscar_dados_brutos(data_inicial, data_final, empresa_codigo)

    if tipo_relatorio == "relatorio de filial":
        agregadores = {
            "Gasolina grid": somar_por_criterio(
                dados_brutos, "produtoNome", "GASOLINA ADITIVADA", "quantidade"
            ),
            "Vendas pista": somar_por_criterio(
                dados_brutos,
                "grupoNome",
                [
                    "LUBRIFICANTES/GRAXAS",
                    "ADITIVOS",
                    "PALHETAS",
                    "FILTROS DE AR",
                    "FILTROS DE COMBUSTÍVEL",
                    "FILTROS DE COMBUSTIVEL",
                    "FILTROS DE OLEO",
                    "DIVERSOS_PISTA",
                    "DIVERSOS PISTA",
                    "PRODUTOS PARA CARRO",
                    "ARLA",
                    "AROELAS/BUJOES/ABRACADEIRAS",
                ],
                "valorVenda",
            ),
            "Aditivos": somar_por_criterio(
                dados_brutos, "grupoNome", "ADITIVOS", "quantidade"
            ),
            "Palhetas": somar_por_criterio(
                dados_brutos, "grupoNome", "PALHETAS", "quantidade"
            ),
            "Diversos pista": somar_por_criterio(
                dados_brutos, "grupoNome", "DIVERSOS PISTA", "quantidade"
            ),
            "Produtos para carro": somar_por_criterio(
                dados_brutos, "grupoNome", "PRODUTOS PARA CARRO", "quantidade"
            ),
            "Filtros": somar_por_criterio(
                dados_brutos,
                "grupoNome",
                [
                    "FILTROS DE AR",
                    "FILTROS DE COMBUSTÍVEL",
                    "FILTROS DE OLEO",
                ],
                "quantidade",
            ),
            "Troca de óleo": somar_por_criterio(
                dados_brutos,
                "grupoNome",
                [
                    "ADITIVOS",
                    "ARLA",
                    "AROELAS/BUJOES/ABRACADEIRAS",
                    "DIVERSOS PISTA",
                    "FILTROS DE AR",
                    "FILTROS DE COMBUSTIVEL",
                    "FILTROS DE COMBUSTÍVEL",
                    "FILTROS DE OLEO",
                    "FILTROS DE ÓLEO",
                    "LUBRIFICANTES/GRAXAS",
                    "PALHETAS",
                    "PRODUTOS PARA CARRO",
                ],
                "valorVenda",
            ),
            "Vendas loja": somar_por_criterio(
                dados_brutos,
                "grupoNome",
                [
                    "CARTÕES",
                    "CIGARROS",
                    "ICE/COOLER/ENERGETICOS",
                    "CERVEJAS",
                    "AGUAS/ CHAS/ REFRIGERANTES",
                    "BOMBONIERE(CHOCOLATES 25G,76 G",
                    "BARRAS,CAIXAS CHOCOLATES 100G,300G",
                    "BOLACHAS/BISCOITOS/TORRADA",
                    "CONVENIENCIA/ALIMENTOS DIVERSOS",
                    "DIVERSOS LOJA/BRIQUEDOS E OUTROS",
                    "SORVETES/PICOLES",
                    "CHIPS SALGADINHOS",
                    "BEBIDAS QUENTES",
                    "HIGIENE/LIMPEZA",
                    "CHARUTOS/CIGARRILHAS",
                    "CARTÃO ELETRÔNICO",
                    "PILHAS",
                    "CHINELOS",
                    "SUCOS E ACHOCOLATADOS",
                    "ELETRONICOS",
                    "AMENDOINS/ CEREAIS",
                    "BALAS/ PIRULITOS",
                    "CHICLETS",
                    "ESTUFA/FRIOS",
                    "LIVROS",
                ],
                "valorVenda",
            ),
        }

        print(f"\n--- Resumo Genérico ---")

        for nome, valor in agregadores.items():
            print(f"{nome}: {valor:,.3f}")

        return agregadores


if __name__ == "__main__":
    gerar_relatorios("2026-03-01", "2026-03-31", "14562", "relatorio de filial")
