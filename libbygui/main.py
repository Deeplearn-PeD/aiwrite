import flet as ft
from libbydbot.brain import LibbyDBot
from libbygui.workflow import Workflow
import sys
import copy


def build_appbar(page):
    def save_file(e):
        txt = page.text_field.value
        page.file_picker.save_file(dialog_title="Save manscript as", file_name="manuscript.md",
                                   file_type=ft.FilePickerFileType.ANY)


    appbar = ft.AppBar(
        leading=ft.Icon(ft.icons.TEXT_SNIPPET_ROUNDED),
        leading_width=40,
        title=ft.Text("Writing Desk"),
        center_title=False,
        bgcolor=ft.colors.SURFACE_VARIANT,
        adaptive=True,
        toolbar_height=80,
        actions=[
            ft.IconButton(ft.icons.SAVE, tooltip="Export Manuscript", on_click=save_file),
            ft.IconButton(ft.icons.EXIT_TO_APP, tooltip="Exit My First Draft",
                          on_click=lambda e: page.window_destroy()),
            ft.Dropdown(
                value='Llama',
                width=150,
                label="Model",
                tooltip="Select the AI model to use for writing",
                options=[
                    ft.dropdown.Option("GPT"),
                    ft.dropdown.Option("Gemma"),
                    ft.dropdown.Option("Llama"),
                ],
                on_change=lambda e: page.client_storage.set("model", e.control.value.lower())
            ),

        ],
    )
    return appbar


def build_navigation_bar(page):
    navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationDestination(icon=ft.icons.DOCUMENT_SCANNER_OUTLINED, label="Manuscripts"),
            ft.NavigationDestination(icon=ft.icons.EDIT_DOCUMENT, label="Edit"),
            ft.NavigationDestination(icon=ft.icons.BOOK, label="Knowledge", tooltip="Knowledge Base", disabled=True),
            ft.NavigationDestination(icon=ft.icons.COFFEE, label="Review", tooltip="Review your text", disabled=True),
        ],
        on_change=lambda e: page.go(
            '/' + e.control.destinations[e.control.selected_index].label.lower().replace(" ", "_"))
    )
    return navigation_bar


def build_manuscript_card(page):
    pr = ft.ProgressRing(value=0)
    def add_section(e):
        man = WKF.add_section(page.client_storage.get("manid"), page.client_storage.get("section"))
        pr.value = 50; page.update()
        page.text_field.value = WKF.get_manuscript_text(page.client_storage.get("manid"))
        page.md.value = page.text_field.value
        pr.value = 100; page.update()
        pr.value = 0
        page.update()

    def enhance_text(e):
        man = WKF.enhance_section(page.client_storage.get("manid"), page.client_storage.get("section"))
        page.text_field.value = WKF.get_manuscript_text(page.client_storage.get("manid"))
        page.md.value = page.text_field.value
        page.update()


    card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    build_markdown_editor(page),
                    ft.Row(
                        [
                            pr,
                            ft.Dropdown(
                                value='Introduction',
                                width=150,
                                label="Section",
                                options=[
                                    ft.dropdown.Option("Abstract"),
                                    ft.dropdown.Option("Introduction"),
                                    ft.dropdown.Option("Methods"),
                                    ft.dropdown.Option("Discussion"),
                                    ft.dropdown.Option("Conclusion"),
                                ],
                                on_change=lambda e: page.client_storage.set("section", e.control.value.lower())
                            ),
                            ft.TextButton("Generate", on_click=add_section),
                            ft.TextButton("Enhance", on_click=enhance_text),
                            ft.TextButton("Criticize")
                         ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            # width=400,
            padding=10,
        ),
        # height=page.window_height,
        # expand=True
    )
    return card


def build_manuscript_list(page):
    mlist = ft.Card(
        content=ft.Container(
            content=ft.Column([]),
            # width=400,
            padding=ft.padding.symmetric(vertical=10),
        )
    )
    for man in WKF.get_man_list(100):
        mlist.content.content.controls.append(
            ft.ListTile(
                leading=ft.Icon(ft.icons.FILE_OPEN),
                title=ft.Text(f'{man.id}. {man.title}'),
                on_click=lambda e: load_manuscript(page, e)
            )
        )
    return mlist


def build_markdown_editor(page: ft.Page) -> ft.Row:
    """
    Builds a markdown editor with a live preview.
    :param page:
    """
    page.md = ft.Markdown(
        value="",
        selectable=True,
        expand=True,
        extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,

    )

    def md_update(e):
        # print('text changed')
        page.md.value = page.text_field.value
        page.update()


    page.text_field = ft.TextField(
        value="# Title\n\n",
        multiline=True,
        on_change=md_update,
        expand=True,
        # height=page.window_height,
        keyboard_type=ft.KeyboardType.TEXT,
        bgcolor=ft.colors.WHITE,
        border_color=ft.colors.GREY,
        text_vertical_align=-1
    )

    editor = ft.Row(
        [
            page.text_field,
            ft.VerticalDivider(width=10, thickness=5, color=ft.colors.RED_ACCENT_700, visible=True),
            # page.md,
            ft.Container(
                page.md,
                expand=True,
                alignment=ft.alignment.top_left,
                padding=ft.padding.Padding(12, 12, 12, 0),
                bgcolor=ft.colors.SURFACE_VARIANT,
            )
        ],
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    return editor


def load_manuscript(page, e):
    manid = int(e.control.title.value.split('.')[0])
    page.client_storage.set("manid", manid)
    txt = WKF.get_manuscript_text(manid)
    page.text_field.value = txt
    page.text_field.on_change(None)
    # print(f'Title: {page.text_field.value[:20]}')
    page.go('/edit')


def main(page: ft.Page):
    page.adaptive = True
    page.title = "My First Draft"
    page.scroll = "adaptive"
    page.client_storage.set("model", "llama")
    page.client_storage.set("section", "introduction")
    page.client_storage.set("manid", 1)
    page.appbar = build_appbar(page)
    nav_bar = build_navigation_bar(page)
    page.theme = ft.Theme(color_scheme_seed="green")
    page.update()

    def file_save(e: ft.FilePickerResultEvent):
        if e.file:
            with open(e.file, 'w') as f:
                f.write(page.text_field.value)

    page.file_picker = ft.FilePicker(on_result=file_save)
    page.overlay.append(page.file_picker)
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
                scroll=ft.ScrollMode.AUTO
            )
        )
        if page.client_storage.contains_key("manid"):
            manid = page.client_storage.get("manid")
            page.text_field.value = WKF.get_manuscript_text(manid)
            page.text_field.on_change(None)

        if page.route == "/manuscripts":
            page.views.append(
                ft.View(
                    "/manuscripts",
                    [
                        page.appbar,
                        build_manuscript_list(page),
                        nav_bar
                    ],
                    scroll=ft.ScrollMode.AUTO
                )
            )
        page.text_field.value = WKF.get_manuscript_text(manid)
        page.update()

    def write_man(e):
        if not context.value:
            context.error_text = "Please enter the initial concept of your manuscript."
            page.update()
        else:
            # prog = ft.ProgressRing(), ft.Text("This may take a while...")
            page.add(ft.ProgressRing(), ft.Text("Generating the text..."))
            # page.update()
            page.client_storage.set("context", context.value)
            WKF.set_model(page.client_storage.get("model"))

            man = WKF.setup_manuscript(context.value)
            editor.value = man.title + "\n\n" + man.abstract
            page.text_field.on_change(None)
            page.update()

    context = ft.TextField(label="Manuscript concept", multiline=True, min_lines=4)
    write_button = ft.ElevatedButton("Write", on_click=write_man)
    manuscript_card = build_manuscript_card(page)
    editor = manuscript_card.content.content.controls[0].controls[0]

    # print(editor)
    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    # page.add(context, write_button, response_card)
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.route = "/edit"
    page.go(page.route)


WKF = Workflow()


def run():
    # ft.app(target=main)
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
