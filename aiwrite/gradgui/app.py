import json
import os
import traceback
from typing import List, Optional, Tuple

import gradio as gr

from aiwrite.workflow import Workflow, Project


class GradioAIWrite:
    def __init__(self, db_path):
        self.workflow = Workflow(model='gemini', dburl=f'sqlite:///{db_path}/aiwrite.db', 
                                 db_path=db_path,
                                 embedding_model="gemini-embedding-001"
                                 )
        self.db_path = db_path
        self.current_manuscript_id = None
        self.current_section = None
        self.available_models = self.workflow.libby.llm.available_models

        # Inicializar a base de conhecimento com uma coleção padrão
        try:
            self.workflow.set_knowledge_base("Literatura")  # ou qualquer nome padrão
        except Exception as e:
            print(f"Aviso: Não foi possível inicializar a base de conhecimento: {str(e)}")

    def get_manuscripts_list(self) -> List[Tuple[str, int]]:
        """Get list of manuscripts for dropdown"""
        manuscripts = self.workflow.get_man_list()
        return [(f"{m.id} - {m.source.split('\n')[0]}", m.id) for m in manuscripts]

    def get_projects_list(self) -> List[Tuple[str, int]]:
        """Get list of projects for dropdown"""
        projects = self.workflow.get_projects()
        return [(f"{p.name} (ID: {p.id})", p.id) for p in projects]

    def update_project_model(self, model: str) -> str:
        """Set the model for the workflow and save project"""
        try:
            self.workflow.set_model(model)
            # Update and save current project if exists
            if self.workflow.current_project:
                self.workflow.current_project.model = model
                self.workflow.save_project(self.workflow.current_project)
            return f"Modelo atualizado com sucesso para {model}!"
        except Exception as e:
            return f"Erro ao atualizar modelo: {str(e)}"

    def update_project_property(self, property_name: str, value: str) -> str:
        """Update a project property and save automatically"""
        if not self.workflow.current_project:
            return "Nenhum projeto carregado."

        try:
            setattr(self.workflow.current_project, property_name, value)
            self.workflow.save_project(self.workflow.current_project)
            return f"Propriedade '{property_name}' atualizada e salva com sucesso!"
        except Exception as e:
            return f"Erro ao atualizar propriedade: {str(e)}"

    def get_base_prompt(self) -> str:
        """Get current base prompt"""
        return self.workflow.base_prompt

    def update_base_prompt(self, new_prompt: str) -> str:
        """Update the base prompt for the workflow"""
        if not new_prompt.strip():
            return "Por favor, insira um prompt válido."

        try:
            self.workflow.base_prompt = new_prompt
            return "Prompt base atualizado com sucesso!"
        except Exception as e:
            return f"Erro ao atualizar prompt base: {str(e)}"

    def create_manuscript(self, concept: str, i18n: gr.I18n) -> Tuple[str, gr.Dropdown]:
        """Create new manuscript"""
        if not concept.strip():
            return i18n("enter_valid_concept"), gr.Dropdown()

        try:
            manuscript = self.workflow.setup_manuscript(concept)
            self.current_manuscript_id = manuscript.id
            manuscripts_list = self.get_manuscripts_list()
            return i18n("manuscript_created")+f" {manuscript.id}", gr.Dropdown(choices=manuscripts_list)
        except Exception as exc:
            tb = repr(traceback.format_exception(exc))
            manuscripts_list = self.get_manuscripts_list()
            return i18n("error_creating_manuscript")+ f": {tb}", gr.Dropdown(choices=manuscripts_list)

    def load_manuscript(self, manuscript_id: int, i18n: gr.I18n) -> Tuple[str, str, gr.Dropdown, gr.Dropdown]:
        """Load manuscript and return its content"""
        if not manuscript_id:
            return i18n("select_manuscript_msg"), "", gr.Dropdown(), gr.Dropdown()

        try:
            self.current_manuscript_id = manuscript_id
            manuscript = self.workflow.get_manuscript(manuscript_id)
            sections = self.workflow.get_manuscript_sections(manuscript_id)
            section_names = list(sections.keys())

            content = self.workflow.get_manuscript_text(manuscript_id)
            return (f"Manuscrito carregado: {manuscript.source.split('\n')[0]}", content,
                    gr.Dropdown(choices=section_names, value=section_names[0] if section_names else None),
                    gr.Dropdown(choices=section_names, value=section_names[0] if section_names else None)
                    )
        except Exception as e:
            return i18n("error_loading_manuscript") + str(e), "", gr.Dropdown(), gr.Dropdown()

    def add_section(self, section_name: str, i18n: gr.I18n) -> Tuple[str, str]:
        """Add new section to current manuscript"""
        if not self.current_manuscript_id:
            return "Nenhum manuscrito selecionado."

        if not section_name.strip():
            return "Por favor, insira um nome para a seção."

        try:
            manuscript = self.workflow.add_section(self.current_manuscript_id, section_name.lower())

            self.load_manuscript(manuscript_id=manuscript.id, i18n=i18n)
            return f"Seção '{section_name}' adicionada com sucesso!", manuscript.source
        except Exception as e:
            return f"Erro ao adicionar seção: {str(e)}", manuscript.source

    def enhance_section(self, section_name: str) -> str:
        """Enhance existing section"""
        if not self.current_manuscript_id:
            return "Nenhum manuscrito selecionado."

        if not section_name:
            return "Selecione uma seção."

        try:
            self.workflow.enhance_section(self.current_manuscript_id, section_name)
            content = self.workflow.get_manuscript_text(self.current_manuscript_id)
            return content
        except Exception as e:
            return f"Erro ao melhorar seção: {str(e)}"

    def criticize_section(self, section_name: str) -> str:
        """Get critique for a section"""
        if not self.current_manuscript_id:
            return "Nenhum manuscrito selecionado."

        if not section_name:
            return "Selecione uma seção."

        try:
            critique = self.workflow.criticize_section(self.current_manuscript_id, section_name)
            return critique
        except Exception as e:
            return f"Erro ao criticar seção: {str(e)}"

    def update_manuscript_text(self, text: str) -> str:
        """Update manuscript with new text"""
        if not self.current_manuscript_id:
            return "Nenhum manuscrito selecionado."

        try:
            self.workflow.update_from_text(self.current_manuscript_id, text)
            return "Manuscrito atualizado com sucesso!"
        except Exception as e:
            return f"Erro ao atualizar manuscrito: {str(e)}"

    def download_manuscript(self) -> Tuple[str, Optional[str]]:
        """Prepare manuscript for download as markdown file"""
        if not self.current_manuscript_id:
            return "Nenhum manuscrito selecionado.", None

        try:
            manuscript = self.workflow.get_manuscript(self.current_manuscript_id)
            content = self.workflow.get_manuscript_text(self.current_manuscript_id)
            
            # Create filename from manuscript title/concept
            title = manuscript.source.split('\n')[0].strip()
            # Clean filename - remove invalid characters
            import re
            filename = re.sub(r'[^\w\s-]', '', title).strip()
            filename = re.sub(r'[-\s]+', '-', filename)
            filename = f"manuscrito-{self.current_manuscript_id}-{filename}.md"
            
            # Write content to temporary file
            import tempfile
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
            temp_file.write(content)
            temp_file.close()
            
            return f"Manuscrito preparado para download: {filename}", temp_file.name
        except Exception as e:
            return f"Erro ao preparar download: {str(e)}", None

    def delete_manuscript(self, manuscript_id: int) -> Tuple[str, gr.Dropdown]:
        """Delete manuscript"""
        if not manuscript_id:
            return "Selecione um manuscrito para deletar.", gr.Dropdown()

        try:
            self.workflow.delete_manuscript(manuscript_id)
            manuscripts_list = self.get_manuscripts_list()
            if manuscript_id == self.current_manuscript_id:
                self.current_manuscript_id = None
            return "Manuscrito deletado com sucesso!", gr.Dropdown(choices=manuscripts_list)
        except Exception as e:
            return f"Erro ao deletar manuscrito: {str(e)}", gr.Dropdown()

    def create_project(self, name: str, language: str, model: str) -> Tuple[str, gr.Dropdown]:
        """Create new project"""
        if not name.strip():
            return "Por favor, insira um nome para o projeto.", gr.Dropdown()

        try:
            project = Project(
                name=name,
                language=language,
                model=model,
                documents_folder="",
                manuscript_id=0
            )
            saved_project = self.workflow.save_project(project)
            projects_list = self.get_projects_list()
            return f"Projeto criado com sucesso! ID: {saved_project.id}", gr.Dropdown(choices=projects_list,
                                                                                      value=saved_project.id)
        except Exception as e:
            return f"Erro ao criar projeto: {str(e)}", gr.Dropdown()

    def load_project(self, project_id: int) -> Tuple[str, str, str, str]:
        """Load existing project and return its details"""
        if not project_id:
            return "Selecione um projeto.", "", "", ""

        try:
            project = self.workflow.get_project(project_id)
            self.workflow.current_project = project
            return (
                f"Projeto carregado: {project.name}",
                project.name,
                project.language,
                project.model
            )
        except Exception as e:
            return f"Erro ao carregar projeto: {str(e)}", "", "", ""

    def get_embedded_documents(self) -> List[Tuple[str, str]]:
        """Get list of embedded documents from knowledge base"""
        try:
            # Garantir que a KB está inicializada
            if not hasattr(self.workflow, 'KB') or self.workflow.KB is None:
                self.workflow.set_knowledge_base("Literatura")

            doc_list = self.workflow.KB.get_embedded_documents()
            return doc_list if doc_list else []
        except Exception as e:
            print(f"Error getting embedded documents: {str(e)}")
            return []

    def get_collections_list(self) -> List[str]:
        """Get list of existing collections from knowledge base"""
        try:
            # Garantir que a KB está inicializada
            if not hasattr(self.workflow, 'KB') or self.workflow.KB is None:
                self.workflow.set_knowledge_base("Literatura")

            # Obter todas as coleções únicas dos documentos
            documents = self.workflow.KB.get_embedded_documents()
            collections = list(set([doc[1] for doc in documents if len(doc) > 1]))

            # Garantir que "Literatura" está sempre na lista
            if "Literatura" not in collections:
                collections.insert(0, "Literatura")

            return collections if collections else ["Literatura"]
        except Exception as e:
            print(f"Error getting collections: {str(e)}")
            return ["Literatura"]

    def refresh_documents_list(self) -> gr.Dataframe:
        """Refresh the documents list display"""
        documents = self.get_embedded_documents()
        df_data = [[doc] for doc in documents] if documents else []
        return gr.Dataframe(value=df_data, headers=["Nome", "Coleção"])

    def embed_document(self, file, collection_name: str) -> Tuple[str, gr.Dataframe]:
        """Embed document into knowledge base"""
        if not file:
            return "Selecione um arquivo.", gr.Dataframe()

        if not collection_name.strip():
            return "Por favor, especifique um nome para a coleção.", gr.Dataframe()

        try:
            # Set the knowledge base collection before embedding
            self.workflow.set_knowledge_base(collection_name.strip())
            self.workflow.embed_document(file.name)
            documents = self.get_embedded_documents()
            df_data = [[doc[0].split("/")[-1], doc[1]] for doc in documents] if documents else []
            return (
                f"Documento '{os.path.basename(file.name)}' incorporado com sucesso na coleção '{collection_name}'!",
                gr.Dataframe(value=df_data, headers=["Nome", "Coleção"], interactive=False, max_height=500))
        except Exception as e:
            df_data= locals().get('df_data', [])
            return f"Erro ao incorporar documento: {str(e)}", gr.Dataframe(value=df_data,
                                                                           headers=["Nome", "Coleção"],
                                                                           interactive=False,
                                                                           max_height=500
                                                                           )


def create_interface(db_path):
    app = GradioAIWrite(db_path=db_path)

    # Initialize I18n with locales
    i18n_path = 'locales' if os.path.exists('locales') else os.path.join(os.path.dirname(__file__), 'locales')
    locales = {f'{fn.split('.')[0]}': json.load(open(os.path.join(i18n_path, fn), 'r', encoding='utf-8')) for fn in
               os.listdir(i18n_path) if fn.endswith('.json')}
    i18n = gr.I18n(**locales)

    with gr.Blocks(title="AIWrite (Demo)",
                   theme=gr.themes.Glass(),
                   css="""
                   footer {visibility: hidden}
                   .markdown-preview-scroll {
                       max-height: 500px;
                       overflow-y: auto;
                       border: 1px solid #e0e0e0;
                       padding: 10px;
                       border-radius: 5px;
                   }
                   """
                   ) as interface:
        with gr.Row():
            with gr.Column(scale=20):
                gr.Markdown(f'# {i18n("title")} <a href="https://github.com/Deeplearn-PeD/aiwrite"><img src="https://twenty-icons.com/github.com/32"></a>')
            with gr.Column(scale=1):
                language_selector = gr.Dropdown(
                    choices=[("Português", "pt"), ("English", "en")],
                    value="pt",
                    label="Language/Idioma",
                    interactive=True,
                    scale=1
                )

        with gr.Tabs():
            # Tab 1: Manuscritos
            with gr.TabItem(i18n("manuscripts_tab")):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown(i18n("manage_manuscripts"))

                        # Create manuscript
                        concept_input = gr.Textbox(label=i18n("manuscript_concept"),
                                                   placeholder=i18n("concept_placeholder"))
                        create_btn = gr.Button(i18n("create_manuscript"))

                        # Load manuscript
                        manuscripts_dropdown = gr.Dropdown(
                            choices=app.get_manuscripts_list(),
                            label=i18n("select_manuscript"),
                            interactive=True
                        )
                        load_btn = gr.Button(i18n("load_manuscript"))
                        delete_btn = gr.Button(i18n("delete_manuscript"), variant="stop")

                        # status_text = gr.Textbox(label="Status", interactive=False)

                    with gr.Column(scale=2):
                        gr.Markdown(i18n("section_editor"))

                        sections_dropdown = gr.Dropdown(label=i18n("sections"), interactive=True)

                        with gr.Row():
                            section_name_input = gr.Textbox(label=i18n("new_section_name"),
                                                            placeholder=i18n("section_placeholder"))
                            add_section_btn = gr.Button(i18n("add_section"))

                        enhance_btn = gr.Button(i18n("enhance_selected_section"))

                        with gr.Row():
                            with gr.Column():
                                manuscript_editor = gr.Textbox(
                                    label=i18n("manuscript_content"),
                                    lines=20,
                                    max_lines=30,
                                    interactive=True
                                )
                                with gr.Row():
                                    update_btn = gr.Button(i18n("update_manuscript"))
                                    download_btn = gr.Button("📥 Baixar Manuscrito", variant="secondary")

                            with gr.Column():
                                gr.Markdown(i18n('manuscript_preview'))
                                manuscript_preview = gr.Markdown(
                                    label=i18n("manuscript_preview"),
                                    # show_label=True,
                                    value="",
                                    height=800,
                                    elem_classes=["markdown-preview-scroll"]
                                )

            # Tab 2: Revisão
            with gr.TabItem(i18n("review_tab")):
                gr.Markdown(i18n("review_and_critique"))

                with gr.Row():
                    review_sections_dropdown = gr.Dropdown(label=i18n("section_to_review"), interactive=True)
                    criticize_btn = gr.Button(i18n("criticize_section"))

                critique_output = gr.Textbox(
                    label=i18n("section_critique"),
                    lines=15,
                    interactive=False
                )

            # Tab 3: Projetos
            with gr.TabItem(i18n("projects_tab")):
                gr.Markdown(i18n("manage_projects"))

                with gr.Row():
                    with gr.Column():
                        gr.Markdown(i18n("create_new_project)"))
                        project_name_input = gr.Textbox(label=i18n("project_name"))
                        project_language = gr.Dropdown(
                            choices=["pt", "en", "es", "fr"],
                            value="pt",
                            label="Idioma"
                        )
                        project_model = gr.Dropdown(
                            choices=app.available_models,
                            value=app.available_models[0],
                            label="Modelo de IA",
                            allow_custom_value="True",
                            interactive=True
                        )
                        create_project_btn = gr.Button(i18n("create_project"))

                        gr.Markdown(i18n("configure_base_prompt"))
                        base_prompt_display = gr.Textbox(
                            label="Prompt Base Atual",
                            value=app.get_base_prompt(),
                            lines=5,
                            interactive=True,
                            placeholder="Digite o prompt base para o modelo de IA..."
                        )
                        update_prompt_btn = gr.Button("Atualizar Prompt Base")

                    with gr.Column():
                        gr.Markdown("### Carregar Projeto Existente")
                        projects_dropdown = gr.Dropdown(
                            choices=app.get_projects_list(),
                            label="Projetos Existentes"
                        )
                        load_project_btn = gr.Button("Carregar Projeto")
                        project_status = gr.Textbox(label="Status do Projeto", interactive=False)

            # Tab 4: Base de Conhecimento
            with gr.TabItem("Base de Conhecimento"):
                gr.Markdown("## Gerenciar Base de Conhecimento")

                with gr.Row():
                    with gr.Column(scale=1):
                        file_upload = gr.File(label="Carregar Documento")
                        collection_name_dropdown = gr.Dropdown(
                            choices=app.get_collections_list(),
                            value="Literatura",
                            label="Nome da Coleção",
                            info="Selecione uma coleção existente ou digite um novo nome",
                            allow_custom_value=True,
                            interactive=True
                        )
                        embed_btn = gr.Button("Incorporar Documento")
                        refresh_collections_btn = gr.Button("Atualizar Coleções")

                    with gr.Column(scale=2):
                        gr.Markdown("### Documentos Incorporados")
                        # Inicializar com dados atuais em vez de chamar a função diretamente
                        try:
                            initial_documents = [[doc[0].split('/')[-1], doc[1]] for doc in
                                                 app.get_embedded_documents()]
                        except:
                            initial_documents = []

                        documents_display = gr.Dataframe(
                            headers=["Nome", "Coleção"],
                            value=initial_documents,
                            interactive=False,
                            max_height=500
                        )
                        refresh_docs_btn = gr.Button("Atualizar Lista")

        # Download file component (hidden)
        download_file = gr.File(visible=False)
        
        # Status geral
        status_text = gr.Textbox(label="Status", interactive=False, max_lines=3)

        # Footer
        gr.Markdown(
            "---\n"
            "**© Copyright 2025 by [Deeplearn Ltd](https://www.deeplearn.ltd)**",
            elem_id="footer"
        )

        # Event handlers
        create_btn.click(
            lambda concept: app.create_manuscript(concept, i18n),
            inputs=[concept_input],
            outputs=[status_text, manuscripts_dropdown]
        )

        load_btn.click(
            lambda manuscript_id: app.load_manuscript(manuscript_id, i18n),
            inputs=[manuscripts_dropdown],
            outputs=[status_text, manuscript_editor, sections_dropdown, review_sections_dropdown]
        ).then(
            lambda text: text,
            inputs=[manuscript_editor],
            outputs=[manuscript_preview]
        )

        add_section_btn.click(
            lambda section_name: app.add_section(section_name, i18n),
            inputs=[section_name_input],
            outputs=[status_text, manuscript_editor]
        )

        enhance_btn.click(
            app.enhance_section,
            inputs=[sections_dropdown],
            outputs=[manuscript_editor]
        ).then(
            lambda text: text,
            inputs=[manuscript_editor],
            outputs=[manuscript_preview]
        )

        update_btn.click(
            app.update_manuscript_text,
            inputs=[manuscript_editor],
            outputs=[status_text]
        )

        download_btn.click(
            app.download_manuscript,
            outputs=[status_text, download_file]
        ).then(
            lambda file_path: gr.File(value=file_path, visible=True) if file_path else gr.File(visible=False),
            inputs=[download_file],
            outputs=[download_file]
        ).then(
            lambda: gr.File(visible=False),
            outputs=[download_file],
            js="() => { setTimeout(() => { document.querySelector('[data-testid=\"file-download\"]')?.click(); }, 100); return null; }"
        )

        # Update preview when editor content changes
        manuscript_editor.change(
            lambda text: text,
            inputs=[manuscript_editor],
            outputs=[manuscript_preview]
        )

        delete_btn.click(
            app.delete_manuscript,
            inputs=[manuscripts_dropdown],
            outputs=[status_text, manuscripts_dropdown]
        )

        criticize_btn.click(
            app.criticize_section,
            inputs=[review_sections_dropdown],
            outputs=[critique_output]
        )

        create_project_btn.click(
            app.create_project,
            inputs=[project_name_input, project_language, project_model],
            outputs=[project_status, projects_dropdown]
        )

        load_project_btn.click(
            app.load_project,
            inputs=[projects_dropdown],
            outputs=[project_status, project_name_input, project_language, project_model]
        )

        project_model.change(
            app.update_project_model,
            inputs=[project_model],
            outputs=[project_status]
        )

        # Auto-save project name changes
        project_name_input.change(
            lambda name: app.update_project_property("name", name),
            inputs=[project_name_input],
            outputs=[project_status]
        )

        # Auto-save project language changes
        project_language.change(
            lambda lang: app.update_project_property("language", lang),
            inputs=[project_language],
            outputs=[project_status]
        )

        embed_btn.click(
            app.embed_document,
            inputs=[file_upload, collection_name_dropdown],
            outputs=[status_text, documents_display]
        )

        refresh_docs_btn.click(
            lambda: gr.Dataframe(value=[[doc[0].split('/')[-1], doc[1]] for doc in app.get_embedded_documents()],
                                 headers=["Nome", "Coleção"],
                                 interactive=False,
                                 max_height=500
                                 ),
            outputs=[documents_display]
        )

        refresh_collections_btn.click(
            lambda: gr.Dropdown(choices=app.get_collections_list(), value="Literatura"),
            outputs=[collection_name_dropdown]
        )

        update_prompt_btn.click(
            app.update_base_prompt,
            inputs=[base_prompt_display],
            outputs=[status_text]
        )

        # Update review sections when manuscript is loaded
        manuscripts_dropdown.change(
            lambda x: gr.Dropdown(choices=list(app.workflow.get_manuscript_sections(x).keys()) if x else []),
            inputs=[manuscripts_dropdown],
            outputs=[review_sections_dropdown]
        )

        # Language change handler
        language_selector.change(
            lambda lang: gr.update(),
            inputs=[language_selector],
            outputs=[]
        )

        # Carregar documentos na inicialização
        interface.load(
            lambda: gr.Dataframe(
                value=[[doc[0].split('/')[-1], doc[1]] for doc in app.get_embedded_documents()],
                headers=["nome", "Coleção"],
                interactive=False
            ),
            outputs=[documents_display]
        )

    return interface, i18n


def main(db_path: Optional[str] = '/data'):
    interface, i18n = create_interface(db_path=db_path)
    interface.launch(server_name="0.0.0.0",
                     server_port=7860,
                     share=False,
                     favicon_path="./assets/icon.png",
                     pwa=True,
                     i18n=i18n
                     )


if __name__ == "__main__":
    main()
