import unittest
from libbygui.workflow import Workflow, Manuscript, parse_manuscript_text

class TestWorkflow(unittest.TestCase):
    def setUp(self):
        self.workflow = Workflow(knowledge_base='test_kb')

    def test_set_model(self):
        self.workflow.set_model('new_model')
        self.assertEqual(self.workflow.libby.model, 'new_model')

    def test_get_man_list(self):
        manuscripts = self.workflow.get_man_list(5)
        self.assertEqual(len(manuscripts), 5)

    def test_get_manuscript_text(self):
        manuscript_id = 1  # assuming a manuscript with id 1 exists
        text = self.workflow.get_manuscript_text(manuscript_id)
        self.assertIsInstance(text, str)

    def test_setup_manuscript(self):
        concept = 'test concept'
        manuscript = self.workflow.setup_manuscript(concept)
        self.assertIsInstance(manuscript, Manuscript)

    def test_get_manuscript(self):
        manuscript_id = 1  # assuming a manuscript with id 1 exists
        manuscript = self.workflow.get_manuscript(manuscript_id)
        self.assertIsInstance(manuscript, Manuscript)

    def test_add_section(self):
        manuscript = Manuscript(title='test', abstract='test')  # assuming this is a valid manuscript
        self.workflow.add_section(manuscript, 'introduction')
        self.assertIsNotNone(manuscript.introduction)

    def test_enhance_section(self):
        manuscript = Manuscript(title='test', abstract='test', introduction='test')  # assuming this is a valid manuscript
        self.workflow.enhance_section(manuscript, 'introduction')
        self.assertIsNotNone(manuscript.introduction)

    def test_criticize_section(self):
        manuscript = Manuscript(title='test', abstract='test', introduction='test')  # assuming this is a valid manuscript
        self.workflow.criticize_section(manuscript, 'introduction')
        self.assertIsNotNone(manuscript.introduction)

    def test__save_manuscript(self):
        manuscript = Manuscript(title='test', abstract='test')  # assuming this is a valid manuscript
        saved_manuscript = self.workflow._save_manuscript(manuscript)
        self.assertEqual(saved_manuscript.id, manuscript.id)

    def test_parse_manuscript(self):
        with open('tests/fixtures/test_manuscript.md', 'r') as f:
            text = f.read()
        manuscript = parse_manuscript_text(text)
        self.assertEqual(manuscript['title'], '"Thermogenic Fever: The Warming World\'s Role in Dengue\'s Global Rise"')
        self.assertEqual(manuscript['abstract'].strip()[:20], '\n\nThermogenic fever')

if __name__ == '__main__':
    unittest.main()