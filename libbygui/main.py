import flet as ft
from libbydbot.brain import LibbyDBot
from libbygui.workflow import Workflow
import sys
import copy
import dotenv

dotenv.load_dotenv()


def build_appbar(page):
    def save_file(e):
        txt = page.text_field.value
        page.file_picker.save_file(dialog_title="Save manscript as", file_name="manuscript.md",
                                   file_type=ft.FilePickerFileType.ANY)
    
    def new_manuscript(e):
        page.client_storage.set("manid", -1)
        page.text_field.value = ""
        page.context.value = ""
        WKF.update_from_text(page.client_storage.get("manid"), page.text_field.value)
        page.write_button.disabled = False
        page.go("/edit")

    appbar = ft.AppBar(
        leading=ft.Icon(ft.Icons.TEXT_SNIPPET_ROUNDED),
        leading_width=40,
        title=ft.Text("Writing Desk"),
        center_title=False,
        bgcolor=ft.Colors.AMBER_300,
        adaptive=True,
        toolbar_height=80,
        actions=[
            ft.IconButton(ft.Icons.NOTE_ADD, tooltip="New Manuscript", on_click=new_manuscript),
            ft.IconButton(ft.Icons.SAVE, tooltip="Export Manuscript", on_click=save_file),
            ft.IconButton(ft.Icons.EXIT_TO_APP, tooltip="Exit Ai Write",
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
            ft.NavigationBarDestination(icon=ft.Icons.EDIT_DOCUMENT, label="Edit"),
            ft.NavigationBarDestination(icon=ft.Icons.DOCUMENT_SCANNER_OUTLINED, label="Manuscripts"),
            ft.NavigationBarDestination(icon=ft.Icons.BOOK, label="Knowledge"),# tooltip="Knowledge Base"),
            ft.NavigationBarDestination(icon=ft.Icons.COFFEE, label="Review", tooltip="Review your text", disabled=False),
        ],
        on_change=lambda e: page.go(
            '/' + e.control.destinations[e.control.selected_index].label.lower().replace(" ", "_"))
    )
    return navigation_bar


def build_manuscript_card(page):
    pr = ft.ProgressRing(value=0)

    def add_section(e):
        man = WKF.add_section(page.client_storage.get("manid"), page.client_storage.get("section"))
        pr.value = 50;
        page.update()
        page.text_field.value = WKF.get_manuscript_text(page.client_storage.get("manid"))
        page.md.value = page.text_field.value
        pr.value = 100;
        page.update()
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
                            ft.TextButton("Generate", on_click=add_section,
                                          tooltip=f"Generate the {page.client_storage.get('section')} section"),
                            ft.TextButton("Enhance", on_click=enhance_text,
                                          tooltip=f"Enhance the {page.client_storage.get('section')} section"),
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


def build_manuscript_review_card(page):
    pr = ft.ProgressRing(value=0)
    review = ft.Text("Crítica ", color="red", expand=True)

    def on_criticize(e):
        critic = WKF.criticize_section(page.client_storage.get("manid"), page.client_storage.get("section"))
        pr.value = 100
        review.value = critic
        page.update()

    card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            review,
                            ft.Markdown(
                                value=WKF.get_manuscript_text(page.client_storage.get("manid")),
                                expand=True,
                                extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                    ),

                    ft.Row(
                        [
                            pr,
                            ft.TextButton("Criticize", on_click=on_criticize,
                                          tooltip=f"Criticize the {page.client_storage.get('section')} section"),
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
                leading=ft.Icon(ft.Icons.FILE_OPEN),
                title=ft.Text(f'{man.id}. {man.title}'),
                subtitle=ft.Text(f'Last updated: {man.last_updated.strftime("%Y-%m-%d %H:%M")}'),
                on_click=lambda e: load_manuscript(page, e),
                trailing=ft.IconButton(
                    ft.Icons.DELETE_OUTLINE,
                    icon_color="red",
                    data=man.id,
                    tooltip="Delete manuscript",
                    on_click=lambda e: delete_manuscript(e, e.control.data, page)
                )
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
        if page.text_field.value:
            WKF.update_from_text(page.client_storage.get("manid"), page.text_field.value)
        page.update()

    page.text_field = ft.TextField(
        value="# Title\n\n",
        multiline=True,
        on_change=md_update,
        on_click=md_update,
        expand=True,
        # height=page.window_height,
        keyboard_type=ft.KeyboardType.TEXT,
        bgcolor=ft.Colors.WHITE,
        border_color=ft.Colors.GREY,
        text_vertical_align=-1,
        label="Editor",
        tooltip="Edit your manuscript here."
    )

    editor = ft.Row(
        [
            page.text_field,
            ft.VerticalDivider(width=10, thickness=5, color=ft.Colors.RED_ACCENT_700, visible=True),
            # page.md,
            ft.Container(
                page.md,
                expand=True,
                alignment=ft.alignment.top_left,
                padding=ft.padding.Padding(12, 12, 12, 0),
                bgcolor=ft.Colors.AMBER_300,
            )
        ],
        vertical_alignment=ft.CrossAxisAlignment.START,
    )

    return editor


def delete_manuscript(e, manid, page):
    WKF.delete_manuscript(manid)
    page.go('/manuscripts')
    page.update()

def load_manuscript(page, e):
    manid = int(e.control.title.value.split('.')[0])
    page.client_storage.set("manid", manid)
    txt = WKF.get_manuscript_text(manid)
    page.text_field.value = txt
    page.text_field.on_change(None)
    WKF.update_from_text(page.client_storage.get("manid"), page.text_field.value)
    page.write_button.disabled = True
    page.go('/edit')

def build_knowledge_page(page):
    # List to store uploaded files
    uploaded_files = []
    files_column = ft.Column(scroll=ft.ScrollMode.AUTO)

    def handle_upload_result(e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                # Create a list tile for each uploaded file
                file_tile = ft.ListTile(
                    leading=ft.Icon(ft.Icons.PICTURE_AS_PDF),
                    title=ft.Text(f.name),
                    trailing=ft.IconButton(
                        ft.icons.DELETE_OUTLINE,
                        icon_color="red",
                        data=f.name,
                        on_click=lambda e: remove_file(e, e.control.data)
                    ),
                )
                files_column.controls.append(file_tile)
                uploaded_files.append(f.name)
                page.update()

    def remove_file(e, filename):
        # Find and remove the list tile for this file
        for control in files_column.controls[:]:
            if control.title.value == filename:
                files_column.controls.remove(control)
                uploaded_files.remove(filename)
                page.update()
                break

    # Create file picker
    pick_files_dialog = ft.FilePicker(on_result=handle_upload_result)

    # Add file picker to overlay
    page.overlay.append(pick_files_dialog)

    # Create upload button
    upload_button = ft.ElevatedButton(
        "Upload PDF Files",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=lambda _: pick_files_dialog.pick_files(
            allow_multiple=True,
            allowed_extensions=["pdf"]
        )
    )

    # Create the main container for the knowledge page
    return ft.Container(
        content=ft.Column([
            ft.Text("Knowledge Base", size=20, weight=ft.FontWeight.BOLD),
            upload_button,
            ft.Divider(),
            ft.Text("Uploaded Files:", size=16),
            files_column,
        ]),
        padding=20
    )


def main(page: ft.Page):
    page.adaptive = True
    page.title = "AI Write"
    page.scroll = "adaptive"
    page.client_storage.set("model", "llama3")
    page.client_storage.set("section", "introduction")
    page.client_storage.set("manid", WKF.get_most_recent_id())
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
                    page.context,
                    page.write_button,
                    manuscript_card,
                    nav_bar
                ],
                scroll=ft.ScrollMode.AUTO
            )
        )
        if page.client_storage.contains_key("manid"):
            manid = page.client_storage.get("manid")
            if manid == -1:
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
        elif page.route == "/review":
            page.views.append(
                ft.View(
                    "/review",
                    [
                        page.appbar,
                        build_manuscript_review_card(page),
                        nav_bar
                    ],
                    scroll=ft.ScrollMode.AUTO
                )
            )
        elif page.route == "/knowledge":
            page.views.append(
                ft.View(
                    "/knowledge",
                    [
                        page.appbar,
                        build_knowledge_page(page),
                        nav_bar
                    ],
                    scroll=ft.ScrollMode.AUTO
                )
            )
        page.appbar.title.value = f"Writing Desk - {page.route.strip('/').capitalize()}"
        page.text_field.value = WKF.get_manuscript_text(manid)
        page.update()

    def write_man(e):
        if not page.context.value:
            page.context.error_text = "Please enter the initial concept of your manuscript."
            page.update()
            return
        else:
            # prog = ft.ProgressRing(), ft.Text("This may take a while...")
            page.add(ft.ProgressRing(), ft.Text("Generating the text..."))
            # page.update()
            page.client_storage.set("context", page.context.value)
            WKF.set_model(page.client_storage.get("model"))

            man = WKF.setup_manuscript(page.context.value)
            editor.value = man.title + "\n\n" + man.abstract
            page.text_field.on_change(None)
            page.write_button.disabled = True
            page.update()

    page.context = ft.TextField(label="Manuscript concept", multiline=True, min_lines=4)
    page.write_button = ft.ElevatedButton("Write", on_click=write_man, tooltip="Generate a new manuscript")
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
    app = ft.app(target=main)
    # ft.app(target=main, view=ft.AppView.WEB_BROWSER)
if __name__ == "__main__":
    run()
