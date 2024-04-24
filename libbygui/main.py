import flet as ft
from libbydbot.brain import LibbyDBot



def main(page: ft.Page):
    page.title = "Libby D. Bot"
    page.scroll = "adaptive"
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

