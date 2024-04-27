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
    navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.DOCUMENT_SCANNER_OUTLINED, label="Manuscripts"),
            ft.NavigationDestination(icon=ft.icons.EDIT_DOCUMENT, label="Edit"),
        ],
        on_change=lambda e: page.go(
            '/' + e.control.destinations[e.control.selected_index].label.lower().replace(" ", "_"))
    )
    return navigation_bar


def build_manuscript_card(page):
    card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    build_markdown_editor(page),
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


def build_manuscript_list(page):
    mlist = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [

                ]
            ),
            # width=400,
            padding=ft.padding.symmetric(vertical=10),
        )
    )
    for man in WKF.get_man_list(10):
        mlist.content.content.controls.append(
            ft.ListTile(
                leading=ft.Icon(ft.icons.FILE_OPEN),
                title=ft.Text(f'{man.id}. {man.title}'),
                on_click=lambda e: load_manuscript(page, man.id)
            )
        )
    return mlist


def build_markdown_editor(page):
    def md_update(e):
        md.value = e.control.value
        md.update()
    text_field = ft.TextField(
        value="",
        multiline=True,
        on_change=md_update,
        expand=True,
        height=page.window_height,
        keyboard_type=ft.KeyboardType.TEXT,
        bgcolor=ft.colors.WHITE,
        border_color=ft.colors.GREY
    )
    md = ft.Markdown(
        value="",
        selectable=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
    )
    editor = ft.Row(
        [
            text_field,
            ft.VerticalDivider(width=10, thickness=5, color=ft.colors.RED_ACCENT_700, visible=True),
            ft.Container(
                ft.Column(
                    [
                        md
                    ],
                    scroll=ft.ScrollMode.HIDDEN
                ),
                expand=True,
                alignment=ft.alignment.top_left,
                padding=ft.padding.Padding(0, 12, 0, 0),
                bgcolor=ft.colors.SURFACE_VARIANT,
            )
        ],
    )

    return editor


def load_manuscript(page, manid):
    page.client_storage.set("manid", manid)
    page.go('/edit')


def main(page: ft.Page):
    page.title = "Libby D. Bot"
    page.scroll = "adaptive"
    page.client_storage.set("model", "llama")
    page.appbar = build_appbar(page)
    nav_bar = build_navigation_bar(page)
    page.update()

    def route_change(route):
        # print(route)
        page.views.clear()
        page.views.append(
            ft.View(
                "/edit",
                [
                    page.appbar,
                    context,
                    write_button,
                    manuscript_card,
                    nav_bar
                ],
            )
        )
        if page.client_storage.contains_key("manid"):
            manid = page.client_storage.get("manid")
            manuscript_card.content.content.controls[0].value = WKF.get_manuscript_text(manid)
        if page.route == "/manuscripts":
            page.views.append(
                ft.View(
                    "/manuscripts",
                    [
                        page.appbar,
                        build_manuscript_list(page),
                        nav_bar
                    ]
                )
            )
        page.update()


    def write_man(e):
        if not context.value:
            context.error_text = "Please enter the initial concept of your manuscript."
            page.update()
        else:
            # prog = ft.ProgressRing(), ft.Text("This may take a while...")
            page.add(ft.ProgressRing(), ft.Text("This may take a while..."))
            # page.update()
            page.client_storage.set("context", context.value)
            WKF.set_model(page.client_storage.get("model"))

            man = WKF.setup_manuscript(context.value)
            manuscript_card.content.content.controls[0].value = man.title + "\n\n" + man.abstract
            manuscript_card.update()
            # page.remove(prog)

    context = ft.TextField(label="Manuscript concept", multiline=True, min_lines=4)
    write_button = ft.ElevatedButton("Write", on_click=write_man)
    manuscript_card = build_manuscript_card(page)
    editor = manuscript_card.content.content.controls[0].controls[0]
    print(editor)
    # page.add(context, write_button, response_card)
    page.on_route_change = route_change
    page.route = "/edit"
    page.go(page.route)


WKF = Workflow()


def run():
    ft.app(main)
