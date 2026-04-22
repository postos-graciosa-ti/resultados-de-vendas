from datetime import date, datetime

import flet as ft
import httpx
from decouple import config

# ── lógica de negócio ────────────────────────────────────────────────────────

POSTOS = [
    ("GRACIOSA", "14526"),
    ("PIRAI", "14566"),
    ("JARIVA", "14562"),
    ("BEMER", "14564"),
    ("GRACIOSA V", "14565"),
    ("FATIMA", "14563"),
]


def buscar_dados_brutos(data_inicial, data_final, empresa_codigo):
    wp_base_url = config("WP_BASE_URL")
    wp_api_key = config("WP_API_KEY")
    url = (
        f"{wp_base_url}/INTEGRACAO/MAPA_DESEMPENHO"
        f"?CHAVE={wp_api_key}&dataInicial={data_inicial}"
        f"&dataFinal={data_final}&empresaCodigo={empresa_codigo}"
    )
    with httpx.Client() as client:
        resposta = client.get(url, timeout=30)
        resposta.raise_for_status()
        return resposta.json()


def somar_por_criterio(dados, campo_filtro, valores_filtro, campo_soma):
    total = 0.0
    if isinstance(valores_filtro, str):
        valores_filtro = [valores_filtro]
    for item in dados:
        if item.get(campo_filtro) in valores_filtro:
            total += float(item.get(campo_soma) or 0)
    return total


def gerar_relatorio_filial(data_inicial, data_final, empresa_codigo):
    dados = buscar_dados_brutos(data_inicial, data_final, empresa_codigo)
    return {
        "Gasolina Grid": somar_por_criterio(
            dados, "produtoNome", "GASOLINA ADITIVADA", "quantidade"
        ),
        "Vendas Pista": somar_por_criterio(
            dados,
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
        "Aditivos": somar_por_criterio(dados, "grupoNome", "ADITIVOS", "quantidade"),
        "Palhetas": somar_por_criterio(dados, "grupoNome", "PALHETAS", "quantidade"),
        "Diversos Pista": somar_por_criterio(
            dados, "grupoNome", "DIVERSOS PISTA", "quantidade"
        ),
        "Produtos para Carro": somar_por_criterio(
            dados, "grupoNome", "PRODUTOS PARA CARRO", "quantidade"
        ),
        "Filtros": somar_por_criterio(
            dados,
            "grupoNome",
            ["FILTROS DE AR", "FILTROS DE COMBUSTÍVEL", "FILTROS DE OLEO"],
            "quantidade",
        ),
        "Troca de Óleo": somar_por_criterio(
            dados,
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
        "Vendas Loja": somar_por_criterio(
            dados,
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


# ── helpers de formatação ────────────────────────────────────────────────────

CURRENCY_KEYS = {"Vendas Pista", "Troca de Óleo", "Vendas Loja"}


def fmt_valor(chave, valor):
    if chave in CURRENCY_KEYS:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{valor:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_label(chave):
    return "R$" if chave in CURRENCY_KEYS else "un."


# ── cores ────────────────────────────────────────────────────────────────────

BG = "#0F1117"
SURFACE = "#1A1D27"
CARD = "#22263A"
ACCENT = "#F5A623"
ACCENT2 = "#4FC3F7"
TEXT = "#E8EAF0"
MUTED = "#6B7280"
SUCCESS = "#34D399"
DANGER = "#F87171"
BORDER = "#2E3247"
MONO = "Courier New"


# ── helpers de layout ─────────────────────────────────────────────────────────


def pad(h=0, v=0):
    return ft.Padding(left=h, right=h, top=v, bottom=v)


def margin_bottom(b):
    return ft.Margin(left=0, right=0, top=0, bottom=b)


def margin_h(h):
    return ft.Margin(left=h, right=h, top=0, bottom=0)


def margin_v(v):
    return ft.Margin(left=0, right=0, top=v, bottom=v)


# ── componentes ──────────────────────────────────────────────────────────────


def header():
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            "MAPA DE DESEMPENHO",
                            size=22,
                            weight=ft.FontWeight.W_900,
                            color=ACCENT,
                            font_family=MONO,
                        ),
                        ft.Text(
                            "Sistema de Relatórios de Filial",
                            size=12,
                            color=MUTED,
                        ),
                    ],
                    spacing=2,
                ),
                ft.Container(
                    content=ft.Text("●", color=SUCCESS, size=10),
                    padding=pad(h=10, v=5),
                    border=ft.border.all(1, SUCCESS),
                    border_radius=4,
                    tooltip="Sistema online",
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding(left=28, right=28, top=20, bottom=20),
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
    )


def make_textfield(value="", hint="", keyboard=ft.KeyboardType.TEXT):
    return ft.TextField(
        value=value,
        hint_text=hint,
        keyboard_type=keyboard,
        text_style=ft.TextStyle(color=TEXT, font_family=MONO, size=14),
        hint_style=ft.TextStyle(color=BORDER, size=13),
        border_color=BORDER,
        focused_border_color=ACCENT,
        fill_color=CARD,
        filled=True,
        border_radius=6,
        height=46,
        content_padding=pad(h=14, v=12),
    )


def labeled_field(label, control):
    return ft.Column(
        controls=[
            ft.Text(label, size=11, color=MUTED, font_family=MONO),
            control,
        ],
        spacing=6,
    )


def divider_line():
    return ft.Container(height=1, bgcolor=BORDER, margin=margin_v(8))


def resultado_card(chave, valor):
    is_currency = chave in CURRENCY_KEYS
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Column(
                    controls=[
                        ft.Text(
                            chave.upper(),
                            size=10,
                            color=MUTED,
                            font_family=MONO,
                        ),
                        ft.Text(
                            fmt_valor(chave, valor),
                            size=18,
                            weight=ft.FontWeight.W_700,
                            color=ACCENT if is_currency else ACCENT2,
                            font_family=MONO,
                        ),
                    ],
                    spacing=3,
                    expand=True,
                ),
                ft.Container(
                    content=ft.Text(
                        fmt_label(chave), size=9, color=MUTED, font_family=MONO
                    ),
                    padding=pad(h=8, v=4),
                    border=ft.border.all(1, BORDER),
                    border_radius=4,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=pad(h=16, v=14),
        bgcolor=CARD,
        border=ft.border.all(1, BORDER),
        border_radius=8,
        margin=margin_bottom(8),
    )


# ── app ───────────────────────────────────────────────────────────────────────


def main(page: ft.Page):
    page.title = "Mapa de Desempenho"
    page.bgcolor = BG
    page.padding = 0
    page.window.width = 520
    page.window.height = 820
    page.window.resizable = True
    page.scroll = ft.ScrollMode.ADAPTIVE

    today = date.today()
    first_day = today.replace(day=1)

    # campos de data
    tf_ini = make_textfield(
        first_day.strftime("%Y-%m-%d"),
        "AAAA-MM-DD",
        keyboard=ft.KeyboardType.DATETIME,
    )
    tf_fim = make_textfield(
        today.strftime("%Y-%m-%d"),
        "AAAA-MM-DD",
        keyboard=ft.KeyboardType.DATETIME,
    )

    # dropdown de postos
    dd_posto = ft.Dropdown(
        options=[
            ft.dropdown.Option(key=codigo, text=f"{nome}  ·  {codigo}")
            for nome, codigo in POSTOS
        ],
        value=POSTOS[0][1],  # seleciona o primeiro por padrão
        text_style=ft.TextStyle(color=TEXT, font_family=MONO, size=14),
        border_color=BORDER,
        focused_border_color=ACCENT,
        fill_color=CARD,
        filled=True,
        border_radius=6,
        height=46,
        content_padding=pad(h=14, v=4),
        # texto da opção selecionada
        color=TEXT,
    )

    # estado da UI
    status_text = ft.Text("", size=12, color=MUTED, font_family=MONO)
    resultados_col = ft.Column(spacing=0, visible=False)
    progress = ft.ProgressBar(color=ACCENT, bgcolor=BORDER, visible=False, height=2)

    btn_gerar = ft.Button(
        content=ft.Text(
            "GERAR RELATÓRIO",
            font_family=MONO,
            weight=ft.FontWeight.W_900,
            size=13,
            color="#000000",
        ),
        style=ft.ButtonStyle(
            bgcolor=ACCENT,
            overlay_color=ft.Colors.with_opacity(0.15, "#000000"),
            shape=ft.RoundedRectangleBorder(radius=6),
        ),
        height=48,
        expand=True,
    )

    # ── validação ─────────────────────────────────────────────────────────────

    def validar():
        erros = []
        for tf, nome in [(tf_ini, "Data inicial"), (tf_fim, "Data final")]:
            v = (tf.value or "").strip()
            if not v:
                erros.append(f"{nome} é obrigatório")
            else:
                try:
                    datetime.strptime(v, "%Y-%m-%d")
                except ValueError:
                    erros.append(f"{nome}: formato inválido (use AAAA-MM-DD)")
        if not dd_posto.value:
            erros.append("Selecione um posto")
        return erros

    # ── handler ───────────────────────────────────────────────────────────────

    def on_gerar(e):
        erros = validar()
        if erros:
            status_text.value = "⚠ " + " · ".join(erros)
            status_text.color = DANGER
            resultados_col.visible = False
            page.update()
            return

        btn_gerar.disabled = True
        progress.visible = True
        status_text.value = "Buscando dados..."
        status_text.color = MUTED
        resultados_col.visible = False
        page.update()

        # nome legível do posto selecionado
        nome_posto = next((n for n, c in POSTOS if c == dd_posto.value), dd_posto.value)

        try:
            dados = gerar_relatorio_filial(
                tf_ini.value.strip(),
                tf_fim.value.strip(),
                dd_posto.value,
            )

            resultados_col.controls.clear()
            resultados_col.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        "RESULTADO",
                                        size=11,
                                        color=MUTED,
                                        font_family=MONO,
                                    ),
                                    ft.Text(
                                        f"{tf_ini.value}  →  {tf_fim.value}",
                                        size=11,
                                        color=MUTED,
                                        font_family=MONO,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            ft.Text(
                                nome_posto.upper(),
                                size=13,
                                weight=ft.FontWeight.W_700,
                                color=ACCENT,
                                font_family=MONO,
                            ),
                        ],
                        spacing=4,
                    ),
                    margin=margin_bottom(12),
                )
            )
            for chave, valor in dados.items():
                resultados_col.controls.append(resultado_card(chave, valor))

            resultados_col.visible = True
            status_text.value = f"✓ {len(dados)} indicadores carregados"
            status_text.color = SUCCESS

        except httpx.HTTPStatusError as ex:
            status_text.value = f"✗ Erro HTTP {ex.response.status_code}"
            status_text.color = DANGER
        except Exception as ex:
            status_text.value = f"✗ {ex}"
            status_text.color = DANGER
        finally:
            btn_gerar.disabled = False
            progress.visible = False
            page.update()

    btn_gerar.on_click = on_gerar

    # ── layout ────────────────────────────────────────────────────────────────

    form_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text(
                    "PARÂMETROS",
                    size=11,
                    color=MUTED,
                    font_family=MONO,
                ),
                divider_line(),
                ft.Row(
                    controls=[
                        labeled_field("DATA INICIAL", tf_ini),
                        labeled_field("DATA FINAL", tf_fim),
                    ],
                    spacing=12,
                    expand=True,
                ),
                labeled_field("POSTO", dd_posto),
                ft.Container(height=4),
                ft.Row(controls=[btn_gerar]),
                progress,
                status_text,
            ],
            spacing=14,
        ),
        padding=20,
        bgcolor=SURFACE,
        border=ft.border.all(1, BORDER),
        border_radius=10,
        margin=margin_h(20),
    )

    results_container = ft.Container(
        content=resultados_col,
        padding=ft.Padding(left=20, right=20, top=4, bottom=4),
    )

    page.add(
        header(),
        ft.Container(height=20),
        form_card,
        ft.Container(height=16),
        results_container,
        ft.Container(height=20),
    )


ft.run(main)
