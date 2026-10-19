#!/usr/bin/env python3
"""Run with python3 -m unittest discover -s this-directory -p 'test_*.py'."""

from pathlib import Path
import subprocess
import sys
import tempfile
from textwrap import indent
import unittest


SCRIPT = Path(__file__).with_name('rule_blocks.py')
BLOCK = (SCRIPT.parent.parent / 'references/rule-blocks/execution.md').read_text()


class RuleBlockTests(unittest.TestCase):
    def check(self, text):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'AGENTS.md'
            path.write_text(text)
            return subprocess.run([sys.executable, str(SCRIPT), str(path)],
                                  text=True, capture_output=True)

    def test_fenced_examples_do_not_duplicate_real_blocks(self):
        for opening, inside, closing in (
            ('~~~markdown', BLOCK, '~~~'),
            ('```markdown', BLOCK, '```'),
            ('````markdown', '```\n' + BLOCK + '```\n', '````'),
            ('~~~~', '~~~\n' + BLOCK, '~~~~~'),
            ('```markdown', '    ```\n' + BLOCK, '```'),
            ('- Example:\n\n    ```markdown',
             ''.join('    ' + line + '\n' for line in BLOCK.splitlines()), '    ```'),
        ):
            with self.subTest(opening=opening):
                result = self.check(opening + '\n' + inside + closing + '\n\n' + BLOCK)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('execution: current', result.stdout)
                self.assertNotIn('execution: duplicate', result.stdout)

    def test_real_duplicate_still_blocks(self):
        result = self.check(BLOCK + '\n' + BLOCK)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('execution: duplicate', result.stdout)

    def test_indented_examples_do_not_duplicate_or_reorder_real_blocks(self):
        for prefix, indent in (
            ('# Example\n\n', '    '),
            ('# Example\n\n', '\t'),
            ('- Example:\n\n', '      '),
            ('10. Example:\n\n', '        '),
            ('- Outer:\n\n  - Example:\n\n', '        '),
        ):
            with self.subTest(prefix=prefix, indent=repr(indent)):
                example = ''.join(indent + line + '\n' for line in BLOCK.splitlines())
                result = self.check(prefix + example + '\n# Actual rules\n\n' + BLOCK)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('execution: current', result.stdout)
                self.assertNotIn('duplicate', result.stdout)
                self.assertNotIn('order: repository sections after', result.stdout)

    def test_indented_unclosed_marker_is_only_example_content(self):
        result = self.check(BLOCK + '\n    ' + BLOCK.splitlines()[0] + '\n')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('unclosed marker', result.stdout)

    def test_thematic_break_does_not_create_a_list_margin(self):
        for separator, code_indent in (
            ('- - -', '    '), ('---', '    '),
            ('* * *', '    '), ('***', '    '),
            ('_ _ _', '    '), ('___', '    '),
            ('   -  - -  ', '    '), ('  *\t*\t*', '    '),
            ('- Outer:\n\n  - - -', '      '),
            ('10. Outer:\n\n    * * *', '        '),
        ):
            with self.subTest(separator=separator):
                example = indent(BLOCK, code_indent)
                result = self.check(separator + '\n\n' + example + '\n' + BLOCK)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('execution: current', result.stdout)
                self.assertNotIn('duplicate', result.stdout)

    def test_unclosed_list_fence_ends_when_its_container_ends(self):
        for opening, example_indent, following in (
            ('- Example:\n\n  ```markdown\n', '  ', BLOCK),
            ('10. Example:\n\n    ~~~markdown\n', '    ', BLOCK),
            ('- Outer:\n\n  - ```markdown\n', '    ', indent(BLOCK, '  ')),
            ('- ```markdown\n', '  ', '- Actual:\n\n' + indent(BLOCK, '  ')),
        ):
            with self.subTest(opening=opening):
                text = opening + indent(BLOCK, example_indent) + '\n' + following
                result = self.check(text)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn('execution: absent', result.stdout)
                self.assertNotIn('duplicate', result.stdout)
                duplicate = self.check(BLOCK + '\n' + text)
                self.assertEqual(duplicate.returncode, 1, duplicate.stdout)
                self.assertIn('execution: duplicate', duplicate.stdout)

    def test_setext_underline_does_not_create_a_list_margin(self):
        for prefix, code_indent in (
            ('Example\n-\n\n', '    '),
            ('  Example\n   - \t\n\n', '    '),
            ('Example\n--\n\n', '    '),
            ('Example\n=\n\n', '    '),
            ('Example\n===\n\n', '    '),
            ('Example\nsecond line\n-\n\n', '    '),
            ('Example\n    continued line\n-\n\n', '    '),
            ('- Example\n  -\n\n', '      '),
            ('10. Example\n    -\n\n', '        '),
            ('- Example\n  =\n\n', '      '),
            ('# Example\n=\n-\n\n', '    '),
        ):
            with self.subTest(prefix=prefix):
                result = self.check(prefix + indent(BLOCK, code_indent) + '\n' + BLOCK)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('execution: current', result.stdout)
                self.assertNotIn('duplicate', result.stdout)

    def test_list_cannot_interrupt_paragraph_without_valid_first_item(self):
        for marker in ('*', '+', '1.', '2.', '2. continued', '10) continued'):
            with self.subTest(marker=marker):
                result = self.check('Example\n' + marker + '\n\n' + indent(BLOCK, '    ') + '\n' + BLOCK)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('execution: current', result.stdout)
                self.assertNotIn('duplicate', result.stdout)

    def test_indented_fence_does_not_hide_real_duplicate(self):
        result = self.check(BLOCK + '\n    ```\n\n' + BLOCK)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn('execution: duplicate', result.stdout)

    def test_real_list_duplicates_still_block(self):
        for listed in (
            '- Rules:\n\n' + indent(BLOCK, '  '),
            '10. Rules:\n\n' + indent(BLOCK, '    '),
            '- Outer:\n\n  - Rules:\n\n' + indent(BLOCK, '    '),
            '- ' + indent(BLOCK, '  ').lstrip(),
            '-\n\n' + indent(BLOCK, '     '),
            '* Rules:\n\n' + indent(BLOCK, '  '),
            '+ Rules:\n\n' + indent(BLOCK, '  '),
            '- -\n\n' + indent(BLOCK, '  '),
            '- * -\n\n' + indent(BLOCK, '  '),
            '# Heading\n-\n\n' + indent(BLOCK, '  '),
            'Example\n\n-\n\n' + indent(BLOCK, '  '),
            '- Outer\n\n  -\n\n' + indent(BLOCK, '    '),
            '- Example\n-\n\n' + indent(BLOCK, '  '),
            'Example\n1. Rules:\n\n' + indent(BLOCK, '   '),
        ):
            with self.subTest(listed=listed[:30]):
                result = self.check(BLOCK + '\n' + listed)
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn('execution: duplicate', result.stdout)

    def test_example_headings_are_not_reported_as_live_sections(self):
        for example in (
            '```markdown\n' + BLOCK + '```\n',
            ''.join('    ' + line + '\n' for line in BLOCK.splitlines()),
        ):
            with self.subTest(example=example[:20]):
                result = self.check(example)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('execution: absent\n', result.stdout)
                self.assertNotIn('section ', result.stdout)


if __name__ == '__main__':
    unittest.main()
