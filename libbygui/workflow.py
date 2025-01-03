from typing import List, Dict, Any, Optional
import datetime
from sqlmodel import Field, Session, SQLModel, create_engine, select
from libbydbot.brain import LibbyDBot
from libbydbot.brain.embed import DocEmbedder
import fitz
from fitz import EmptyFileError


class Manuscript(SQLModel, table=True):
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
    source: str  # Stores the complete markdown text of the manuscript


class Workflow:
    def __init__(self, db_url: str = "sqlite:///manuscripts.db", model: str = "gpt",
                 knowledge_base: str = "embeddings"):
        self.engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine)
        self.base_prompt = ("You are a scientific writer. You should write sections of scientific articles in markdown "
                            "format on request.")
        self.libby = LibbyDBot(model=model)
        self.KB = DocEmbedder(col_name=knowledge_base)
        self.manuscript= None

    def set_knowledge_base(self, collection_name: str):
        self.KB = DocEmbedder(col_name=collection_name)

    def set_model(self, model: str):
        self.libby = LibbyDBot(model=model)

    def embed_document(self, file_name: str):
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
        with Session(self.engine) as session:
            statement = select(Manuscript).limit(n)
            manuscripts = session.exec(statement).all()
        return manuscripts

    def get_manuscript_text(self, manuscript_id: int) -> str:
        manuscript = self.get_manuscript(manuscript_id)
        return manuscript.source if manuscript else ""

    def setup_manuscript(self, concept: str):
        title = self.libby.ask(
            f"Please provide a title for the manuscript, based on this concept: {concept}.\n\n Only return the title, without additional text.")
        knowledge = self.KB.retrieve_docs(concept, num_docs=15).strip('"')
        self.libby.set_context(self.base_prompt + f"\n\n{concept}" + f"\n\n{knowledge}")
        abstract = self.libby.ask(
            "Please write an abstract for a manuscript, based on the context provided. Only return the abstract text, without additional text.")
        
        markdown_content = f"# {title}\n\n## Abstract\n{abstract}"
        manuscript = Manuscript(source=markdown_content)
        self._save_manuscript(manuscript)
        return manuscript

    def get_most_recent_id(self):
        with Session(self.engine) as session:
            statement = select(Manuscript).order_by(Manuscript.last_updated.desc()).limit(1)
            manuscript = session.exec(statement).first()
        return -1 if manuscript is None else manuscript.id

    def get_manuscript(self, manuscript_id: int) -> Manuscript:
        with Session(self.engine) as session:
            statement = select(Manuscript).where(Manuscript.id == manuscript_id)
            manuscript = session.exec(statement).first()
            self.manuscript = manuscript
        return manuscript

    def add_section(self, manuscript_id: int, section_name: str):
        manuscript = self.get_manuscript(manuscript_id)
        if not manuscript:
            return None
            
        self.libby.set_context(self.base_prompt + f"\n\nManuscript:\n\n{manuscript.source}")
        section = self.libby.ask(
            f"Please write the {section_name} section of the manuscript, based on the context provided. Only return the section text, without additional text.")
        
        # Add the new section to the markdown content
        new_content = f"{manuscript.source}\n\n## {section_name.capitalize()}\n{section}"
        manuscript.source = new_content
        self._save_manuscript(manuscript)
        return manuscript

    def enhance_section(self, manuscript_id: int, section_name: str):
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

    def update_from_text(self, manuscript_id: int, text: str):
        """Update the manuscript content from a markdown text"""
        manuscript = self.get_manuscript(manuscript_id)
        parsed = parse_manuscript_text(text)
        if not parsed:
            return
        manuscript.source = text
        manuscript.last_updated = datetime.datetime.now()
        self._save_manuscript(manuscript)

    def get_manuscript_sections(self, manuscript_id: int) -> Dict[str, str]:
        manuscript = self.get_manuscript(manuscript_id)
        return parse_manuscript_text(manuscript.source)

    def criticize_section(self, manuscript_id: int, section_name: str):
        self.libby.set_context(self.base_prompt + f"\n\nManuscript:\n\n{self.get_manuscript_text(manuscript_id)}")
        criticized_section = self.libby.ask(
            f"Please criticize the {section_name} section of the manuscript, based on the context provided. "
            f"Only return your critical opinion of the section, indicating changes that could be applied to improve it.")
        return criticized_section

    def delete_manuscript(self, manuscript_id: int):
        """Delete a manuscript from the database"""
        with Session(self.engine) as session:
            manuscript = session.get(Manuscript, manuscript_id)
            if manuscript:
                session.delete(manuscript)
                session.commit()

    def _save_manuscript(self, manuscript: Manuscript):
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
