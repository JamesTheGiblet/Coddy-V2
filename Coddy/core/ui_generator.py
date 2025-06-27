# core/ui_generator.py
import ast
from pathlib import Path
import sys
import os


class UIGenerator:
    """
    Generates a basic Streamlit UI from a Python data class definition.
    """

    def _get_widget_for_type(self, type_str: str, field_name: str) -> str:
        """Maps a Python type string to a Streamlit widget."""
        label = field_name.replace('_', ' ').title()
        type_map = {
            'str': f"st.text_input('{label}')",
            'int': f"st.number_input('{label}', step=1)",
            'float': f"st.number_input('{label}')",
            'bool': f"st.checkbox('{label}')",
            'date': f"st.date_input('{label}')",
        }
        return type_map.get(type_str, f"st.text_input('{label}')")

    def _get_import_path_from_source_file(self, source_file: Path) -> str:
        """
        Calculates the Python import path for a given source file path.
        It finds the longest sys.path entry that is a parent of the source file
        and constructs the import path relative to it.
        """
        abs_source_path = source_file.resolve()

        best_path_root = None
        # Use a copy of sys.path because it can be modified during iteration
        for p in list(sys.path):
            if not p: continue

            try:
                # Some paths in sys.path might not exist or be resolvable
                abs_p = Path(p).resolve()
                # Use a compatible way to check if abs_source_path is under abs_p
                if str(abs_source_path).startswith(str(abs_p) + os.path.sep):
                    if best_path_root is None or len(str(abs_p)) > len(str(best_path_root)):
                        best_path_root = abs_p
            except (FileNotFoundError, RuntimeError):
                continue

        if best_path_root:
            relative_path = abs_source_path.relative_to(best_path_root)
            import_path = str(relative_path.with_suffix('')).replace(os.path.sep, '.')
            return import_path
        else:
            return source_file.stem

    def generate_from_file(self, source_path: str) -> str:
        """
        Reads a Python file, finds the first class, and generates a Streamlit UI for it.
        """
        source_file = Path(source_path)
        if not source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        source_code = source_file.read_text(encoding='utf-8')
        tree = ast.parse(source_code)
        
        class_node = next((node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)), None)

        if not class_node:
            raise ValueError(f"No class definition found in {source_path}")

        class_name = class_node.name
        fields = []
        imports_needed = set()

        for node in class_node.body:
            if isinstance(node, ast.AnnAssign):
                field_name = node.target.id
                field_type = 'str' # default
                if isinstance(node.annotation, ast.Name):
                    field_type = node.annotation.id
                elif isinstance(node.annotation, ast.Attribute):
                    field_type = node.annotation.attr
                    if isinstance(node.annotation.value, ast.Name):
                        imports_needed.add(node.annotation.value.id)

                fields.append({'name': field_name, 'type': field_type})

        if not fields:
             raise ValueError(f"No typed attributes found in class {class_name}")

        module_import_path = self._get_import_path_from_source_file(source_file)

        import_statements = "import streamlit as st\n"
        for imp in sorted(list(imports_needed)):
            import_statements += f"import {imp}\n"
        import_statements += f"from {module_import_path} import {class_name}\n\n"

        title = f"st.title('📝 Input for {class_name}')\n\n"
        form_start = "with st.form(key='data_form'):\n"
        
        widget_code = "".join([f"    {f['name']}_input = {self._get_widget_for_type(f['type'], f['name'])}\n" for f in fields])
        submit_button = "    submit_button = st.form_submit_button(label='Submit')\n\n"

        instance_creation = ", ".join([f"{f['name']}={f['name']}_input" for f in fields])
        display_logic = (
            "if submit_button:\n"
            "    try:\n"
            f"        instance = {class_name}({instance_creation})\n"
            "        st.success('Instance created successfully!')\n"
            "        import json\n"
            "        if hasattr(instance, 'json'):\n"
            "            st.json(json.loads(instance.json()))\n"
            "        else:\n"
            "            st.json(instance.__dict__)\n"
            "    except Exception as e:\n"
            "        st.error(f'Error creating instance: {e}')\n"
        )

        return import_statements + title + form_start + widget_code + submit_button + display_logic