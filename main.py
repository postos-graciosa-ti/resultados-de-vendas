from datetime import datetime

import flet as ft
import httpx
from decouple import config


def buscar_dados_brutos(data_inicial, data_final, empresa_codigo):
    # Simulando a busca ou usando suas variáveis de ambiente
    try:
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
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return []


def somar_por_criterio(dados, campo_filtro, valores_filtro, campo_soma):
    total = 0.0
    if isinstance(valores_filtro, str):
        valores_filtro = [valores_filtro]
    for item in dados:
        if item.get(campo_filtro) in valores_filtro:
            total += float(item.get(campo_soma) or 0)
    return total


# --- DICIONÁRIO DE METAS (HARDCODED) ---
# Estrutura: { Indicador: { "metas": [v1, v2, v3], "fatores": [f1, f2, f3] } }
METAS_CONFIG = {
    "Gasolina grid": {"metas": [1000, 2000, 3000], "fatores": [0.01, 0.02, 0.03]},
    "Vendas pista": {"metas": [5000, 10000, 15000], "fatores": [0.005, 0.01, 0.015]},
    "Aditivos": {"metas": [50, 100, 150], "fatores": [1.0, 1.5, 2.0]},
    # ... adicione os outros conforme necessário
}

# --- INTERFACE FLET ---


def main(page: ft.Page):
    page.title = "Sistema de Desempenho - Relatórios"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    page.scroll = "auto"

    # Campos de Entrada
    txt_data_ini = ft.TextField(
        label="Data Inicial (AAAA-MM-DD)", value="2026-03-01", expand=True
    )
    txt_data_fim = ft.TextField(
        label="Data Final (AAAA-MM-DD)", value="2026-03-31", expand=True
    )
    txt_filial = ft.TextField(label="Código Filial", value="14562", expand=True)

    dd_tipo = ft.Dropdown(
        label="Tipo de Relatório",
        options=[
            ft.dropdown.Option("filial", "RELATÓRIO POR FILIAL"),
            ft.dropdown.Option("funcionario", "RELATÓRIO POR FUNCIONÁRIO"),
        ],
        value="filial",
        expand=True,
    )

    result_container = ft.Column(spacing=20)

    def calcular_comissao_e_meta(indicador, realizado):
        config_meta = METAS_CONFIG.get(
            indicador, {"metas": [0, 0, 0], "fatores": [0, 0, 0]}
        )
        metas = config_meta["metas"]
        fatores = config_meta["fatores"]

        nivel_batido = -1
        for i, m in enumerate(metas):
            if realizado >= m:
                nivel_batido = i

        comissao = realizado * fatores[nivel_batido] if nivel_batido >= 0 else 0

        proxima_meta_str = ""
        if nivel_batido < 2:
            falta = metas[nivel_batido + 1] - realizado
            proxima_meta_str = f"Faltam {falta:,.2f} para Nível {nivel_batido + 2}"
        else:
            ultrapassou = realizado - metas[2]
            proxima_meta_str = f"Meta Máxima Batida! (+{ultrapassou:,.2f})"

        return nivel_batido + 1, comissao, proxima_meta_str

    def processar_relatorio(e):
        result_container.controls.clear()
        page.update()

        dados = buscar_dados_brutos(
            txt_data_ini.value, txt_data_fim.value, txt_filial.value
        )
        if not dados:
            result_container.controls.append(
                ft.Text("Nenhum dado encontrado.", color="red")
            )
            page.update()
            return

        indicadores_nomes = {
            "Gasolina grid": ("produtoNome", ["GASOLINA ADITIVADA"], "quantidade"),
            "Vendas pista": (
                "grupoNome",
                [
                    "LUBRIFICANTES/GRAXAS",
                    "ADITIVOS",
                    "PALHETAS",
                    "FILTROS DE AR",
                    "FILTROS DE COMBUSTÍVEL",
                    "FILTROS DE OLEO",
                    "DIVERSOS PISTA",
                    "PRODUTOS PARA CARRO",
                    "ARLA",
                    "AROELAS/BUJOES/ABRACADEIRAS",
                ],
                "valorVenda",
            ),
            "Aditivos": ("grupoNome", ["ADITIVOS"], "quantidade"),
            "Vendas loja": (
                "grupoNome",
                [
                    "CARTÕES",
                    "CIGARROS",
                    "CERVEJAS",
                    "AGUAS/ CHAS/ REFRIGERANTES",
                    "CONVENIENCIA/ALIMENTOS DIVERSOS",
                ],
                "valorVenda",
            ),  # Reduzido para exemplo
        }

        if dd_tipo.value == "filial":
            table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Indicador")),
                    ft.DataColumn(ft.Text("Total"), numeric=True),
                ],
                rows=[],
            )
            for nome, specs in indicadores_nomes.items():
                valor = somar_por_criterio(dados, specs[0], specs[1], specs[2])
                table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(nome)),
                            ft.DataCell(ft.Text(f"{valor:,.2f}")),
                        ]
                    )
                )

            result_container.controls.append(
                ft.Text("Resumo por Filial", size=20, weight="bold")
            )
            result_container.controls.append(table)

        else:
            # Agrupar por Funcionário
            funcionarios = sorted(
                list(
                    set(
                        item.get("funcionarioNome")
                        for item in dados
                        if item.get("funcionarioNome")
                    )
                )
            )

            for func in funcionarios:
                dados_func = [d for d in dados if d.get("funcionarioNome") == func]

                rows = []
                total_comissao_func = 0

                for nome, specs in indicadores_nomes.items():
                    realizado = somar_por_criterio(
                        dados_func, specs[0], specs[1], specs[2]
                    )
                    nivel, comissao, status_meta = calcular_comissao_e_meta(
                        nome, realizado
                    )
                    total_comissao_func += comissao

                    rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(nome)),
                                ft.DataCell(ft.Text(f"{realizado:,.2f}")),
                                ft.DataCell(ft.Text(f"Nível {nivel}")),
                                ft.DataCell(ft.Text(status_meta)),
                                ft.DataCell(ft.Text(f"R$ {comissao:,.2f}")),
                            ]
                        )
                    )

                result_container.controls.append(
                    ft.Card(
                        content=ft.Container(
                            padding=15,
                            content=ft.Column(
                                [
                                    ft.Text(
                                        f"Funcionário: {func}",
                                        size=18,
                                        weight="bold",
                                        color="blue",
                                    ),
                                    ft.DataTable(
                                        columns=[
                                            ft.DataColumn(ft.Text("Indicador")),
                                            ft.DataColumn(ft.Text("Realizado")),
                                            ft.DataColumn(ft.Text("Meta")),
                                            ft.DataColumn(ft.Text("Status")),
                                            ft.DataColumn(ft.Text("Comissão")),
                                        ],
                                        rows=rows,
                                    ),
                                    ft.Text(
                                        f"Total Comissão: R$ {total_comissao_func:,.2f}",
                                        size=16,
                                        weight="bold",
                                    ),
                                ]
                            ),
                        )
                    )
                )

        page.update()

    btn_gerar = ft.ElevatedButton(
        "Gerar Relatório", icon="play_arrow", on_click=processar_relatorio
    )

    page.add(
        ft.Text("Filtros de Pesquisa", size=25, weight="bold"),
        ft.Row([txt_data_ini, txt_data_fim, txt_filial]),
        ft.Row([dd_tipo, btn_gerar]),
        ft.Divider(),
        result_container,
    )


if __name__ == "__main__":
    ft.run(main)
