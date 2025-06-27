# tests/test_ui_generator.py
import unittest
import os
import sys
import tempfile
from pathlib import Path
from core.ui_generator import UIGenerator
from core.utils import write_file

class TestUIGenerator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        # Add the temp directory to sys.path so imports can be resolved
        sys.path.insert(0, str(self.temp_path))

    def tearDown(self):
        self.temp_dir.cleanup()
        # Clean up sys.path
        if str(self.temp_path) in sys.path:
            sys.path.remove(str(self.temp_path))

    def test_generate_from_file(self):
        model_content = """
from pydantic import BaseModel
from datetime import date

class TestModel(BaseModel):
    name: str
    age: int
    is_student: bool
"""
        # Create a 'tests' package inside the temp directory to match the expected import
        tests_dir = self.temp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").touch()

        model_path = tests_dir / "test_model.py"
        write_file(str(model_path), model_content)

        generator = UIGenerator()
        ui_code = generator.generate_from_file(str(model_path))

        self.assertIn("import streamlit as st", ui_code)
        # With the temp dir in sys.path and the correct folder structure, this should now work
        self.assertIn("from tests.test_model import TestModel", ui_code.replace('\\', '/'))
        self.assertIn("st.title('📝 Input for TestModel')", ui_code)
        self.assertIn("name_input = st.text_input('Name')", ui_code)
        self.assertIn("age_input = st.number_input('Age', step=1)", ui_code)
        self.assertIn("is_student_input = st.checkbox('Is Student')", ui_code)
        self.assertIn("st.form_submit_button(label='Submit')", ui_code)
        self.assertIn("instance = TestModel(name=name_input, age=age_input, is_student=is_student_input)", ui_code)