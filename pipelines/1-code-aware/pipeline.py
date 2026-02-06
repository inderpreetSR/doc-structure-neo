"""
Pipeline 1: Code-Aware Auto-Generation
Parses Python source files using AST and generates Markdown documentation.
Run: python pipeline.py --source ./your-project --output ./docs
"""

import ast
import os
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime


class CodeAwareDocGenerator:
    """Parses Python source files and generates documentation."""

    def __init__(self, source_dir, output_dir):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.registry = []

    def scan_files(self, extensions=('.py',)):
        """Recursively find all source files."""
        files = []
        for ext in extensions:
            files.extend(self.source_dir.rglob(f'*{ext}'))
        return sorted(files)

    def _load_registry(self):
        """Load previous registry to support incremental builds."""
        reg_path = self.output_dir / 'registry.json'
        if not reg_path.exists():
            return {}
        try:
            data = json.loads(reg_path.read_text(encoding='utf-8'))
            return {item.get('source'): item for item in data if item.get('source')}
        except Exception:
            return {}

    def _hash_bytes(self, data):
        return hashlib.md5(data).hexdigest()

    def parse_python_file(self, filepath):
        """Parse a Python file and extract classes/functions."""
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        try:
            tree = ast.parse(source, filename=str(filepath))
        except SyntaxError:
            return []

        items = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                items.append({
                    'type': 'function',
                    'name': node.name,
                    'args': [a.arg for a in node.args.args],
                    'docstring': ast.get_docstring(node) or '',
                    'lineno': node.lineno,
                    'returns': ast.dump(node.returns) if node.returns else None,
                    'decorators': [
                        ast.dump(d) for d in node.decorator_list
                    ]
                })
            elif isinstance(node, ast.ClassDef):
                methods = []
                for n in node.body:
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(n.name)
                items.append({
                    'type': 'class',
                    'name': node.name,
                    'methods': methods,
                    'docstring': ast.get_docstring(node) or '',
                    'lineno': node.lineno,
                    'bases': [ast.dump(b) for b in node.bases]
                })
        return items

    def generate_llm_prompt(self, filepath, items):
        """Build an LLM prompt for enhanced documentation."""
        prompt = f"Generate comprehensive documentation for `{filepath.name}`:\n\n"
        for item in items:
            if item['type'] == 'function':
                prompt += f"Function: {item['name']}({', '.join(item['args'])})\n"
                prompt += f"  Docstring: {item['docstring']}\n"
                prompt += f"  Returns: {item['returns']}\n\n"
            elif item['type'] == 'class':
                prompt += f"Class: {item['name']}\n"
                prompt += f"  Methods: {', '.join(item['methods'])}\n"
                prompt += f"  Docstring: {item['docstring']}\n\n"
        prompt += "\nProvide: summary, usage examples, parameter descriptions, return values."
        return prompt

    def render_markdown(self, filepath, items):
        """Render extracted items into Markdown."""
        rel = filepath.relative_to(self.source_dir)
        md = f"# {rel}\n\n"
        md += f"*Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        md += "---\n\n"

        # Table of contents
        md += "## Table of Contents\n\n"
        for item in items:
            anchor = item['name'].lower().replace('_', '-')
            if item['type'] == 'class':
                md += f"- [Class `{item['name']}`](#{anchor})\n"
            else:
                md += f"- [`{item['name']}()`](#{anchor})\n"
        md += "\n---\n\n"

        for item in items:
            if item['type'] == 'class':
                md += f"## Class `{item['name']}`\n\n"
                if item['docstring']:
                    md += f"> {item['docstring']}\n\n"
                md += f"**Methods:** {', '.join(f'`{m}`' for m in item['methods'])}\n\n"
                md += f"*Defined at line {item['lineno']}*\n\n"
            elif item['type'] == 'function':
                md += f"### `{item['name']}({', '.join(item['args'])})`\n\n"
                if item['docstring']:
                    md += f"> {item['docstring']}\n\n"
                if item['returns']:
                    md += f"**Returns:** `{item['returns']}`\n\n"
                md += f"*Line {item['lineno']}*\n\n"
            md += "---\n\n"
        return md

    def run(self):
        """Execute the full pipeline."""
        files = self.scan_files()
        print(f"[scan] Found {len(files)} Python files in {self.source_dir}")

        existing_registry = self._load_registry()

        for filepath in files:
            source_bytes = filepath.read_bytes()
            source_hash = self._hash_bytes(source_bytes)
            out_name = filepath.relative_to(self.source_dir)
            out_path = self.output_dir / f"{out_name}.md"

            existing = existing_registry.get(str(filepath))
            if existing and existing.get('source_hash') == source_hash and out_path.exists():
                self.registry.append(existing)
                print(f"[skip] {out_name} unchanged")
                continue

            items = self.parse_python_file(filepath)
            if not items:
                continue

            md = self.render_markdown(filepath, items)

            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(md, encoding='utf-8')

            self.registry.append({
                'source': str(filepath),
                'output': str(out_path),
                'items': len(items),
                'hash': self._hash_bytes(md.encode()),
                'source_hash': source_hash,
                'generated_at': datetime.now().isoformat()
            })
            print(f"[gen]  {out_name} -> {len(items)} items documented")

        # Write registry
        reg_path = self.output_dir / 'registry.json'
        reg_path.write_text(json.dumps(self.registry, indent=2))

        print(f"\n{'='*50}")
        print(f"[done] Generated docs for {len(self.registry)} files")
        print(f"[done] Registry saved to {reg_path}")
        print(f"[done] Output directory: {self.output_dir}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Code-Aware Documentation Generator')
    parser.add_argument('--source', required=True, help='Source directory to scan')
    parser.add_argument('--output', default='./docs', help='Output directory for docs')
    args = parser.parse_args()

    gen = CodeAwareDocGenerator(args.source, args.output)
    gen.run()
