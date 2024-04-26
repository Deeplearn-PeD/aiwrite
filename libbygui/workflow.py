from typing import List, Dict, Any, Optional
from sqlmodel import Field, Session, SQLModel, create_engine
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

    def setup_manuscript(self, concept: str):
        title = self.libby.ask(f"Please provide a title for the manuscript, based on this concept: {concept}.\n\n Only return the title, without additional text.")
        knowledge = self.KB.retrieve_docs(concept, num_docs=15)
        self.libby.set_context(self.base_prompt + f"\n\n{concept}" + f"\n\n{knowledge}")
        abstract = self.libby.ask("Please write an abstract for a manuscript, based on the context provided. Only return the abstract text, without additional text.")
        manuscript = Manuscript(title='# ' + title if title is not None else "# title", abstract=abstract)
        self._save_manuscript(manuscript)
        return manuscript

    def _save_manuscript(self, manuscript: Manuscript):
        with Session(self.engine) as session:
            session.add(manuscript)
            session.commit()
            session.refresh(manuscript)
        return manuscript
