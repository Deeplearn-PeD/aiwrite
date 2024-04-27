from typing import List, Dict, Any, Optional
from sqlmodel import Field, Session, SQLModel, create_engine, select
from libbydbot.brain import LibbyDBot
from libbydbot.brain.embed import DocEmbedder


class Manuscript(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    abstract: str
    introduction: Optional[str] = None
    methods: Optional[str] = None
    discussion: Optional[str] = None
    conclusion: Optional[str] = None




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
    def get_man_list(self, n: object = 10) -> List[Manuscript]:
        with Session(self.engine) as session:
            statement = select(Manuscript).limit(n)
            manuscripts = session.exec(statement).all()
        return manuscripts

    def get_manuscript_text(self, manuscript_id: int) -> Dict[str, Any]:
        manuscript = self.get_manuscript(manuscript_id)
        return f"""
        # {manuscript.title}
        ## Abstract
        {manuscript.abstract}
        ## Introduction
        {manuscript.introduction}
        ## Methods
        {manuscript.methods}
        ## Discussion
        {manuscript.discussion}
        ## Conclusion
        {manuscript.conclusion}
        """

    def setup_manuscript(self, concept: str):
        title = self.libby.ask(f"Please provide a title for the manuscript, based on this concept: {concept}.\n\n Only return the title, without additional text.")
        knowledge = self.KB.retrieve_docs(concept, num_docs=15)
        self.libby.set_context(self.base_prompt + f"\n\n{concept}" + f"\n\n{knowledge}")
        abstract = self.libby.ask("Please write an abstract for a manuscript, based on the context provided. Only return the abstract text, without additional text.")
        manuscript = Manuscript(title='# ' + title if title is not None else "# title", abstract=abstract)
        self._save_manuscript(manuscript)
        return manuscript

    def get_manuscript(self,manuscript_id: int) -> Manuscript:
        with Session(self.engine) as session:
            statement = select(Manuscript).where(Manuscript.id == manuscript_id)
            manuscript = session.exec(statement).first()
        return manuscript

    def add_section(self, manuscript: Manuscript, section_name: str):
        section = self.libby.ask(f"Please write the {section_name} section of the manuscript, based on the context provided. Only return the section text, without additional text.")
        setattr(manuscript, section_name, section)
        self._save_manuscript(manuscript)
        return manuscript

    def enhance_section(self, manuscript: Manuscript, section_name: str):
        section = getattr(manuscript, section_name)
        enhanced_section = self.libby.ask(f"Please enhance the {section_name} section of the manuscript, based on the context provided. Only return the enhanced section text, without additional text.")
        setattr(manuscript, section_name, enhanced_section)
        self._save_manuscript(manuscript)
        return manuscript

    def criticize_section(self, manuscript: Manuscript, section_name: str):
        section = getattr(manuscript, section_name)
        criticized_section = self.libby.ask(f"Please criticize the {section_name} section of the manuscript, based on the context provided. Only return the criticized section text, without additional text.")
        setattr(manuscript, section_name, criticized_section)
        self._save_manuscript(manuscript)
        return manuscript

    def _save_manuscript(self, manuscript: Manuscript):
        with Session(self.engine) as session:
            session.add(manuscript)
            session.commit()
            session.refresh(manuscript)
        return manuscript
