"""
Pipeline 5: Multi-Source Aggregation
Collects docs from code comments, API schemas, diagrams, runbooks, and changelogs.
Run: python pipeline.py --project ./your-project --output ./docs-site
"""

import os
import re
import ast
import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None


class MultiSourceAggregator:
    """Aggregate documentation from multiple sources into a unified site."""

    def __init__(self, project_dir, output_dir):
        self.project_dir = Path(project_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = {
            'generated': datetime.now().isoformat(),
            'project': str(self.project_dir),
            'sections': []
        }

    def _new_section(self, name, section_type, output_dir):
        return {'name': name, 'type': section_type, 'output_dir': output_dir, 'items': []}

    def _safe_name(self, rel_path):
        safe = rel_path.replace(os.sep, '_').replace('/', '_')
        safe = re.sub(r'[^A-Za-z0-9._-]', '_', safe)
        return safe.strip('_')

    def _build_output(self, section, rel_path, ext='.md'):
        safe = self._safe_name(rel_path)
        if not safe.lower().endswith(ext):
            safe = f"{safe}{ext}"
        out_rel = f"{section['output_dir']}/{safe}"
        return self.output_dir / out_rel, out_rel

    # ---- Collectors ----

    def collect_readmes(self):
        """Collect all README files."""
        readmes = list(self.project_dir.rglob('README*'))
        section = self._new_section('Getting Started', 'readme', 'getting-started')

        for readme in readmes:
            if '.git' in str(readme):
                continue
            rel = str(readme.relative_to(self.project_dir))
            content = readme.read_text(encoding='utf-8', errors='ignore')
            out_path, out_rel = self._build_output(section, rel)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content, encoding='utf-8')
            section['items'].append({'source': rel, 'output': out_rel})
            print(f"[readme]   {rel}")

        self.manifest['sections'].append(section)
        return section

    def collect_runbooks(self):
        """Collect operational runbooks and guides."""
        doc_dirs = ['docs', 'runbooks', 'guides', 'wiki', 'documentation']
        section = self._new_section('Operations & Guides', 'runbooks', 'guides')

        for d in doc_dirs:
            doc_path = self.project_dir / d
            if doc_path.exists():
                for md_file in doc_path.rglob('*.md'):
                    rel = str(md_file.relative_to(self.project_dir))
                    content = md_file.read_text(encoding='utf-8', errors='ignore')
                    out_path, out_rel = self._build_output(section, rel)
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(content, encoding='utf-8')
                    section['items'].append({'source': rel, 'output': out_rel})
                    print(f"[guide]    {rel}")

        self.manifest['sections'].append(section)
        return section

    def collect_diagrams(self):
        """Collect Mermaid and PlantUML diagram files."""
        diagram_exts = ('.mmd', '.mermaid', '.puml', '.plantuml')
        section = self._new_section('Architecture Diagrams', 'diagrams', 'architecture')

        for ext in diagram_exts:
            for diagram in self.project_dir.rglob(f'*{ext}'):
                rel = str(diagram.relative_to(self.project_dir))
                content = diagram.read_text(encoding='utf-8', errors='ignore')
                lang = 'mermaid' if ext in ('.mmd', '.mermaid') else 'plantuml'
                md = f"# {diagram.stem}\n\n```{lang}\n{content}\n```\n"
                out_path, out_rel = self._build_output(section, rel)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(md, encoding='utf-8')
                section['items'].append({'source': rel, 'output': out_rel})
                print(f"[diagram]  {rel}")

        self.manifest['sections'].append(section)
        return section

    def collect_api_schemas(self):
        """Collect OpenAPI and GraphQL schemas."""
        section = self._new_section('API Reference', 'api', 'api')
        patterns = ['**/openapi.*', '**/swagger.*', '**/*.graphql']

        for pattern in patterns:
            for schema in self.project_dir.glob(pattern):
                if '.git' in str(schema):
                    continue
                rel = str(schema.relative_to(self.project_dir))
                content = schema.read_text(encoding='utf-8', errors='ignore')
                md = f"# API: {schema.stem}\n\n*Source: `{rel}`*\n\n"
                md += f"```{schema.suffix.lstrip('.')}\n{content}\n```\n"
                out_path, out_rel = self._build_output(section, rel)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(md, encoding='utf-8')
                section['items'].append({'source': rel, 'output': out_rel})
                print(f"[api]      {rel}")

        self.manifest['sections'].append(section)
        return section

    def collect_changelog(self):
        """Collect CHANGELOG and release notes."""
        section = self._new_section('Version History', 'changelog', 'changelog')
        names = ['CHANGELOG.md', 'CHANGELOG', 'CHANGES.md', 'HISTORY.md', 'RELEASES.md']

        for name in names:
            changelog = self.project_dir / name
            if changelog.exists():
                content = changelog.read_text(encoding='utf-8', errors='ignore')
                out_path, out_rel = self._build_output(section, name)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                out_path.write_text(content, encoding='utf-8')
                section['items'].append({'source': name, 'output': out_rel})
                print(f"[log]      {name}")

        self.manifest['sections'].append(section)
        return section

    def collect_code_comments(self):
        """Extract top-level module docstrings from Python files."""
        section = self._new_section('Code Reference', 'code', 'code-reference')
        ignore = {'.git', 'node_modules', '__pycache__', '.venv', 'venv'}

        for pyfile in sorted(self.project_dir.rglob('*.py')):
            if any(d in pyfile.parts for d in ignore):
                continue
            try:
                source = pyfile.read_text(encoding='utf-8')
                tree = ast.parse(source)
                docstring = ast.get_docstring(tree)
                if docstring:
                    rel = str(pyfile.relative_to(self.project_dir))
                    md = f"# `{rel}`\n\n{docstring}\n"
                    out_path, out_rel = self._build_output(section, rel)
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(md, encoding='utf-8')
                    section['items'].append({'source': rel, 'output': out_rel})
                    print(f"[code]     {rel}")
            except Exception:
                pass

        self.manifest['sections'].append(section)
        return section

    # ---- Site Generator ----

    def generate_index(self):
        """Generate a unified index page."""
        md = "# Documentation Hub\n\n"
        md += f"*Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n---\n\n"

        for section in self.manifest['sections']:
            if section['items']:
                md += f"## {section['name']}\n\n"
                for item in section['items']:
                    md += f"- [{item['source']}]({item['output']})\n"
                md += "\n"

        total = sum(len(s['items']) for s in self.manifest['sections'])
        md += f"---\n\n*{total} documents from {len(self.manifest['sections'])} sources*\n"

        (self.output_dir / 'index.md').write_text(md, encoding='utf-8')

        # Save manifest
        manifest_path = self.output_dir / 'manifest.json'
        manifest_path.write_text(json.dumps(self.manifest, indent=2))
        print(f"\n[index]    Generated index ({total} documents)")

    def generate_section_indexes(self):
        """Generate per-section index pages for MkDocs navigation."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        for section in self.manifest['sections']:
            if not section['items']:
                continue
            section_dir = self.output_dir / section['output_dir']
            section_dir.mkdir(parents=True, exist_ok=True)
            md = f"# {section['name']}\n\n*Auto-generated on {timestamp}*\n\n"
            for item in section['items']:
                link = Path(item['output']).name
                md += f"- [{item['source']}]({link})\n"
            (section_dir / 'index.md').write_text(md, encoding='utf-8')

    def generate_mkdocs_config(self):
        """Generate an MkDocs configuration file."""
        if not yaml:
            print("[warn]    PyYAML not installed, skipping mkdocs.yml generation")
            return

        config = {
            'site_name': 'Project Documentation',
            'theme': {'name': 'material'},
            'nav': [{'Home': 'index.md'}]
        }
        for section in self.manifest['sections']:
            if section['items']:
                config['nav'].append({section['name']: f"{section['output_dir']}/index.md"})

        config_path = self.output_dir / 'mkdocs.yml'
        config_path.write_text(yaml.dump(config, default_flow_style=False))
        print(f"[mkdocs]   Generated mkdocs.yml")

    def run(self):
        """Execute the full aggregation pipeline."""
        print(f"{'='*50}")
        print(f"Multi-Source Documentation Aggregator")
        print(f"{'='*50}")

        self.collect_readmes()
        self.collect_runbooks()
        self.collect_diagrams()
        self.collect_api_schemas()
        self.collect_changelog()
        self.collect_code_comments()
        self.generate_index()
        self.generate_section_indexes()
        self.generate_mkdocs_config()

        total = sum(len(s['items']) for s in self.manifest['sections'])
        print(f"\n{'='*50}")
        print(f"[done]     {total} documents aggregated into {self.output_dir}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Multi-Source Doc Aggregator')
    parser.add_argument('--project', required=True, help='Project directory')
    parser.add_argument('--output', default='./docs-site', help='Output directory')
    args = parser.parse_args()

    agg = MultiSourceAggregator(args.project, args.output)
    agg.run()
