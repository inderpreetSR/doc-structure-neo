"""
Pipeline 2: Git-Driven Change Detection
Detects changed files via git diff, builds dependency graph, and selectively regenerates docs.
Run: python pipeline.py --repo ./your-repo --output ./docs
"""

import subprocess
import re
import os
import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime


class GitDrivenDocPipeline:
    """Detects git changes and selectively regenerates docs."""

    def __init__(self, repo_dir, output_dir, base_ref='HEAD~1'):
        self.repo_dir = Path(repo_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.base_ref = base_ref
        self.dep_graph = defaultdict(set)
        self.import_map = defaultdict(set)

    def get_changed_files(self):
        """Get list of changed files from git diff."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', self.base_ref],
                cwd=self.repo_dir, capture_output=True, text=True, timeout=30
            )
            files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            print(f"[diff]    {len(files)} files changed since {self.base_ref}")
            return files
        except subprocess.TimeoutExpired:
            print("[warn]    git diff timed out, scanning all files")
            return [str(f.relative_to(self.repo_dir))
                    for f in self.repo_dir.rglob('*.py')]
        except FileNotFoundError:
            print("[warn]    git not found, scanning all files")
            return [str(f.relative_to(self.repo_dir))
                    for f in self.repo_dir.rglob('*.py')]

    def build_dependency_graph(self):
        """Parse imports to build a dependency graph."""
        py_files = list(self.repo_dir.rglob('*.py'))
        import_pattern = re.compile(
            r'^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))', re.MULTILINE
        )
        for filepath in py_files:
            module = str(filepath.relative_to(self.repo_dir)).replace(os.sep, '.').rstrip('.py')
            try:
                source = filepath.read_text(encoding='utf-8')
            except Exception:
                continue
            for match in import_pattern.finditer(source):
                imported = match.group(1) or match.group(2)
                self.import_map[module].add(imported)
                self.dep_graph[imported].add(module)

        print(f"[graph]   Built dependency graph: {len(self.dep_graph)} modules")
        return self.dep_graph

    def resolve_affected(self, changed_files):
        """Resolve all affected modules (direct + transitive dependents)."""
        changed_modules = set()
        for f in changed_files:
            if f.endswith('.py'):
                mod = f.replace(os.sep, '.').rstrip('.py')
                changed_modules.add(mod)

        affected = set(changed_modules)
        queue = list(changed_modules)
        visited = set()
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            for dependent in self.dep_graph.get(current, set()):
                if dependent not in affected:
                    affected.add(dependent)
                    queue.append(dependent)

        print(f"[resolve] {len(changed_modules)} changed -> {len(affected)} affected modules")
        return affected

    def regenerate_docs(self, affected_modules):
        """Regenerate documentation only for affected modules."""
        regenerated = []
        for module in sorted(affected_modules):
            mod_path = self.repo_dir / module.replace('.', os.sep)
            candidates = [mod_path.with_suffix('.py'), mod_path / '__init__.py']
            for candidate in candidates:
                if candidate.exists():
                    doc_content = self._generate_doc(candidate, module)
                    out_path = self.output_dir / f"{module.replace('.', '_')}.md"
                    out_path.write_text(doc_content, encoding='utf-8')
                    regenerated.append(module)
                    print(f"[regen]   {module}")
                    break
        return regenerated

    def _generate_doc(self, filepath, module_name):
        """Generate a Markdown doc for a module."""
        source = filepath.read_text(encoding='utf-8')
        line_count = len(source.splitlines())
        imports = self.import_map.get(module_name, set())
        dependents = self.dep_graph.get(module_name, set())

        md = f"# {module_name}\n\n"
        md += f"*Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        md += f"**Source:** `{filepath.relative_to(self.repo_dir)}`  \n"
        md += f"**Lines:** {line_count}  \n\n"
        if imports:
            md += f"**Imports:** {', '.join(f'`{i}`' for i in sorted(imports))}\n\n"
        if dependents:
            md += f"**Used by:** {', '.join(f'`{d}`' for d in sorted(dependents))}\n\n"
        md += "---\n\n"
        md += "```python\n" + source[:3000] + "\n```\n"
        return md

    def run(self):
        """Execute the full pipeline."""
        print(f"{'='*50}")
        print(f"Git-Driven Change Detection Pipeline")
        print(f"{'='*50}")

        changed = self.get_changed_files()
        if not changed:
            print("[done]    No changes detected, nothing to regenerate.")
            return

        self.build_dependency_graph()
        affected = self.resolve_affected(changed)
        regenerated = self.regenerate_docs(affected)

        report = {
            'timestamp': datetime.now().isoformat(),
            'base_ref': self.base_ref,
            'changed_files': changed,
            'affected_modules': list(affected),
            'regenerated': regenerated
        }
        report_path = self.output_dir / 'build-report.json'
        report_path.write_text(json.dumps(report, indent=2))

        print(f"\n{'='*50}")
        print(f"[done]    Regenerated {len(regenerated)} docs")
        print(f"[done]    Report: {report_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Git-Driven Doc Pipeline')
    parser.add_argument('--repo', required=True, help='Git repository path')
    parser.add_argument('--output', default='./docs', help='Output directory')
    parser.add_argument('--base-ref', default='HEAD~1', help='Git base reference')
    args = parser.parse_args()

    pipeline = GitDrivenDocPipeline(args.repo, args.output, args.base_ref)
    pipeline.run()
