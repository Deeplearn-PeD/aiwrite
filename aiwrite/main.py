from typing import List, Any

import dotenv
import flet as ft

from aiwrite.workflow import Workflow, parse_manuscript_text, Project

dotenv.load_dotenv()


def build_appbar(page: ft.Page) -> ft.AppBar:
    """
     Build the application's top app bar with navigation controls.
    
    Args:
        page: The Flet page object to attach controls to
        
    Returns:
        ft.AppBar: Configured app bar with navigation buttons and model selector
    """

    def save_file(e):
        txt = page.text_field.value
        page.file_picker.save_file(dialog_title="Save manscript as", file_name="manuscript.md",
                                   file_type=ft.FilePickerFileType.ANY)

    # def change_model(e):
    #     page.client_storage.set("model", e.control.value.lower())
    #     page.WKF.set_model(e.control.value.lower())

    appbar = ft.AppBar(
        leading=ft.Icon(ft.Icons.TEXT_SNIPPET_ROUNDED),
        leading_width=40,
        title=ft.Text("Writing Desk"),
        center_title=False,
        bgcolor=ft.Colors.AMBER_300,
        adaptive=True,
        toolbar_height=80,
        actions=[
            ft.IconButton(ft.Icons.SAVE, tooltip="Export Manuscript", on_click=save_file),
            ft.IconButton(ft.Icons.EXIT_TO_APP, tooltip="Exit Ai Write",
                          on_click=lambda e: page.window.destroy()),
        ],
    )
    return appbar


def build_navigation_bar(page: ft.Page) -> ft.NavigationBar:
    """
    Build the bottom navigation bar for switching between app views.
    
    Args:
        page: The Flet page object to attach controls to
        
    Returns:
        ft.NavigationBar: Configured navigation bar with view destinations
    """
    navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.EDIT_DOCUMENT, label="Edit"),
            ft.NavigationBarDestination(icon=ft.Icons.BOOK, label="Knowledge"),
            ft.NavigationBarDestination(icon=ft.Icons.COFFEE, label="Review", disabled=False),
            ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Projects"),
        ],
        on_change=lambda e: page.go(
            '/' + e.control.destinations[e.control.selected_index].label.lower().replace(" ", "_"))
    )
    return navigation_bar


def build_manuscript_card(page: ft.Page) -> ft.Card:
    """
    Build the manuscript editing card with section controls and markdown editor.
    
    Args:
        page: The Flet page object to attach controls to
        
    Returns:
        ft.Card: Container with section controls and markdown editor
    """
    pr = ft.ProgressRing(value=0)

    def add_section(e):
        def handle_dialog(e):
            if not section_name.value:
                return
            page.client_storage.set("section", section_name.value.lower())
            page.dialog.open = False
            man = page.WKF.add_section(page.client_storage.get("manid"), section_name.value.lower())
            pr.value = 50
            page.update()
            page.text_field.value = page.WKF.get_manuscript_text(page.client_storage.get("manid"))
            page.md.value = page.text_field.value
            pr.value = 100
            page.update()
            pr.value = 0
            update_section_dropdown(page)
            page.update()

        section_name = ft.TextField(label="Section Name", autofocus=True)
        dialog = ft.AlertDialog(
            title=ft.Text("Add New Section"),
            content=section_name,
            actions=[
                ft.TextButton("Add", on_click=handle_dialog),
                ft.TextButton("Cancel", on_click=lambda e: setattr(page.dialog, "open", False))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dialog)
        # page.dialog.open = True
        page.update()

    def enhance_text(e):
        man = page.WKF.enhance_section(page.client_storage.get("manid"), page.client_storage.get("section"))
        page.text_field.value = page.WKF.get_manuscript_text(page.client_storage.get("manid"))
        page.md.value = page.text_field.value
        update_section_dropdown(page)
        page.update()

    # Create dropdown that we'll update dynamically
    page.section_dropdown = ft.Dropdown(
        width=150,
        label="Section",
        options=[],
        on_change=lambda e: page.client_storage.set("section", e.control.value.lower())
    )

    card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            pr,
                            page.section_dropdown,
                            ft.ElevatedButton("Generate", on_click=add_section,
                                              tooltip=f"Generate a new section"),
                            ft.ElevatedButton("Enhance", on_click=enhance_text,
                                              tooltip=f"Enhance the {page.client_storage.get('section')} section"),
                        ],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                    build_markdown_editor(page),
                ],
                scroll=ft.ScrollMode.AUTO,
            ),
            padding=10,
        )
    )

    return card


def get_sections_from_manuscript(page: ft.Page) -> List[str]:
    """
    Get section names from the current manuscript using parse_manuscript_text.
    
    Args:
        page: The Flet page object containing the current manuscript
        
    Returns:
        List[str]: List of section names in the manuscript
    """
    text = page.WKF.get_manuscript_text(page.client_storage.get("manid"))
    parsed = parse_manuscript_text(text)
    return list(parsed.keys())


def update_section_dropdown(page: ft.Page) -> None:
    """
    Update the section dropdown options based on current manuscript sections.
    
    Args:
        page: The Flet page object containing the current manuscript
    """
    sections = get_sections_from_manuscript(page)
    page.section_dropdown.options = [
        ft.dropdown.Option(section) for section in sections
    ]
    if sections:
        page.section_dropdown.value = sections[0]
        page.client_storage.set("section", sections[0].lower())
    else:
        page.section_dropdown.value = None
    try:
        page.section_dropdown.update()
    except AssertionError:  # Dropdown not in view
        pass


def build_manuscript_review_card(page: ft.Page) -> ft.Card:
    """
    Build the manuscript review card with section-by-section critique functionality.
    
    Args:
        page: The Flet page object to attach controls to
        
    Returns:
        ft.Card: Container with section editors and critique controls
    """
    # Get all sections from the current manuscript
    sections = page.WKF.get_manuscript_sections(page.client_storage.get("manid"))
    
    # Create a column to hold all section review controls
    review_controls = ft.Column(scroll=ft.ScrollMode.AUTO)
    
    # Create a review panel for each section
    for section_name, section_content in sections.items():
        # Create review result display
        review_result = ft.Text("", color="red", expand=True)
        
        # Create markdown editor for the section
        section_editor = ft.Markdown(
            value=section_content,
            selectable=True,
            expand=True,
            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
        )
        
        # Create review button and progress ring for this section
        review_progress = ft.ProgressRing(
            width=16,
            height=16,
            stroke_width=2,
            visible=False
        )

        def create_review_handler(section_name, review_result, progress):
            def on_criticize(e):
                # Show progress ring
                progress.visible = True
                page.update()
                
                # Get critique
                critic = page.WKF.criticize_section(
                    page.client_storage.get("manid"), 
                    section_name
                )
                
                # Update UI
                review_result.value = critic
                progress.visible = False
                page.update()
            return on_criticize
        
        # Add section controls to the column
        review_controls.controls.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text(f"Section: {section_name}", weight=ft.FontWeight.BOLD),
                        ft.Row([
                            section_editor,
                            ft.VerticalDivider(width=10),
                            ft.Column([
                                ft.Row([
                                    ft.ElevatedButton(
                                        "Review Section",
                                        icon=ft.Icons.COFFEE,
                                        on_click=create_review_handler(section_name, review_result, review_progress),
                                        tooltip=f"Review the {section_name} section"
                                    ),
                                    review_progress
                                ], spacing=10),
                                ft.Divider(),
                                review_result
                            ], width=300)
                        ])
                    ]),
                    padding=10
                )
            )
        )

    return ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Text("Manuscript Review", size=20, weight=ft.FontWeight.BOLD),
                review_controls
            ]),
            padding=20
        )
    )




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
            page.WKF.update_from_text(page.client_storage.get("manid"), page.text_field.value)
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


def delete_manuscript(e: ft.ControlEvent, manid: int, page: ft.Page) -> None:
    """
    Delete a manuscript and update the UI.
    
    Args:
        e: The control event that triggered the deletion
        manid: ID of the manuscript to delete
        page: The Flet page object to update
    """
    page.WKF.delete_manuscript(manid)
    page.go('/manuscripts')
    page.update()


def load_manuscript(page: ft.Page, e: ft.ControlEvent) -> None:
    """
    Load a manuscript into the editor.
    
    Args:
        page: The Flet page object to update
        e: The control event that triggered the load
    """
    manid = int(e.control.title.value.split('.')[0])
    page.client_storage.set("manid", manid)
    txt = page.WKF.get_manuscript_text(manid)
    page.text_field.value = txt
    page.text_field.on_change(None)
    page.WKF.update_from_text(page.client_storage.get("manid"), page.text_field.value)
    page.write_button.disabled = True
    page.go('/edit')

def load_manuscript_id(page, manid):
    """
    Load a manuscript into the editor.

    Args:
        page: The Flet page object to update
        e: The control event that triggered the load
    """
    page.client_storage.set("manid", manid)
    txt = page.WKF.get_manuscript_text(manid)
    page.text_field.value = txt
    page.text_field.on_change(None)
    page.WKF.update_from_text(page.client_storage.get("manid"), page.text_field.value)
    page.write_button.disabled = True



def build_settings_page(page: ft.Page) -> ft.Container:
    """Build the project settings page with project selection and configuration.
    
    Args:
        page: The Flet page object to attach controls to
        
    Returns:
        ft.Container: Configured settings interface
    """
    # Declare variables that need to be accessed by update_project_fields
    global project_name, project_title, documents_folder, language_dropdown, model_dropdown
    # Project selector
    project_dropdown = ft.Dropdown(
        label="Project",
        options=[
            ft.dropdown.Option(f"{proj.id}: {proj.name}")
            for proj in page.WKF.get_projects()
        ],
        value=str(page.client_storage.get("project_id") or ""),
        on_change=lambda e: update_project_fields(page, e.control.value.split(":")[0])
    )

    # Delete project handler
    def delete_project(e):
        if not page.WKF.current_project:
            return
            
        def confirm_delete(e):
            page.WKF.delete_project(page.WKF.current_project.id)
            page.dialog.open = False
            # Clear fields and reset to first project
            projects = page.WKF.get_projects()
            if projects:
                update_project_fields(page, str(projects[0].id))
            else:
                # No projects left - clear everything
                page.WKF.current_project = None
                project_name.value = ""
                project_title.value = ""
                documents_folder.value = ""
                language_dropdown.value = "en"
                model_dropdown.value = "llama3.2"
                page.client_storage.set("project_id", None)
                page.client_storage.set("manid", None)
                page.text_field.value = ""
                page.md.value = ""
            page.update()

        page.dialog = ft.AlertDialog(
            title=ft.Text(f"Delete '{page.WKF.current_project.name}'?"),
            content=ft.Text("This will permanently delete the project and its manuscript."),
            actions=[
                ft.TextButton("Delete", on_click=confirm_delete),
                ft.TextButton("Cancel", on_click=lambda e: setattr(page.dialog, "open", False))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.dialog.open = True
        page.update()

    # New project button
    def create_new_project(e):
        # Clear current manuscript state
        page.client_storage.set("manid", -1)
        page.text_field.value = ""
        page.md.value = ""
        page.context.value = ""
        
        # Create and save new project
        new_project = Project(name="New Project")
        saved_project = page.WKF.save_project(new_project)
        
        # Update UI
        project_dropdown.options.append(
            ft.dropdown.Option(f"{saved_project.id}: {saved_project.name}")
        )
        project_dropdown.value = f"{saved_project.id}: {saved_project.name}"
        update_project_fields(page, saved_project.id)
        page.update()

    # Project name field
    project_name = ft.TextField(
        label="Project Name",
        value=page.WKF.current_project.name if page.WKF.current_project else "",
        on_change=lambda e: update_project_field(page, "name", e.control.value)
    )
    
    # Initialize fields with current project data
    if page.WKF.current_project:
        project_name.value = page.WKF.current_project.name
        if page.WKF.current_project.manuscript_id:
            page.client_storage.set("manid", page.WKF.current_project.manuscript_id)

    # Project title display
    project_title = ft.TextField(
        label="Manuscript Title",
        value=parse_manuscript_text(page.WKF.get_manuscript_text(page.WKF.current_project.manuscript_id))['title'] 
              if page.WKF.current_project and page.WKF.current_project.manuscript_id else "",
        read_only=True
    )

    # Documents folder picker
    def handle_folder_pick(e: ft.FilePickerResultEvent):
        if e.path:
            update_project_field(page, "documents_folder", e.path)
            documents_folder.value = e.path
            page.update()

    folder_picker = ft.FilePicker(on_result=handle_folder_pick)
    page.overlay.append(folder_picker)

    documents_folder = ft.TextField(
        label="Documents Folder",
        value=page.WKF.current_project.documents_folder if page.WKF.current_project else "",
        read_only=True
    )

    # Language selector
    language_dropdown = ft.Dropdown(
        label="Language",
        value=page.WKF.current_project.language if page.WKF.current_project else "en",
        options=[
            ft.dropdown.Option("en", "English"),
            ft.dropdown.Option("pt", "Portuguese"),
            ft.dropdown.Option("es", "Spanish"),
        ],
        on_change=lambda e: update_project_field(page, "language", e.control.value)
    )

    # Model selector
    model_dropdown = ft.Dropdown(
        label="LLM Model",
        value=page.WKF.current_project.model if page.WKF.current_project else "llama3.2",
        options=[ft.dropdown.Option(text=m, key=m) for m in page.WKF.libby.llm.available_models],
        #     ft.dropdown.Option(text="OpenAI", key='gpt'),
        #     ft.dropdown.Option(text="Google", key='gemma2'),
        #     ft.dropdown.Option(text="Llama", key='llama3.2'),
        # ],
        on_change=lambda e: update_project_field(page, "model", e.control.value)
    )

    return ft.Container(
        content=ft.Column([
            ft.Text("Project Settings", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([
                project_dropdown,
                ft.IconButton(
                    ft.Icons.ADD,
                    on_click=create_new_project,
                    tooltip="Create new project"
                ),
                ft.IconButton(
                    ft.Icons.DELETE,
                    on_click=delete_project,
                    tooltip="Delete current project",
                    icon_color=ft.Colors.RED
                )
            ]),
            project_name,
            project_title,
            ft.Row([
                documents_folder,
                ft.ElevatedButton(
                    "Select Folder",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=lambda _: folder_picker.get_directory_path()
                ),
                ft.ElevatedButton(
                    "Re-scan Folder",
                    icon=ft.Icons.REFRESH,
                    on_click=lambda _: page.WKF.KB.embed_path(documents_folder.value) if documents_folder.value else None,
                    tooltip="Re-scan and re-embed documents in the selected folder"
                )
            ]),
            language_dropdown,
            model_dropdown,
        ], scroll=ft.ScrollMode.AUTO),
        padding=20
    )


def update_project_fields(page: ft.Page, project_id: str) -> None:
    """
    Load a project's settings and update all related fields in the UI.
    
    Args:
        page: The Flet page object to update
        project_id: ID of the project to load
    """
    # Access the global variables we need to update
    global project_name, manuscript_dropdown, documents_folder, language_dropdown, model_dropdown
    if not project_id:
        return

    # Load the project
    page.client_storage.set("project_id", int(project_id))
    page.WKF.current_project = page.WKF.get_project(int(project_id))
    
    # Update all fields in the settings page
    project = page.WKF.current_project
    if project:
        # Update project name
        project_name.value = project.name
        
        # Update project title
        if project.manuscript_id:
            project_title.value = parse_manuscript_text(page.WKF.get_manuscript_text(project.manuscript_id))['title']
        else:
            project_title.value = ""
        
        # Update documents folder
        documents_folder.value = project.documents_folder or ""
        
        # Update language
        language_dropdown.value = project.language
        
        # Update model
        model_dropdown.value = project.model
        
        # Handle manuscript loading/clearing
        if project.manuscript_id:
            # Load associated manuscript
            page.client_storage.set("manid", project.manuscript_id)
            txt = page.WKF.get_manuscript_text(project.manuscript_id)
            page.text_field.value = txt
            page.md.value = txt
            page.text_field.on_change(None)
            page.WKF.update_from_text(project.manuscript_id, txt)
            page.write_button.disabled = True
        else:
            # Clear editor if no manuscript
            page.client_storage.set("manid", -1)
            page.text_field.value = ""
            page.md.value = ""
            page.text_field.on_change(None)
            page.write_button.disabled = False
            
    page.update()


def update_project_field(page: ft.Page, field: str, value: Any) -> None:
    """
    Update a project field and save it to the database.
    
    Args:
        page: The Flet page object
        field: Name of the field to update
        value: New value for the field
    """
    if not page.WKF.current_project:
        return
    if field == "model":
        page.client_storage.set("model", value.lower())
        page.WKF.set_model(value.lower())
    elif field == "manuscript_id":
        load_manuscript_id(page, value)

    setattr(page.WKF.current_project, field, value)
    page.WKF.save_project(page.WKF.current_project)



def build_knowledge_page(page: ft.Page) -> ft.Container:
    """
    Build the knowledge base page for managing uploaded documents.
    
    Args:
        page: The Flet page object to attach controls to
        
    Returns:
        ft.Container: Configured knowledge base interface
    """
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
                        ft.Icons.DELETE_OUTLINE,
                        icon_color="red",
                        data=f.name,
                        on_click=lambda e: remove_file(e, e.control.data)
                    ),
                )
                files_column.controls.append(file_tile)
                page.WKF.embed_document(f.path)
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


def main(page: ft.Page) -> None:
    """
    Main application entry point that sets up the UI and routing.
    
    Args:
        page: The Flet page object to configure
    """
    page.adaptive = True
    page.title = "Writing Desk"
    page.window_title = "Writing Desk"
    page.scroll = "adaptive"
    # Initialize default settings
    page.client_storage.set("model", "llama3")
    page.client_storage.set("section", "introduction")
    page.client_storage.set("language", "en")
    page.client_storage.set("project_name", "My Manuscript Project")
    page.WKF = Workflow()
    # Load most recent project on startup
    most_recent_project_id = page.WKF.get_most_recent_project()
    page.client_storage.set('project_id', most_recent_project_id)
    if most_recent_project_id:
        page.WKF.current_project = page.WKF.get_project(most_recent_project_id)
        manid = page.WKF.get_project_manuscript(most_recent_project_id)
        page.client_storage.set("manid", manid)
        if manid:
            page.WKF.set_knowledge_base(collection_name=f"man_{most_recent_project_id}")
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
                page.text_field.value = page.WKF.get_manuscript_text(manid)
                page.text_field.on_change(None)

        if page.route == "/review":
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
        elif page.route == "/projects":
            page.views.append(
                ft.View(
                    "/projects",
                    [
                        page.appbar,
                        build_settings_page(page),
                        nav_bar
                    ],
                    scroll=ft.ScrollMode.AUTO
                )
            )
        # Update window title with project name if available
        project_name = ""
        if page.WKF.current_project:
            project_name = f" - {page.WKF.current_project.name}"
        page.appbar.title.value = f"Writing Desk{project_name} - {page.route.strip('/').capitalize()}"
        page.window_title = f"Writing Desk{project_name}"
        page.text_field.value = page.WKF.get_manuscript_text(manid)
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
            page.WKF.set_model(page.client_storage.get("model"))

            man = page.WKF.setup_manuscript(page.context.value)
            editor.value = man.source
            page.text_field.on_change(None)
            page.write_button.disabled = True
            page.update()

    page.context = ft.TextField(label="Manuscript concept", multiline=True, min_lines=4)
    page.write_button = ft.ElevatedButton("Initialize", on_click=write_man, tooltip="Generate a new manuscript")
    manuscript_card = build_manuscript_card(page)
    # Initialize dropdown with current manuscript sections after card is created
    update_section_dropdown(page)
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


def run() -> None:
    """
    Run the Flet application.
    """
    app = ft.app(target=main)
    # ft.app(target=main, view=ft.AppView.WEB_BROWSER)


if __name__ == "__main__":
    run()
