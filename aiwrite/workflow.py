import datetime
import os
from typing import List, Dict, Optional

import fitz
from fitz import EmptyFileError
from libbydbot.brain import LibbyDBot
from libbydbot.brain.embed import DocEmbedder
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Project(SQLModel, table=True):
    """Represents a project configuration.
    
    Attributes:
        id: Unique identifier for the project
        name: Project name
        manuscript_id: ID of selected manuscript
        documents_folder: Path to documents folder
        language: Language code (en, pt, es)
        model: LLM model name
        created: Timestamp when project was created
        last_updated: Timestamp when project was last modified
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    manuscript_id: Optional[int] = Field(default=None, foreign_key="manuscript.id")
    documents_folder: Optional[str] = None
    language: str = Field(default="en")
    model: str = Field(default="llama3")
    created: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        nullable=False,
        index=True
    )
    last_updated: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        nullable=False,
        index=True
    )


class Manuscript(SQLModel, table=True):
    """Represents a manuscript in the database.
    
    Attributes:
        id: Unique identifier for the manuscript
        created: Timestamp when manuscript was first created
        last_updated: Timestamp when manuscript was last modified
        source: Complete Markdown text content of the manuscript
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    created: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        nullable=False,
        index=True
    )
    last_updated: datetime.datetime = Field(
        default_factory=datetime.datetime.now,
        nullable=False,
        index=True
    )
    source: str  # Stores the complete Markdown text of the manuscript


class Workflow:
    """Manages the manuscript writing workflow including database, AI model and knowledge base.
    
    Attributes:
        engine: Database engine connection
        base_prompt: Default prompt for AI writing
        libby: AI model instance
        KB: Knowledge base embedding instance
        manuscript: Currently loaded manuscript
    """

    def __init__(self, dburl: str = "sqlite:///data/aiwrite.db", model: str = "gpt", db_path: str = "/data",
                 collection_name: str = "literature", project_id: Optional[int] = None):
        """Initialize the workflow with database, AI model and knowledge base.
        
        Args:
            dburl: Database connection URL
            model: Name of AI model to use
            collection_name: Name of knowledge base collection
            project_id: ID of the project to load (if any)
        """
        self.engine = create_engine(dburl)
        self.db_path = db_path
        if not os.path.exists(db_path.strip('/')):
            os.makedirs(db_path.strip('/'))
        SQLModel.metadata.create_all(self.engine)
        self.base_prompt = ("You are a scientific writer. You should write sections of scientific articles in markdown "
                            "format on request.")
        self.libby = LibbyDBot(model=model)
        self.dburl = dburl
        self.KB = DocEmbedder(col_name=collection_name, dburl=f'sqlite:///{db_path}/embedding.db', embedding_model='gemini-embedding-001')
        self.KB.get_embedded_documents()
        self.manuscript = None
        self.project_id = project_id
        self.current_project = self.get_project(project_id) if project_id else None

    def set_knowledge_base(self, collection_name: str) -> None:
        """Set the knowledge base collection to use.
        
        Args:
            collection_name: Name of the knowledge base collection
        """
        self.KB = DocEmbedder(col_name=collection_name, dburl=self.dburl)

    def set_model(self, model: str) -> None:
        """Set the AI model to use for writing.
        
        Args:
            model: Name of the AI model
        """
        try:
            self.libby = LibbyDBot(model=model)
        except ValueError as exc:
            print(f"Error: {exc}\nUsing the default model instead.")

    def embed_document(self, file_name: str) -> None:
        """Embed the contents of a document into the knowledge base.
        
        Args:
            file_name: Path to the document file to embed
        """
        try:
            doc = fitz.open(file_name)
        except EmptyFileError:
            pass
        n = doc.name
        for page_number, page in enumerate(doc):
            text = page.get_text()
            if not text:
                continue
            self.KB.embed_text(text, n, page_number)

    def get_man_list(self, n: int = 100) -> List[Manuscript]:
        """Get a list of manuscripts from the database.
        
        Args:
            n: Maximum number of manuscripts to return
            
        Returns:
            List of Manuscript objects
        """
        with Session(self.engine) as session:
            statement = select(Manuscript).limit(n)
            manuscripts = session.exec(statement).all()
        return manuscripts

    def get_manuscript_text(self, manuscript_id: int) -> str:
        """Get the markdown text content of a manuscript.
        
        Args:
            manuscript_id: ID of the manuscript to retrieve
            
        Returns:
            Markdown text content of the manuscript
        """
        manuscript = self.get_manuscript(manuscript_id)
        return manuscript.source if manuscript else ""

    def setup_manuscript(self, concept: str) -> Manuscript:
        """Initialize a new manuscript with title and abstract based on a concept.
        
        Args:
            concept: Initial concept/idea for the manuscript
            
        Returns:
            Newly created Manuscript object
        """
        title = self.libby.ask(
            f"Please provide a title for the manuscript, based on this concept: {concept}.\n\n Only return the title, without additional text.")
        knowledge = self.KB.retrieve_docs(concept, num_docs=15).strip('"')
        self.libby.set_context(self.base_prompt + f"\n\n{concept}" + f"\n\n{knowledge}")
        abstract = self.libby.ask(
            "Please write an abstract for a manuscript, based on the context provided. Only return the abstract text, without additional text.")

        markdown_content = f"# {title}\n\n## Abstract\n{abstract}"
        manuscript = Manuscript(source=markdown_content)
        self._save_manuscript(manuscript)
        if self.current_project:
            with Session(self.engine) as session:
                self.current_project.manuscript_id = manuscript.id
                session.add(self.current_project)
                session.commit()
        return manuscript

    def get_most_recent_project(self) -> int:
        """Get the ID of the most recently updated manuscript.
        
        Returns:
            ID of most recent manuscript, or -1 if none exist
        """
        with Session(self.engine) as session:
            statement = select(Project).order_by(Project.last_updated.desc()).limit(1)
            project = session.exec(statement).first()
        return -1 if project is None else project.id

    def get_project_manuscript(self, project_id: int) -> Manuscript:
        """Get the manuscript id associated with a project.

        Args:
            project_id: ID of the project to retrieve manuscript from

        Returns:
            Manuscript object associated with the project
        """
        project = self.get_project(project_id)
        return project.manuscript_id if project.manuscript_id is not None else -1

    def get_manuscript(self, manuscript_id: int) -> Manuscript:
        """Retrieve a manuscript from the database by ID.
        
        Args:
            manuscript_id: ID of the manuscript to retrieve
            
        Returns:
            Manuscript object if found, None otherwise
        """
        with Session(self.engine) as session:
            statement = select(Manuscript).where(Manuscript.id == manuscript_id)
            manuscript = session.exec(statement).first()
            self.manuscript = manuscript
        return manuscript

    def add_section(self, manuscript_id: int, section_name: str) -> Optional[Manuscript]:
        """Add a new section to a manuscript.
        
        Args:
            manuscript_id: ID of the manuscript to modify
            section_name: Name of the section to add
            
        Returns:
            Updated Manuscript object if successful, None otherwise
        """
        manuscript = self.get_manuscript(manuscript_id)
        if not manuscript:
            return None

        self.libby.set_context(self.base_prompt + f"\n\nManuscript:\n\n{manuscript.source}")
        section = self.libby.ask(
            f"Please write the {section_name} section of the manuscript, based on the context provided. Only return the section text, without additional text.")

        # Add the new section to the markdown content
        if section.startswith(f"## {section_name.capitalize()}"):
            section = section.split("\n", 1)[1].strip()
        new_content = f"{manuscript.source}\n\n## {section_name.capitalize()}\n{section}"
        manuscript.source = new_content
        self._save_manuscript(manuscript)
        return manuscript

    def enhance_section(self, manuscript_id: int, section_name: str) -> Optional[Manuscript]:
        """Enhance/improve an existing section in a manuscript.
        
        Args:
            manuscript_id: ID of the manuscript to modify
            section_name: Name of the section to enhance
            
        Returns:
            Updated Manuscript object if successful, None otherwise
        """
        manuscript = self.get_manuscript(manuscript_id)
        if not manuscript:
            return None

        # Find and replace the existing section
        section_header = f"## {section_name.capitalize()}"
        if section_header not in manuscript.source:
            return self.add_section(manuscript_id, section_name)

        self.libby.set_context(self.base_prompt + f"\n\nManuscript:\n\n{manuscript.source}")
        enhanced_section = self.libby.ask(
            f"Please enhance the {section_name} section of the manuscript, based on the context provided. Only return the enhanced section text, without additional text.")

        # Replace the existing section with the enhanced one
        parts = manuscript.source.split(section_header)
        if len(parts) > 1:
            before_section = parts[0]
            after_section = parts[1].split("\n## ", 1)[1] if "\n## " in parts[1] else ""
            new_content = f"{before_section}{section_header}\n{enhanced_section}\n\n## {after_section}" if after_section else f"{before_section}{section_header}\n{enhanced_section}"
            manuscript.source = new_content
            self._save_manuscript(manuscript)
        return manuscript

    def update_from_text(self, manuscript_id: int, text: str) -> None:
        """Update a manuscript's content from markdown text.
        
        Args:
            manuscript_id: ID of the manuscript to update
            text: New markdown text content
        """
        """Update the manuscript content from a markdown text"""
        manuscript = self.get_manuscript(manuscript_id)
        parsed = parse_manuscript_text(text)
        if not parsed:
            return
        manuscript.source = text
        manuscript.last_updated = datetime.datetime.now()
        self._save_manuscript(manuscript)

    def get_manuscript_sections(self, manuscript_id: int) -> Dict[str, str]:
        """Get all sections from a manuscript as a dictionary.
        
        Args:
            manuscript_id: ID of the manuscript to retrieve sections from
            
        Returns:
            Dictionary mapping section names to their content
        """
        manuscript = self.get_manuscript(manuscript_id)
        return parse_manuscript_text(manuscript.source)

    def criticize_section(self, manuscript_id: int, section_name: str) -> str:
        """Get critical feedback on a manuscript section.
        
        Args:
            manuscript_id: ID of the manuscript containing the section
            section_name: Name of the section to critique
            
        Returns:
            String containing critical feedback
        """
        self.libby.set_context(self.base_prompt + f"\n\nManuscript:\n\n{self.get_manuscript_text(manuscript_id)}")
        criticized_section = self.libby.ask(
            f"Please criticize the {section_name} section of the manuscript, based on the context provided. "
            f"Only return your critical opinion of the section, indicating changes that could be applied to improve it.")
        return criticized_section

    def delete_manuscript(self, manuscript_id: int) -> None:
        """Delete a manuscript from the database.
        
        Args:
            manuscript_id: ID of the manuscript to delete
        """
        """Delete a manuscript from the database"""
        with Session(self.engine) as session:
            manuscript = session.get(Manuscript, manuscript_id)
            if manuscript:
                session.delete(manuscript)
                session.commit()

    def save_project(self, project: Project) -> Project:
        """Save a project configuration to the database.
        
        Args:
            project: Project object to save
            
        Returns:
            Saved Project object
        """
        with Session(self.engine) as session:
            project.last_updated = datetime.datetime.now()
            session.add(project)
            session.commit()
            session.refresh(project)
            self.current_project = project
            self.project_id = project.id
        return project

    def get_project(self, project_id: int) -> Project:
        """Get a project by ID. If project doesn't exist or table is empty,
        create a new project with empty manuscript.
        
        Args:
            project_id: ID of the project to retrieve
            
        Returns:
            Project object (new one created if needed)
        """
        with Session(self.engine) as session:
            # Check if project exists
            statement = select(Project).where(Project.id == project_id)
            project = session.exec(statement).first()
            
            # If project doesn't exist or table is empty, create new one
            if not project:
                # Create empty manuscript
                empty_manuscript = Manuscript(source="# New Manuscript\n\n## Abstract\n")
                session.add(empty_manuscript)
                session.commit()
                session.refresh(empty_manuscript)
                
                # Create new project
                project = Project(
                    name="New Project",
                    manuscript_id=empty_manuscript.id,
                    language="en",
                    model="llama3"
                )
                session.add(project)
                session.commit()
                session.refresh(project)
                
            self.current_project = project
            self.project_id = project.id
            return project

    def get_projects(self) -> List[Project]:
        """Get all projects.
        
        Returns:
            List of Project objects
        """
        with Session(self.engine) as session:
            statement = select(Project)
            projects = session.exec(statement).all()
        return projects

    def delete_project(self, project_id: int) -> None:
        """Delete a project from the database.
        
        Args:
            project_id: ID of the project to delete
        """
        with Session(self.engine) as session:
            project = session.get(Project, project_id)
            if project:
                session.delete(project)
                session.commit()

    def _save_manuscript(self, manuscript: Manuscript) -> Manuscript:
        """Save a manuscript to the database.
        
        Args:
            manuscript: Manuscript object to save
            
        Returns:
            Saved Manuscript object
        """
        with Session(self.engine) as session:
            # Update last_updated timestamp
            manuscript.last_updated = datetime.datetime.now()
            session.add(manuscript)
            session.commit()
            session.refresh(manuscript)
        return manuscript


def parse_manuscript_text(text: str) -> Dict[str, str]:
    """
    Parse a markdown text into sections
    :param text: Markdown text
    :return: Dictionary with all the sections
    """
    parsed = {}
    if not text:
        return parsed

    # Extract title
    title_parts = text.split('# ', 1)
    if len(title_parts) > 1:
        parsed['title'] = title_parts[1].split('\n', 1)[0].strip()

    # Extract sections
    sections = text.split('## ')
    for section in sections[1:]:
        section_name = section.split('\n', 1)[0].lower()
        section_content = section.split('\n', 1)[1].strip() if '\n' in section else ''
        parsed[section_name] = section_content

    return parsed
