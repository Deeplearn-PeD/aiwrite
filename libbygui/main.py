import flet as ft
from libbydbot.brain import LibbyDBot
from libbygui.workflow import Workflow

def build_appbar(page):
    appbar = ft.AppBar(
        leading=ft.Icon(ft.icons.TEXT_SNIPPET_ROUNDED),
        leading_width=40,
        title=ft.Text("Libby"),
        center_title=False,
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[
            ft.IconButton(ft.icons.WB_SUNNY_OUTLINED),
            ft.Dropdown(
                value='Llama',
                width=150,
                label="Model",
                options=[
                    ft.dropdown.Option("ChatGPT"),
                    ft.dropdown.Option("Gemma"),
                    ft.dropdown.Option("Llama"),
                ],
                on_change=lambda e: page.client_storage.set("model", e.control.value)
            ),

        ],
    )
    return appbar

def build_navigation_bar(page):
    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.DOCUMENT_SCANNER_OUTLINED, label="My Manuscripts"),
            ft.NavigationDestination(icon=ft.icons.EDIT_DOCUMENT, label="Edit"),
        ]
    )
def build_response_card():
    card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Markdown(
                        value="",
                        selectable=True,
                        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    ),
                    ft.Row(
                        [ft.TextButton("Enhance"), ft.TextButton("Criticize")],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ]
            ),
            # width=400,
            padding=10,
        )
    )
    return card

def main(page: ft.Page):
    page.title = "Libby D. Bot"
    page.scroll = "adaptive"
    page.client_storage.set("model", "llama")

    page.appbar = build_appbar(page)
    build_navigation_bar(page)
    def write_man(e):
        if not context.value:
            context.error_text = "Please enter the initial concept of your manuscript."
            page.update()
        else:
            page.client_storage.set("context", context.value)
            WKF = Workflow(model=page.client_storage.get("model"))
            man = WKF.setup_manuscript(context.value)
            response_card.content.content.controls[0].value = man.title + "\n\n" + man.abstract
            response_card.update()


    context = ft.TextField(label="Manuscript concept", multiline=True, min_lines=4)

    response_card = build_response_card()
    page.add(context, ft.ElevatedButton("Write", on_click=write_man), response_card)

def run():
    ft.app(main)

