from typing import List, Dict, Any, Optional
import datetime
from sqlmodel import Field, Session, SQLModel, create_engine, select
from libbydbot.brain import LibbyDBot
from libbydbot.brain.embed import DocEmbedder


class Manuscript(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    last_updated: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, nullable=False)
    title: str
    abstract: str
    introduction: Optional[str] = ""
    methods: Optional[str] = ""
    discussion: Optional[str] = ""
    conclusion: Optional[str] = ""




class Workflow:
    def __init__(self, db_url: str = "sqlite:///manuscripts.db", model: str = "llama",
                 knowledge_base: str = "embeddings"):
        self.engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine)
        self.base_prompt = "You are a scientific writer. You should write sections of scientific articles in markdown format on request."
        self.libby = LibbyDBot(model=model)
        self.KB = DocEmbedder(name=knowledge_base)

    def set_model(self, model: str):
        self.libby = LibbyDBot(model=model)
    def get_man_list(self, n: int = 100) -> List[Manuscript]:
        with Session(self.engine) as session:
            statement = select(Manuscript).limit(n)
            manuscripts = session.exec(statement).all()
        return manuscripts

    def get_manuscript_text(self, manuscript_id: int) -> Dict[str, Any]:
        manuscript = self.get_manuscript(manuscript_id)
        if manuscript is None:
            return ""
        return f"""
{'' if manuscript.title.startswith('#') else '# '}{manuscript.title}
{'' if '## Abstract' in manuscript.abstract else '## Abstract'}
{manuscript.abstract}
{'' if '## Introduction' in manuscript.introduction else '## Introduction'}
{manuscript.introduction}
{'' if '## Methods' in manuscript.methods else '## Methods'}
{manuscript.methods}
{'' if '## Discussion' in manuscript.discussion else '## Discussion'}
{manuscript.discussion}
{'' if '## Conclusion' in manuscript.conclusion else '## Conclusion'}
{manuscript.conclusion}
        """.strip()

    def setup_manuscript(self, concept: str):
        title = self.libby.ask(f"Please provide a title for the manuscript, based on this concept: {concept}.\n\n Only return the title, without additional text.")
        knowledge = self.KB.retrieve_docs(concept, num_docs=15)
        self.libby.set_context(self.base_prompt + f"\n\n{concept}" + f"\n\n{knowledge}")
        abstract = self.libby.ask("Please write an abstract for a manuscript, based on the context provided. Only return the abstract text, without additional text.")
        manuscript = Manuscript(title='# ' + title if title is not None else "# title", abstract=abstract)
        self._save_manuscript(manuscript)
        return manuscript

    def get_most_recent_id(self):
        with Session(self.engine) as session:
            statement = select(Manuscript).order_by(Manuscript.last_updated.desc()).limit(1)
            manuscript = session.exec(statement).first()
        return -1 if manuscript is None else manuscript.id

    def get_manuscript(self,manuscript_id: int) -> Manuscript:
        with Session(self.engine) as session:
            statement = select(Manuscript).where(Manuscript.id == manuscript_id)
            manuscript = session.exec(statement).first()
            self.manuscript = manuscript
        return manuscript

    def add_section(self, manuscript_id: int, section_name: str):
        manuscript = self.get_manuscript(manuscript_id)
        self.libby.set_context(self.base_prompt + f"\n\nManuscript:\n\n{self.get_manuscript_text(manuscript_id)}")
        section = self.libby.ask(f"Please write the {section_name} section of the manuscript, based on the context provided. Only return the section text, without additional text.")
        setattr(manuscript, section_name, section)
        self._save_manuscript(manuscript)
        return manuscript

    def enhance_section(self, manuscript_id: int, section_name: str):
        manuscript = self.get_manuscript(manuscript_id)
        self.libby.set_context(self.base_prompt + f"\n\nManuscript:\n\n{self.get_manuscript_text(manuscript_id)}")
        enhanced_section = self.libby.ask(f"Please enhance the {section_name} section of the manuscript, based on the context provided. Only return the enhanced section text, without additional text.")
        setattr(manuscript, section_name, enhanced_section)
        self._save_manuscript(manuscript)
        return manuscript

    def update_from_text(self, manuscript_id: int, text: str):
        manuscript = self.get_manuscript(manuscript_id)
        parsed = parse_manuscript_text(text)
        if not parsed:
            return
        for section in parsed:
            setattr(manuscript, section, parsed[section])
        self._save_manuscript(manuscript)

    def criticize_section(self, manuscript_id: int, section_name: str):
        self.libby.set_context(self.base_prompt + f"\n\nManuscript:\n\n{self.get_manuscript_text(manuscript_id)}")
        criticized_section = self.libby.ask(f"Please criticize the {section_name} section of the manuscript, based on the context provided. "
                                            f"Only return your critical opinion of the section, indicating changes that could be applied to improve it.")
        return criticized_section

    def _save_manuscript(self, manuscript: Manuscript):
        with Session(self.engine) as session:
            session.add(manuscript)
            session.commit()
            session.refresh(manuscript)
        return manuscript

def parse_manuscript_text(text: str) -> Dict[str, str]:
    """
    Parse a markdown text into sections
    :param text: Markdown text
    :return: Dictionary with all th sections
    """
    parsed = {}
    if text:
        parsed['title'] = text.split('# Abstract')[0].strip('# ').strip()
        parsed['abstract'] = text.split('## Introduction')[0].split('# Abstract')[1].strip()
        parsed['introduction'] = text.split('## Methods')[0].split('## Introduction')[1].strip()
        parsed['methods'] = text.split('## Discussion')[0].split('## Methods')[1].strip()
        parsed['discussion'] = text.split('## Conclusion')[0].split('## Discussion')[1].strip()
        parsed['conclusion'] = text.split('## Conclusion')[1].strip()
    return parsed
