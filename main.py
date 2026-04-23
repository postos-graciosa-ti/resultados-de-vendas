from datetime import date

import flet as ft
import httpx
from decouple import config

METAS_POR_POSTO = {
    # JARIVA
    "14562": {
        "GRID": {
            "metas": [
                10000.0,
                12000.0,
                15000.0,
            ],
            "fatores": [
                0.01,
                0.015,
                0.02,
            ],
        },
        "Vendas Pista": {
            "metas": [
                2000.0,
                3000.0,
                4000.0,
            ],
            "fatores": [
                0.05,
                0.06,
                0.07,
            ],
        },
        "Aditivos": {
            "metas": [
                20.0,
                35.0,
                6000.0,
            ],
            "fatores": [
                0.50,
                1.50,
                0.01,
            ],
        },
        "Palhetas": {
            "metas": [
                10.0,
                15.0,
                25.0,
            ],
            "fatores": [
                1.00,
                1.50,
                2.00,
            ],
        },
        "Diversos Pista": {
            "metas": [
                15.0,
                25.0,
                30.0,
            ],
            "fatores": [
                1.00,
                1.50,
                2.00,
            ],
        },
        "Produtos para Carro": {
            "metas": [
                10.0,
                15.0,
                25.0,
            ],
            "fatores": [
                1.00,
                1.50,
                2.00,
            ],
        },
        "Filtros": {
            "metas": [
                45.0,
                60.0,
                75.0,
            ],
            "fatores": [
                1.00,
                1.50,
                2.00,
            ],
        },
        "Vendas Loja": {
            "metas": [
                6000,
                8000,
                10000,
            ],
            "fatores": [
                0.025,
                0.050,
                1.000,
            ],
        },
        "Troca de Óleo": {
            "metas": [
                15000.0,
                20000.0,
                25000.0,
            ],
            "fatores": [
                0.06,
                0.07,
                0.08,
            ],
        },
    },
}


def buscar_dados_brutos(data_inicial, data_final, empresa_codigo):
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


def calcular_projecao_diaria(realizado, proxima_meta):
    hoje = date.today()

    if hoje.day <= 25:
        fim_ciclo = date(hoje.year, hoje.month, 25)

    else:
        mes_fim = hoje.month + 1 if hoje.month < 12 else 1

        ano_fim = hoje.year if hoje.month < 12 else hoje.year + 1

        fim_ciclo = date(ano_fim, mes_fim, 25)

    dias_restantes = (fim_ciclo - hoje).days

    if dias_restantes <= 0:
        dias_restantes = 1

    falta = proxima_meta - realizado

    if falta <= 0:
        return 0, dias_restantes

    return (falta / dias_restantes), dias_restantes


def calcular_comissao_e_meta(indicador, realizado, filial_codigo):
    config_posto = METAS_POR_POSTO.get(filial_codigo)

    config_meta = config_posto.get(
        indicador, {"metas": [0, 0, 0], "fatores": [0, 0, 0]}
    )

    metas = config_meta["metas"]

    fatores = config_meta["fatores"]

    nivel_batido = -1

    for i, m in enumerate(metas):
        if realizado >= m:
            nivel_batido = i

    fator_atual = fatores[nivel_batido] if nivel_batido >= 0 else 0.0

    comissao = realizado * fator_atual

    status_str = ""

    diario_str = ""

    if nivel_batido < 2:
        prox_meta_valor = metas[nivel_batido + 1]

        falta = prox_meta_valor - realizado

        valor_diario, dias = calcular_projecao_diaria(realizado, prox_meta_valor)

        status_str = f"Faltam {falta:,.2f}"

        diario_str = f"R$ {valor_diario:,.2f}/dia"

    else:
        status_str = "Meta Máxima!"

        diario_str = "-"

    return (
        nivel_batido + 1,
        comissao,
        status_str,
        diario_str,
        metas,
        fatores,
        fator_atual,
    )


def main(page: ft.Page):
    page.title = "Postos Graciosa | Relatórios de Desempenho"

    page.theme_mode = ft.ThemeMode.LIGHT

    page.padding = 20

    page.scroll = "auto"

    txt_data_ini = ft.TextField(label="Data Inicial", value="2026-03-26", expand=True)

    txt_data_fim = ft.TextField(label="Data Final", value="2026-04-25", expand=True)

    dd_filial = ft.Dropdown(
        label="Selecionar Posto",
        expand=True,
        options=[
            ft.dropdown.Option("14562", "Posto Jariva"),
        ],
        value="14562",
    )

    dd_tipo = ft.Dropdown(
        label="Tipo de Relatório",
        options=[
            ft.dropdown.Option("filial", "RELATÓRIO POR FILIAL"),
            ft.dropdown.Option("funcionario", "RELATÓRIO POR FUNCIONÁRIO"),
        ],
        value="funcionario",
        expand=True,
    )

    result_container = ft.Column(spacing=20)

    def processar_relatorio(e):
        result_container.controls.clear()

        page.update()

        codigo_selecionado = dd_filial.value

        dados = buscar_dados_brutos(
            txt_data_ini.value, txt_data_fim.value, codigo_selecionado
        )

        if not dados:
            result_container.controls.append(
                ft.Text("Nenhum dado encontrado.", color="red")
            )

            page.update()

            return

        indicadores_nomes = {
            "GRID": (
                "produtoNome",
                ["GASOLINA ADITIVADA"],
                "quantidade",
            ),
            "Vendas Pista": (
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
            "Aditivos": (
                "grupoNome",
                ["ADITIVOS"],
                "quantidade",
            ),
            "Palhetas": (
                "grupoNome",
                ["PALHETAS"],
                "quantidade",
            ),
            "Diversos Pista": (
                "grupoNome",
                ["DIVERSOS PISTA"],
                "quantidade",
            ),
            "Produtos para Carro": (
                "grupoNome",
                ["PRODUTOS PARA CARRO"],
                "quantidade",
            ),
            "Filtros": (
                "grupoNome",
                [
                    "FILTROS DE AR",
                    "FILTROS DE COMBUSTÍVEL",
                    "FILTROS DE OLEO",
                ],
                "quantidade",
            ),
            "Vendas Loja": (
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
            "Troca de Óleo": (
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
        }

        nome_posto = next(
            (opt.text for opt in dd_filial.options if opt.key == codigo_selecionado),
            "Posto",
        )

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
                ft.Text(f"Resumo: {nome_posto}", size=20, weight="bold")
            )

            result_container.controls.append(table)

        else:
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

                for nome, specs in indicadores_nomes.items():
                    realizado = somar_por_criterio(
                        dados_func, specs[0], specs[1], specs[2]
                    )

                    nivel, comissao, status, diario, grade_m, grade_f, f_atual = (
                        calcular_comissao_e_meta(nome, realizado, codigo_selecionado)
                    )

                    txt_metas = " | ".join([f"{m:,.0f}" for m in grade_m])

                    txt_fatores = " | ".join([f"{f:.3f}" for f in grade_f])

                    rows.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(nome)),
                                ft.DataCell(ft.Text(f"{realizado:,.2f}")),
                                ft.DataCell(
                                    ft.Text(txt_metas, size=11, color="blue_grey")
                                ),
                                ft.DataCell(ft.Text(f"Nív. {nivel}")),
                                ft.DataCell(
                                    ft.Text(txt_fatores, size=11, color="grey_700")
                                ),
                                ft.DataCell(
                                    ft.Text(
                                        f"{f_atual:.3f}", weight="bold", color="green"
                                    )
                                ),
                                ft.DataCell(ft.Text(status)),
                                ft.DataCell(
                                    ft.Text(diario, color="orange", weight="bold")
                                ),
                                ft.DataCell(ft.Text(f"R$ {comissao:,.2f}")),
                            ]
                        )
                    )

                result_container.controls.append(
                    ft.Card(
                        ft.Container(
                            padding=10,
                            content=ft.Column(
                                [
                                    ft.Text(f"Funcionário: {func}", weight="bold"),
                                    ft.DataTable(
                                        columns=[
                                            ft.DataColumn(ft.Text("Indicador")),
                                            ft.DataColumn(ft.Text("Realizado")),
                                            ft.DataColumn(ft.Text("Metas (1|2|3)")),
                                            ft.DataColumn(ft.Text("Nível")),
                                            ft.DataColumn(ft.Text("Grade Fatores")),
                                            ft.DataColumn(ft.Text("Fator Atual")),
                                            ft.DataColumn(ft.Text("Status")),
                                            ft.DataColumn(ft.Text("Nec./Dia")),
                                            ft.DataColumn(ft.Text("Comissão")),
                                        ],
                                        rows=rows,
                                    ),
                                ]
                            ),
                        )
                    )
                )

        page.update()

    btn_gerar = ft.FilledButton(
        "Gerar Relatório", icon=ft.Icons.PLAY_ARROW, on_click=processar_relatorio
    )

    page.add(
        ft.Row([txt_data_ini, txt_data_fim, dd_filial]),
        ft.Row([dd_tipo, btn_gerar]),
        result_container,
    )


if __name__ == "__main__":
    ft.run(main)
