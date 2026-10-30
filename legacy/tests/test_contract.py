import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate import declarations

class ContractTests(unittest.TestCase):
    def test_defaults_are_not_layout(self):
        self.assertEqual(declarations('struct S {\n int a = 1;\n};'),declarations('struct S {\n int a = 2;\n};'))
    def test_field_order(self):
        self.assertNotEqual(declarations('struct S {\n int a;\n float b;\n};'),declarations('struct S {\n float b;\n int a;\n};'))
    def test_inserted_field(self):
        self.assertNotEqual(declarations('struct S {\n int a;\n};'),declarations('struct S {\n int a;\n int b;\n};'))
    def test_enum_order(self):
        self.assertNotEqual(declarations('enum class E { A, B };'),declarations('enum class E { B, A };'))

if __name__ == '__main__': unittest.main()
