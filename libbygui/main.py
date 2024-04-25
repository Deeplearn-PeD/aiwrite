import flet as ft
from libbydbot.brain import LibbyDBot

def build_appbar():
    appbar = ft.AppBar(
        leading=ft.Icon(ft.icons.TEXT_SNIPPET_ROUNDED),
        leading_width=40,
        title=ft.Text("Libby"),
        center_title=False,
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[
            ft.IconButton(ft.icons.WB_SUNNY_OUTLINED),
            ft.Dropdown(
                width=150,
                label="Model",
                options=[
                    ft.dropdown.Option("ChatGPT"),
                    ft.dropdown.Option("Gemma"),
                    ft.dropdown.Option("Lamma"),
                ]),
            ft.PopupMenuButton(
                items=[
                    ft.PopupMenuItem(text="Item 1"),
                    ft.PopupMenuItem(),  # divider
                ]
            ),
        ],
    )
    return appbar

def build_response_card():
    card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.DOCUMENT_SCANNER),
                        title=ft.Text("Abstract"),
                        subtitle=ft.Text(
                            "First Draft."
                        ),
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

    page.appbar = build_appbar()
    def ask_libby(e):
        if not question.value:
            question.error_text = "Please enter a question"
            page.update()
        else:
            LDB = LibbyDBot(model='llama3')
            LDB.set_context("You are Libby D. Bot, a research Assistant, you should answer questions "
                           "based on the context provided.")
            response = LDB.ask(question.value)
            page.add(ft.Text(f"Libby says: {response}"))

    context = ft.TextField(label="Context", multiline=True, min_lines=5)
    question = ft.TextField(label="Question")
    response_card = build_response_card()
    page.add(context, question, ft.ElevatedButton("Ask Libby", on_click=ask_libby), response_card)

def run():
    ft.app(main)

