import flet as ft
from libbydbot.brain import LibbyDBot

def build_appbar():
    appbar = ft.AppBar(
        leading=ft.Icon(ft.icons.LIGHT),
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
            page.add(ft.Text("Libby says: I am still learning, but I think you should ask a librarian."))
            page.add(ft.Text(f"Libby says: {response}"))


    question = ft.TextField(label="Question")
    page.add(question, ft.ElevatedButton("Ask Libby", on_click=ask_libby))

def run():
    ft.app(main)

