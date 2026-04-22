import json
import os
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

import flet as ft
import httpx

POSTOS = [
    ("GRACIOSA", "14526"),
    ("PIRAI", "14566"),
    ("JARIVA", "14562"),
    ("BEMER", "14564"),
    ("GRACIOSA V", "14565"),
    ("FATIMA", "14563"),
]

TIPOS_RELATORIO = [
    ("Relatório de Filial", "filial"),
    ("Relatório de Funcionários", "funcionarios"),
]

CONFIG_FILE = (
    Path(os.environ.get("APPDATA") or Path.home() / ".config")
    / "MapaDesempenho"
    / "config.json"
)


def _load_file_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))

    except Exception:
        return {}


def _save_file_config(data: dict):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

    CONFIG_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def cred_get(page: ft.Page, key: str) -> str:
    try:
        return page.client_storage.get(key) or ""

    except AttributeError:
        return _load_file_config().get(key, "")


def cred_set(page: ft.Page, key: str, value: str):
    try:
        page.client_storage.set(key, value)

    except AttributeError:
        cfg = _load_file_config()

        cfg[key] = value

        _save_file_config(cfg)


def has_creds(page: ft.Page) -> bool:
    return bool(cred_get(page, "wp_base_url") and cred_get(page, "wp_api_key"))


def buscar_dados_brutos(data_inicial, data_final, empresa_codigo, base_url, api_key):
    url = (
        f"{base_url}/INTEGRACAO/MAPA_DESEMPENHO"
        f"?CHAVE={api_key}&dataInicial={data_inicial}"
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


def _agregadores_de(dados):
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


def gerar_relatorio_filial(data_inicial, data_final, empresa_codigo, base_url, api_key):
    dados = buscar_dados_brutos(
        data_inicial, data_final, empresa_codigo, base_url, api_key
    )

    return _agregadores_de(dados)


def gerar_relatorio_funcionarios(
    data_inicial, data_final, empresa_codigo, base_url, api_key
):
    dados = buscar_dados_brutos(
        data_inicial, data_final, empresa_codigo, base_url, api_key
    )

    por_func: dict[str, list] = defaultdict(list)

    for item in dados:
        nome = item.get("funcionarioNome") or "SEM NOME"

        por_func[nome].append(item)

    return {
        nome: _agregadores_de(registros) for nome, registros in sorted(por_func.items())
    }


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

CURRENCY_KEYS = {"Vendas Pista", "Troca de Óleo", "Vendas Loja"}


def fmt_valor(chave, valor):
    if chave in CURRENCY_KEYS:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return f"{valor:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_label(chave):
    return "R$" if chave in CURRENCY_KEYS else "un."


def pad(h=0, v=0):
    return ft.Padding(left=h, right=h, top=v, bottom=v)


def margin_bottom(b):
    return ft.Margin(left=0, right=0, top=0, bottom=b)


def margin_h(h):
    return ft.Margin(left=h, right=h, top=0, bottom=0)


def margin_v(v):
    return ft.Margin(left=0, right=0, top=v, bottom=v)


def make_textfield(value="", hint="", keyboard=ft.KeyboardType.TEXT, password=False):
    return ft.TextField(
        value=value,
        hint_text=hint,
        keyboard_type=keyboard,
        password=password,
        can_reveal_password=password,
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


def make_dropdown(options_kv, value=None):
    return ft.Dropdown(
        options=[ft.dropdown.Option(key=k, text=t) for t, k in options_kv],
        value=value or options_kv[0][1],
        text_style=ft.TextStyle(color=TEXT, font_family=MONO, size=14),
        border_color=BORDER,
        focused_border_color=ACCENT,
        fill_color=CARD,
        filled=True,
        border_radius=6,
        height=46,
        content_padding=pad(h=14, v=4),
        color=TEXT,
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


def funcionario_section(nome, indicadores):
    cards = ft.Column(
        controls=[resultado_card(k, v) for k, v in indicadores.items()],
        spacing=0,
        visible=False,
    )

    chevron = ft.Text("▶", size=11, color=MUTED, font_family=MONO)

    def toggle(e):
        cards.visible = not cards.visible

        chevron.value = "▼" if cards.visible else "▶"

        e.control.page.update()

    header_row = ft.Container(
        content=ft.Row(
            controls=[
                ft.Text(
                    nome,
                    size=13,
                    weight=ft.FontWeight.W_600,
                    color=TEXT,
                    font_family=MONO,
                    expand=True,
                ),
                chevron,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=pad(h=16, v=12),
        bgcolor=SURFACE,
        border=ft.border.all(1, BORDER),
        border_radius=8,
        margin=margin_bottom(4),
        on_click=toggle,
        ink=True,
    )

    return ft.Column(controls=[header_row, cards], spacing=0)


def build_config_screen(page: ft.Page, on_save):
    tf_url = make_textfield(
        value=cred_get(page, "wp_base_url"),
        hint="https://api.exemplo.com",
        keyboard=ft.KeyboardType.URL,
    )

    tf_key = make_textfield(
        value=cred_get(page, "wp_api_key"),
        hint="sua-chave-secreta",
        password=True,
    )

    status = ft.Text("", size=12, color=DANGER, font_family=MONO)

    def salvar(e):
        url = (tf_url.value or "").strip().rstrip("/")

        key = (tf_key.value or "").strip()

        if not url or not key:
            status.value = "⚠ Preencha os dois campos"

            page.update()

            return

        cred_set(page, "wp_base_url", url)

        cred_set(page, "wp_api_key", key)

        on_save()

    btn = ft.Button(
        content=ft.Text(
            "SALVAR E CONTINUAR",
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
        on_click=salvar,
    )

    plataforma = (
        "arquivo em %APPDATA%\\MapaDesempenho\\config.json"
        if os.name == "nt"
        else "arquivo em ~/.config/MapaDesempenho/config.json"
    )

    return ft.Column(
        controls=[
            ft.Container(height=40),
            ft.Container(
                content=ft.Text(
                    "CONFIGURAÇÃO",
                    size=22,
                    weight=ft.FontWeight.W_900,
                    color=ACCENT,
                    font_family=MONO,
                ),
                padding=ft.Padding(left=28, right=28, top=0, bottom=20),
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "CREDENCIAIS DE ACESSO",
                            size=11,
                            color=MUTED,
                            font_family=MONO,
                        ),
                        divider_line(),
                        ft.Text(
                            f"Salvas localmente ({plataforma}). Nunca enviadas a terceiros.",
                            size=11,
                            color=MUTED,
                        ),
                        labeled_field("URL BASE DA API", tf_url),
                        labeled_field("CHAVE DA API", tf_key),
                        ft.Container(height=4),
                        ft.Row(controls=[btn]),
                        status,
                    ],
                    spacing=14,
                ),
                padding=20,
                bgcolor=SURFACE,
                border=ft.border.all(1, BORDER),
                border_radius=10,
                margin=margin_h(20),
            ),
        ],
        spacing=0,
    )


def build_main_screen(page: ft.Page, on_config):
    base_url = cred_get(page, "wp_base_url")

    api_key = cred_get(page, "wp_api_key")

    today = date.today()

    first_day = today.replace(day=1)

    tf_ini = make_textfield(
        first_day.strftime("%Y-%m-%d"), "AAAA-MM-DD", keyboard=ft.KeyboardType.DATETIME
    )

    tf_fim = make_textfield(
        today.strftime("%Y-%m-%d"), "AAAA-MM-DD", keyboard=ft.KeyboardType.DATETIME
    )

    dd_posto = make_dropdown(
        [(f"{n}  ·  {c}", c) for n, c in POSTOS], value=POSTOS[0][1]
    )

    dd_tipo = make_dropdown(TIPOS_RELATORIO)

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

        return erros

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

        nome_posto = next((n for n, c in POSTOS if c == dd_posto.value), dd_posto.value)

        try:
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

            if dd_tipo.value == "filial":
                dados = gerar_relatorio_filial(
                    tf_ini.value.strip(),
                    tf_fim.value.strip(),
                    dd_posto.value,
                    base_url,
                    api_key,
                )

                for chave, valor in dados.items():
                    resultados_col.controls.append(resultado_card(chave, valor))

                status_text.value = f"✓ {len(dados)} indicadores carregados"

            else:
                dados = gerar_relatorio_funcionarios(
                    tf_ini.value.strip(),
                    tf_fim.value.strip(),
                    dd_posto.value,
                    base_url,
                    api_key,
                )

                for nome_func, indicadores in dados.items():
                    resultados_col.controls.append(
                        funcionario_section(nome_func, indicadores)
                    )

                status_text.value = (
                    f"✓ {len(dados)} funcionários  ·  clique para expandir"
                )

            resultados_col.visible = True

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

    header_widget = ft.Container(
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
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text("●", color=SUCCESS, size=10),
                            padding=pad(h=10, v=5),
                            border=ft.border.all(1, SUCCESS),
                            border_radius=4,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SETTINGS_OUTLINED,
                            icon_color=MUTED,
                            icon_size=20,
                            tooltip="Alterar credenciais",
                            on_click=lambda e: on_config(),
                        ),
                    ],
                    spacing=8,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding(left=28, right=28, top=20, bottom=20),
        border=ft.border.only(bottom=ft.BorderSide(1, BORDER)),
    )

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
                labeled_field("TIPO DE RELATÓRIO", dd_tipo),
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

    return ft.Column(
        controls=[
            header_widget,
            ft.Container(height=20),
            form_card,
            ft.Container(height=16),
            ft.Container(
                content=resultados_col,
                padding=ft.Padding(left=20, right=20, top=4, bottom=4),
            ),
            ft.Container(height=20),
        ],
        spacing=0,
    )


def main(page: ft.Page):
    page.title = "Mapa de Desempenho"

    page.bgcolor = BG

    page.padding = 0

    page.window.width = 520

    page.window.height = 820

    page.window.resizable = True

    page.scroll = ft.ScrollMode.ADAPTIVE

    def show_config():
        page.controls.clear()

        page.add(build_config_screen(page, on_save=show_main))

        page.update()

    def show_main():
        page.controls.clear()

        page.add(build_main_screen(page, on_config=show_config))

        page.update()

    if has_creds(page):
        show_main()

    else:
        show_config()


ft.run(main)
