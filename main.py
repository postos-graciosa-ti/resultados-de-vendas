import json
import os
from datetime import date
from pathlib import Path

import flet as ft
import httpx


def get_config_path() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    config_dir = base / "PostosGraciosa"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"


def carregar_config() -> dict:
    path = get_config_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"WP_BASE_URL": "", "WP_API_KEY": ""}


def salvar_config(cfg: dict) -> None:
    get_config_path().write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
    )


METAS_POR_POSTO = {
    "14562": {
        "GRID": {
            "metas": [10000.0, 12000.0, 15000.0],
            "fatores": [0.01, 0.015, 0.02],
        },
        "Vendas Pista": {
            "metas": [2000.0, 3000.0, 4000.0],
            "fatores": [0.05, 0.06, 0.07],
        },
        "Aditivos": {
            "metas": [20.0, 35.0, 6000.0],
            "fatores": [0.50, 1.50, 0.01],
        },
        "Palhetas": {
            "metas": [10.0, 15.0, 25.0],
            "fatores": [1.00, 1.50, 2.00],
        },
        "Diversos Pista": {
            "metas": [15.0, 25.0, 30.0],
            "fatores": [1.00, 1.50, 2.00],
        },
        "Produtos para Carro": {
            "metas": [10.0, 15.0, 25.0],
            "fatores": [1.00, 1.50, 2.00],
        },
        "Filtros": {
            "metas": [45.0, 60.0, 75.0],
            "fatores": [1.00, 1.50, 2.00],
        },
        "Vendas Loja": {
            "metas": [6000, 8000, 10000],
            "fatores": [0.025, 0.050, 0.01],
        },
        "Troca de Oleo": {
            "metas": [15000.0, 20000.0, 25000.0],
            "fatores": [0.06, 0.07, 0.08],
        },
    },
}


def buscar_dados_brutos(data_inicial, data_final, empresa_codigo, cfg):
    wp_base_url = cfg.get("WP_BASE_URL", "").rstrip("/")
    wp_api_key = cfg.get("WP_API_KEY", "")
    if not wp_base_url or not wp_api_key:
        raise ValueError(
            "Configure WP_BASE_URL e WP_API_KEY nas Configuracoes antes de gerar relatorios."
        )
    url = (
        f"{wp_base_url}/INTEGRACAO/MAPA_DESEMPENHO"
        f"?CHAVE={wp_api_key}&dataInicial={data_inicial}"
        f"&dataFinal={data_final}&empresaCodigo={empresa_codigo}"
    )
    with httpx.Client() as client:
        resposta = client.get(url)
        resposta.raise_for_status()
        return resposta.json()


def somar_por_criterio(dados, campo_filtro, valores_filtro, campo_soma):
    total = 0.0
    if isinstance(valores_filtro, str):
        valores_filtro = [valores_filtro]
    for item in dados:
        if item.get(campo_filtro) in valores_filtro:
            valor_bruto = item.get(campo_soma)
            if valor_bruto is not None:
                if isinstance(valor_bruto, str):
                    valor_limpo = valor_bruto.replace(".", "").replace(",", ".")
                    try:
                        total += float(valor_limpo)
                    except ValueError:
                        pass
                else:
                    total += float(valor_bruto)
    return total


def calcular_ciclo_atual():
    """Retorna (data_inicio, data_fim) do ciclo atual: dia 26 mês anterior até dia 25 mês atual."""
    hoje = date.today()
    if hoje.day <= 25:
        # Ainda no ciclo: início foi dia 26 do mês anterior
        mes_ini = hoje.month - 1 if hoje.month > 1 else 12
        ano_ini = hoje.year if hoje.month > 1 else hoje.year - 1
        inicio = date(ano_ini, mes_ini, 26)
        fim = date(hoje.year, hoje.month, 25)
    else:
        # Já passou do dia 25: início é dia 26 do mês atual, fim dia 25 do próximo
        inicio = date(hoje.year, hoje.month, 26)
        mes_fim = hoje.month + 1 if hoje.month < 12 else 1
        ano_fim = hoje.year if hoje.month < 12 else hoje.year + 1
        fim = date(ano_fim, mes_fim, 25)
    return inicio, fim


def calcular_necessario_por_dia(realizado, proxima_meta):
    """Calcula quanto falta por dia até o fim do ciclo para atingir a próxima meta."""
    hoje = date.today()
    _, fim_ciclo = calcular_ciclo_atual()
    dias_restantes = max((fim_ciclo - hoje).days, 1)
    falta = proxima_meta - realizado
    if falta <= 0:
        return 0.0, dias_restantes
    return falta / dias_restantes, dias_restantes


def calcular_dados_indicador(indicador, realizado, filial_codigo):
    """Retorna todos os dados calculados para um indicador."""
    config_posto = METAS_POR_POSTO.get(filial_codigo, {})
    config_meta = config_posto.get(
        indicador, {"metas": [0, 0, 0], "fatores": [0, 0, 0]}
    )
    metas = config_meta["metas"]
    fatores = config_meta["fatores"]

    nivel_batido = -1
    for i, m in enumerate(metas):
        if realizado >= m:
            nivel_batido = i

    fator_atual = float(fatores[nivel_batido]) if nivel_batido >= 0 else 0.0
    comissao = float(realizado) * fator_atual

    # Próxima meta e necessário/dia
    if nivel_batido < 2:
        proxima_meta_idx = nivel_batido + 1
        proxima_meta_valor = metas[proxima_meta_idx]
        necessario_dia, dias_restantes = calcular_necessario_por_dia(realizado, proxima_meta_valor)
    else:
        proxima_meta_idx = None
        proxima_meta_valor = None
        necessario_dia = 0.0
        dias_restantes = 0

    return {
        "metas": metas,
        "fatores": fatores,
        "nivel_batido": nivel_batido,          # -1 = nenhuma meta atingida
        "fator_atual": fator_atual,
        "comissao": comissao,
        "proxima_meta_idx": proxima_meta_idx,
        "proxima_meta_valor": proxima_meta_valor,
        "necessario_dia": necessario_dia,
        "dias_restantes": dias_restantes,
    }


# ──────────────────────────────────────────────
# Indicadores
# ──────────────────────────────────────────────

INDICADORES = {
    "GRID": ("produtoNome", ["GASOLINA ADITIVADA"], "quantidade"),
    "Vendas Pista": (
        "grupoNome",
        [
            "LUBRIFICANTES/GRAXAS", "ADITIVOS", "PALHETAS",
            "FILTROS DE AR", "FILTROS DE COMBUSTIVEL", "FILTROS DE OLEO",
            "DIVERSOS_PISTA", "DIVERSOS PISTA", "PRODUTOS PARA CARRO",
            "ARLA", "AROELAS/BUJOES/ABRACADEIRAS",
        ],
        "valorVenda",
    ),
    "Aditivos": ("grupoNome", ["ADITIVOS"], "quantidade"),
    "Palhetas": ("grupoNome", ["PALHETAS"], "quantidade"),
    "Diversos Pista": ("grupoNome", ["DIVERSOS PISTA"], "quantidade"),
    "Produtos para Carro": ("grupoNome", ["PRODUTOS PARA CARRO"], "quantidade"),
    "Filtros": (
        "grupoNome",
        ["FILTROS DE AR", "FILTROS DE COMBUSTIVEL", "FILTROS DE OLEO"],
        "quantidade",
    ),
    "Vendas Loja": (
        "grupoNome",
        [
            "CARTOES", "CIGARROS", "ICE/COOLER/ENERGETICOS", "CERVEJAS",
            "AGUAS/ CHAS/ REFRIGERANTES", "BOMBONIERE(CHOCOLATES 25G,76 G",
            "BARRAS,CAIXAS CHOCOLATES 100G,300G", "BOLACHAS/BISCOITOS/TORRADA",
            "CONVENIENCIA/ALIMENTOS DIVERSOS", "DIVERSOS LOJA/BRIQUEDOS E OUTROS",
            "SORVETES/PICOLES", "CHIPS SALGADINHOS", "BEBIDAS QUENTES",
            "HIGIENE/LIMPEZA", "CHARUTOS/CIGARRILHAS", "CARTAO ELETRONICO",
            "PILHAS", "CHINELOS", "SUCOS E ACHOCOLATADOS", "ELETRONICOS",
            "AMENDOINS/ CEREAIS", "BALAS/ PIRULITOS", "CHICLETS",
            "ESTUFA/FRIOS", "LIVROS",
        ],
        "valorVenda",
    ),
    "Troca de Oleo": (
        "grupoNome",
        [
            "ADITIVOS", "ARLA", "AROELAS/BUJOES/ABRACADEIRAS",
            "DIVERSOS PISTA", "FILTROS DE AR", "FILTROS DE COMBUSTIVEL",
            "FILTROS DE OLEO", "LUBRIFICANTES/GRAXAS", "PALHETAS",
            "PRODUTOS PARA CARRO",
        ],
        "valorVenda",
    ),
}


# ──────────────────────────────────────────────
# Builders de cards por tipo de relatório
# ──────────────────────────────────────────────

def build_card_diario(func, rows_diario):
    """Card do Relatório Diário para um funcionário."""
    return ft.Card(
        ft.Container(
            padding=12,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text(func, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                    ft.Divider(height=4),
                    ft.DataTable(
                        column_spacing=20,
                        columns=[
                            ft.DataColumn(ft.Text("Indicador", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Realizado", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Meta 1", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Meta 2", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Meta 3", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Proxima Meta", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Nec./Dia", weight=ft.FontWeight.BOLD), numeric=True),
                        ],
                        rows=rows_diario,
                    ),
                ],
            ),
        )
    )


def build_card_comissoes(func, rows_comissao, total_comissao):
    """Card do Relatório de Comissões para um funcionário."""
    return ft.Card(
        ft.Container(
            padding=12,
            content=ft.Column(
                spacing=8,
                controls=[
                    ft.Text(func, size=15, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
                    ft.Divider(height=4),
                    ft.DataTable(
                        column_spacing=20,
                        columns=[
                            ft.DataColumn(ft.Text("Indicador", weight=ft.FontWeight.BOLD)),
                            ft.DataColumn(ft.Text("Realizado", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Meta 1", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Meta 2", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Meta 3", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Meta Atingida", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Fator 1", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Fator 2", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Fator 3", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Fator Atual", weight=ft.FontWeight.BOLD), numeric=True),
                            ft.DataColumn(ft.Text("Comissao", weight=ft.FontWeight.BOLD), numeric=True),
                        ],
                        rows=rows_comissao,
                    ),
                    ft.Divider(height=4),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        controls=[
                            ft.Text(
                                f"Total de Comissoes: R$ {total_comissao:,.2f}",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREEN_800,
                            )
                        ],
                    ),
                ],
            ),
        )
    )


# ──────────────────────────────────────────────
# App principal
# ──────────────────────────────────────────────

def main(page: ft.Page):
    page.title = "Postos Graciosa | Relatorios de Desempenho"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    cfg = carregar_config()

    # ─── Widgets de configuracoes ──────────────────
    txt_url = ft.TextField(
        label="URL Base da API (WP_BASE_URL)",
        hint_text="https://exemplo.com.br",
        value=cfg.get("WP_BASE_URL", ""),
        expand=True,
        prefix_icon=ft.Icons.LINK,
    )
    txt_key = ft.TextField(
        label="Chave da API (WP_API_KEY)",
        hint_text="Sua chave secreta",
        value=cfg.get("WP_API_KEY", ""),
        password=True,
        can_reveal_password=True,
        expand=True,
        prefix_icon=ft.Icons.VPN_KEY,
    )
    cfg_status = ft.Text("", color=ft.Colors.GREEN_700)

    # ─── Widgets da tela principal ─────────────────
    txt_data_ini = ft.TextField(label="Data Inicial", value="2026-03-26", expand=True)
    txt_data_fim = ft.TextField(label="Data Final", value="2026-04-25", expand=True)
    dd_filial = ft.Dropdown(
        label="Selecionar Posto",
        expand=True,
        options=[ft.dropdown.Option("14562", "Posto Jariva")],
        value="14562",
    )
    dd_tipo = ft.Dropdown(
        label="Tipo de Relatorio",
        options=[
            ft.dropdown.Option("filial", "RELATORIO POR FILIAL"),
            ft.dropdown.Option("diario", "RELATORIO DIARIO (Por Funcionario)"),
            ft.dropdown.Option("comissoes", "RELATORIO DE COMISSOES (Por Funcionario)"),
        ],
        value="diario",
        expand=True,
    )
    result_container = ft.Column(spacing=20)

    aviso_cfg = ft.Container(
        visible=not (cfg.get("WP_BASE_URL") and cfg.get("WP_API_KEY")),
        bgcolor=ft.Colors.ORANGE_50,
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        content=ft.Row(
            wrap=True,
            controls=[
                ft.Icon(ft.Icons.WARNING_AMBER, color=ft.Colors.ORANGE_700),
                ft.Text(
                    "API nao configurada. Acesse Configuracoes antes de gerar relatorios.",
                    color=ft.Colors.ORANGE_900,
                ),
            ],
        ),
    )

    tela_principal = ft.Container(expand=True, visible=True)
    tela_config = ft.Container(expand=True, visible=False)

    def ir_para_config(e=None):
        txt_url.value = cfg.get("WP_BASE_URL", "")
        txt_key.value = cfg.get("WP_API_KEY", "")
        cfg_status.value = ""
        tela_principal.visible = False
        tela_config.visible = True
        page.update()

    def ir_para_principal(e=None):
        tela_principal.visible = True
        tela_config.visible = False
        page.update()

    def salvar_cfg(e):
        nova_cfg = {
            "WP_BASE_URL": txt_url.value.strip(),
            "WP_API_KEY": txt_key.value.strip(),
        }
        salvar_config(nova_cfg)
        cfg.update(nova_cfg)
        cfg_status.value = "Configuracoes salvas com sucesso!"
        cfg_status.color = ft.Colors.GREEN_700
        aviso_cfg.visible = not (cfg.get("WP_BASE_URL") and cfg.get("WP_API_KEY"))
        page.update()

    def testar_conexao(e):
        cfg_status.value = "Testando conexao..."
        cfg_status.color = ft.Colors.BLUE_700
        page.update()
        try:
            url = txt_url.value.strip().rstrip("/")
            key = txt_key.value.strip()
            if not url or not key:
                raise ValueError("Preencha URL e Chave antes de testar.")
            test_url = (
                f"{url}/INTEGRACAO/MAPA_DESEMPENHO"
                f"?CHAVE={key}&dataInicial=2026-01-01&dataFinal=2026-01-01&empresaCodigo=14562"
            )
            with httpx.Client(timeout=10) as client:
                r = client.get(test_url)
            if r.status_code < 500:
                cfg_status.value = f"Conexao OK - HTTP {r.status_code}"
                cfg_status.color = ft.Colors.GREEN_700
            else:
                cfg_status.value = f"Servidor retornou HTTP {r.status_code}"
                cfg_status.color = ft.Colors.ORANGE_700
        except Exception as ex:
            cfg_status.value = f"Erro: {ex}"
            cfg_status.color = ft.Colors.RED_700
        page.update()

    # ─── Handler do relatório ──────────────────────
    def processar_relatorio(e):
        result_container.controls.clear()
        page.update()

        codigo = dd_filial.value
        try:
            dados = buscar_dados_brutos(
                txt_data_ini.value, txt_data_fim.value, codigo, cfg
            )
        except Exception as err:
            result_container.controls.append(ft.Text(str(err), color=ft.Colors.RED_700))
            page.update()
            return

        if not dados:
            result_container.controls.append(
                ft.Text("Nenhum dado encontrado.", color="red")
            )
            page.update()
            return

        nome_posto = next(
            (opt.text for opt in dd_filial.options if opt.key == codigo), "Posto"
        )

        # ── RELATÓRIO POR FILIAL ────────────────────
        if dd_tipo.value == "filial":
            table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Indicador")),
                    ft.DataColumn(ft.Text("Total"), numeric=True),
                ],
                rows=[],
            )
            for nome, specs in INDICADORES.items():
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

        # ── RELATÓRIO DIÁRIO ────────────────────────
        elif dd_tipo.value == "diario":
            _, fim_ciclo = calcular_ciclo_atual()
            result_container.controls.append(
                ft.Text(
                    f"Relatorio Diario — {nome_posto}  |  Ciclo ate {fim_ciclo.strftime('%d/%m/%Y')}",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_900,
                )
            )

            funcionarios = sorted(
                {item.get("funcionarioNome") for item in dados if item.get("funcionarioNome")}
            )

            for func in funcionarios:
                dados_func = [d for d in dados if d.get("funcionarioNome") == func]
                rows_diario = []

                for nome, specs in INDICADORES.items():
                    realizado = somar_por_criterio(dados_func, specs[0], specs[1], specs[2])
                    calc = calcular_dados_indicador(nome, realizado, codigo)

                    metas = calc["metas"]

                    # Próxima meta
                    if calc["proxima_meta_valor"] is not None:
                        prox_meta_txt = ft.Text(
                            f"{calc['proxima_meta_valor']:,.2f}",
                            color=ft.Colors.ORANGE_700,
                            weight=ft.FontWeight.BOLD,
                        )
                        nec_dia_txt = ft.Text(
                            f"{calc['necessario_dia']:,.2f}",
                            color=ft.Colors.RED_700,
                            weight=ft.FontWeight.BOLD,
                        )
                    else:
                        prox_meta_txt = ft.Text("Max. Atingida", color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD)
                        nec_dia_txt = ft.Text("-", color=ft.Colors.GREY_500)

                    rows_diario.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(nome)),
                                ft.DataCell(ft.Text(f"{realizado:,.2f}")),
                                ft.DataCell(ft.Text(f"{metas[0]:,.2f}", color=ft.Colors.GREY_700)),
                                ft.DataCell(ft.Text(f"{metas[1]:,.2f}", color=ft.Colors.GREY_700)),
                                ft.DataCell(ft.Text(f"{metas[2]:,.2f}", color=ft.Colors.GREY_700)),
                                ft.DataCell(prox_meta_txt),
                                ft.DataCell(nec_dia_txt),
                            ]
                        )
                    )

                result_container.controls.append(build_card_diario(func, rows_diario))

        # ── RELATÓRIO DE COMISSÕES ──────────────────
        elif dd_tipo.value == "comissoes":
            result_container.controls.append(
                ft.Text(
                    f"Relatorio de Comissoes — {nome_posto}",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_900,
                )
            )

            funcionarios = sorted(
                {item.get("funcionarioNome") for item in dados if item.get("funcionarioNome")}
            )

            for func in funcionarios:
                dados_func = [d for d in dados if d.get("funcionarioNome") == func]
                rows_comissao = []
                total_comissao = 0.0

                for nome, specs in INDICADORES.items():
                    realizado = somar_por_criterio(dados_func, specs[0], specs[1], specs[2])
                    calc = calcular_dados_indicador(nome, realizado, codigo)

                    metas = calc["metas"]
                    fatores = calc["fatores"]
                    nivel = calc["nivel_batido"]
                    total_comissao += calc["comissao"]

                    # Meta atingida
                    if nivel >= 0:
                        meta_atingida_txt = ft.Text(
                            f"Meta {nivel + 1}: {metas[nivel]:,.2f}",
                            color=ft.Colors.GREEN_700,
                            weight=ft.FontWeight.BOLD,
                        )
                    else:
                        meta_atingida_txt = ft.Text("Nenhuma", color=ft.Colors.RED_400)

                    # Fator atual
                    fator_atual_txt = ft.Text(
                        f"{calc['fator_atual']:.3f}",
                        color=ft.Colors.GREEN_800 if nivel >= 0 else ft.Colors.GREY_500,
                        weight=ft.FontWeight.BOLD,
                    )

                    rows_comissao.append(
                        ft.DataRow(
                            cells=[
                                ft.DataCell(ft.Text(nome)),
                                ft.DataCell(ft.Text(f"{realizado:,.2f}")),
                                ft.DataCell(ft.Text(f"{metas[0]:,.2f}", color=ft.Colors.GREY_700)),
                                ft.DataCell(ft.Text(f"{metas[1]:,.2f}", color=ft.Colors.GREY_700)),
                                ft.DataCell(ft.Text(f"{metas[2]:,.2f}", color=ft.Colors.GREY_700)),
                                ft.DataCell(meta_atingida_txt),
                                ft.DataCell(ft.Text(f"{fatores[0]:.3f}", color=ft.Colors.GREY_600)),
                                ft.DataCell(ft.Text(f"{fatores[1]:.3f}", color=ft.Colors.GREY_600)),
                                ft.DataCell(ft.Text(f"{fatores[2]:.3f}", color=ft.Colors.GREY_600)),
                                ft.DataCell(fator_atual_txt),
                                ft.DataCell(
                                    ft.Text(
                                        f"R$ {calc['comissao']:,.2f}",
                                        color=ft.Colors.GREEN_800,
                                        weight=ft.FontWeight.BOLD,
                                    )
                                ),
                            ]
                        )
                    )

                result_container.controls.append(
                    build_card_comissoes(func, rows_comissao, total_comissao)
                )

        page.update()

    # ─── Montagem das telas ────────────────────────
    tela_principal.content = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.AppBar(
                title=ft.Text("Postos Graciosa | Desempenho"),
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.SETTINGS,
                        tooltip="Configuracoes",
                        icon_color=ft.Colors.WHITE,
                        on_click=ir_para_config,
                    )
                ],
            ),
            ft.Container(
                padding=20,
                content=ft.Column(
                    spacing=16,
                    controls=[
                        aviso_cfg,
                        ft.Row([txt_data_ini, txt_data_fim, dd_filial]),
                        ft.Row(
                            [
                                dd_tipo,
                                ft.FilledButton(
                                    "Gerar Relatorio",
                                    icon=ft.Icons.PLAY_ARROW,
                                    on_click=processar_relatorio,
                                ),
                            ]
                        ),
                        result_container,
                    ],
                ),
            ),
        ],
    )

    tela_config.content = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        controls=[
            ft.AppBar(
                leading=ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.WHITE,
                    on_click=ir_para_principal,
                ),
                title=ft.Text("Configuracoes"),
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
            ),
            ft.Container(
                padding=24,
                content=ft.Column(
                    spacing=20,
                    controls=[
                        ft.Text(
                            "Variaveis de Ambiente",
                            size=22,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_900,
                        ),
                        ft.Text(
                            "As configuracoes sao salvas localmente no dispositivo.",
                            size=13,
                            color=ft.Colors.GREY_700,
                        ),
                        ft.Divider(),
                        ft.Row([txt_url]),
                        ft.Row([txt_key]),
                        ft.Row(
                            spacing=12,
                            controls=[
                                ft.FilledButton("Salvar", icon=ft.Icons.SAVE, on_click=salvar_cfg),
                                ft.OutlinedButton("Testar Conexao", icon=ft.Icons.WIFI_TETHERING, on_click=testar_conexao),
                            ],
                        ),
                        cfg_status,
                        ft.Divider(),
                        ft.Text(
                            f"Arquivo: {get_config_path()}",
                            size=11,
                            color=ft.Colors.GREY_600,
                            italic=True,
                        ),
                    ],
                ),
            ),
        ],
    )

    page.add(tela_principal, tela_config)


if __name__ == "__main__":
    ft.run(main)