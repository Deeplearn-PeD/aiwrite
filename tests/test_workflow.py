import unittest
from datetime import datetime
from typing import Dict

from aiwrite.workflow import Workflow, Manuscript, Project, parse_manuscript_text


class TestWorkflow(unittest.TestCase):
    def setUp(self):
        self.workflow = Workflow()
        # Setup test project
        self.test_project = Project(
            name="Test Project",
            manuscript_id=1,
            documents_folder="/test/path",
            language="en",
            model="gpt-4",
            created=datetime.now(),
            last_updated=datetime.now()
        )
        self.workflow.save_project(self.test_project)

    def test_set_model(self):
        self.workflow.set_model('new_model')
        self.assertEqual(self.workflow.libby.model, 'new_model')

    def test_get_man_list(self):
        manuscripts = self.workflow.get_man_list(5)
        self.assertIsInstance(manuscripts, list)
        self.assertLessEqual(len(manuscripts), 5)

    def test_get_manuscript_text(self):
        # Setup test manuscript
        manuscript = self.workflow.setup_manuscript("Test Manuscript")
        text = self.workflow.get_manuscript_text(manuscript.id)
        self.assertIsInstance(text, str)

    def test_setup_manuscript(self):
        concept = 'test concept'
        manuscript = self.workflow.setup_manuscript(concept)
        self.assertIsInstance(manuscript, Manuscript)
        self.assertEqual(manuscript.title, concept)

    def test_get_manuscript(self):
        # Setup test manuscript
        manuscript = self.workflow.setup_manuscript("Test Manuscript")
        fetched_manuscript = self.workflow.get_manuscript(manuscript.id)
        self.assertIsInstance(fetched_manuscript, Manuscript)
        self.assertEqual(fetched_manuscript.id, manuscript.id)

    def test_add_section(self):
        manuscript = self.workflow.setup_manuscript("Test Manuscript")
        updated_manuscript = self.workflow.add_section(manuscript.id, "introduction")
        self.assertIsNotNone(updated_manuscript)
        self.assertIn("introduction", updated_manuscript.sections)

    def test_enhance_section(self):
        manuscript = self.workflow.setup_manuscript("Test Manuscript")
        self.workflow.add_section(manuscript.id, "introduction")
        enhanced_manuscript = self.workflow.enhance_section(manuscript.id, "introduction")
        self.assertIsNotNone(enhanced_manuscript)
        self.assertGreater(len(enhanced_manuscript.sections["introduction"]), 0)

    def test_criticize_section(self):
        manuscript = self.workflow.setup_manuscript("Test Manuscript")
        self.workflow.add_section(manuscript.id, "introduction")
        criticism = self.workflow.criticize_section(manuscript.id, "introduction")
        self.assertIsInstance(criticism, str)
        self.assertGreater(len(criticism), 0)

    def test_project_management(self):
        # Test saving and retrieving project
        project = self.workflow.save_project(self.test_project)
        self.assertIsInstance(project, Project)
        
        # Test getting project
        fetched_project = self.workflow.get_project(project.id)
        self.assertEqual(fetched_project.id, project.id)
        
        # Test getting projects list
        projects = self.workflow.get_projects()
        self.assertIsInstance(projects, list)
        self.assertGreater(len(projects), 0)

    def test_parse_manuscript(self):
        with open('tests/fixtures/test_manuscript.md', 'r') as f:
            text = f.read()
        manuscript = parse_manuscript_text(text)
        self.assertIsInstance(manuscript, Dict)
        self.assertEqual(manuscript['title'], '"Thermogenic Fever: The Warming World\'s Role in Dengue\'s Global Rise"')
        self.assertEqual(manuscript['abstract'].strip()[:20], 'Thermogenic fever')

    def tearDown(self):
        # Clean up test data
        if hasattr(self, 'test_project'):
            self.workflow.delete_project(self.test_project.id)


if __name__ == '__main__':
    unittest.main()
