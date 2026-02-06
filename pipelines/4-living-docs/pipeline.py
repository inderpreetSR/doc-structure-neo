"""
Pipeline 4: Living Documentation from Tests & Specs
Generates documentation from BDD feature files, OpenAPI schemas, and test files.
Run: python pipeline.py --project ./your-project --output ./docs
"""

import os
import re
import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    yaml = None


class LivingDocsPipeline:
    """Generate documentation from tests, specs, and API schemas."""

    def __init__(self, project_dir, output_dir):
        self.project_dir = Path(project_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ---- BDD / Gherkin Feature Files ----

    def parse_feature_files(self):
        """Parse .feature files (Gherkin syntax) into documentation."""
        features = list(self.project_dir.rglob('*.feature'))
        print(f"[bdd]    Found {len(features)} feature files")

        parsed = []
        for fpath in features:
            content = fpath.read_text(encoding='utf-8', errors='ignore')
            feature_match = re.search(r'Feature:\s*(.+)', content)
            scenario_pattern = re.compile(
                r'(Scenario(?:\s+Outline)?):\s*(.+)',
                re.MULTILINE
            )
            given_when_then = re.findall(
                r'(Given|When|Then|And|But)\s+(.+)', content
            )

            feature_name = feature_match.group(1).strip() if feature_match else fpath.stem
            scenarios = [m.group(2).strip() for m in scenario_pattern.finditer(content)]

            parsed.append({
                'type': 'feature',
                'name': feature_name,
                'file': str(fpath.relative_to(self.project_dir)),
                'scenarios': scenarios,
                'steps': len(given_when_then),
                'raw': content
            })
        return parsed

    # ---- OpenAPI / Swagger ----

    def parse_openapi_specs(self):
        """Parse OpenAPI/Swagger YAML/JSON specs."""
        spec_patterns = [
            '**/openapi.yaml', '**/openapi.yml', '**/openapi.json',
            '**/swagger.yaml', '**/swagger.yml', '**/swagger.json'
        ]
        specs = []
        for pattern in spec_patterns:
            specs.extend(self.project_dir.glob(pattern))

        print(f"[api]    Found {len(specs)} OpenAPI specs")

        parsed = []
        for spec_path in specs:
            content = spec_path.read_text(encoding='utf-8', errors='ignore')
            if spec_path.suffix == '.json':
                spec = json.loads(content)
            elif yaml:
                spec = yaml.safe_load(content)
            else:
                print(f"[warn]   PyYAML not installed, skipping {spec_path.name}")
                continue

            info = spec.get('info', {})
            paths = spec.get('paths', {})
            endpoints = []
            for path, methods in paths.items():
                for method, details in methods.items():
                    if method in ('get', 'post', 'put', 'patch', 'delete', 'head', 'options'):
                        params = details.get('parameters', [])
                        endpoints.append({
                            'method': method.upper(),
                            'path': path,
                            'summary': details.get('summary', ''),
                            'description': details.get('description', ''),
                            'tags': details.get('tags', []),
                            'parameters': len(params),
                            'responses': list(details.get('responses', {}).keys())
                        })

            parsed.append({
                'type': 'api',
                'title': info.get('title', 'API'),
                'version': info.get('version', ''),
                'description': info.get('description', ''),
                'endpoints': endpoints,
                'file': str(spec_path.relative_to(self.project_dir))
            })
        return parsed

    # ---- Test File Scanner ----

    def parse_test_files(self):
        """Scan test files for documented test cases."""
        test_files = list(self.project_dir.rglob('test_*.py'))
        test_files += list(self.project_dir.rglob('*_test.py'))
        test_files = list(set(test_files))
        print(f"[test]   Found {len(test_files)} test files")

        parsed = []
        test_pattern = re.compile(
            r'def\s+(test_\w+)\s*\(.*?\):\s*\n\s*"""(.*?)"""',
            re.DOTALL
        )

        for tpath in sorted(test_files):
            source = tpath.read_text(encoding='utf-8', errors='ignore')
            documented = []
            for match in test_pattern.finditer(source):
                documented.append({
                    'name': match.group(1),
                    'description': match.group(2).strip()
                })

            all_tests = re.findall(r'def\s+(test_\w+)', source)
            total = len(all_tests)

            parsed.append({
                'type': 'tests',
                'file': str(tpath.relative_to(self.project_dir)),
                'documented_tests': documented,
                'all_test_names': all_tests,
                'total_tests': total,
                'doc_coverage': len(documented) / max(total, 1) * 100
            })
        return parsed

    # ---- Markdown Renderer ----

    def render_docs(self, features, apis, tests):
        """Render all parsed sources into Markdown documentation."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        # 1. Features doc
        if features:
            md = f"# Feature Documentation\n\n*Generated: {timestamp}*\n\n"
            total_scenarios = sum(len(f['scenarios']) for f in features)
            md += f"**{len(features)} features** with **{total_scenarios} scenarios**\n\n---\n\n"
            for feat in features:
                md += f"## {feat['name']}\n\n"
                md += f"*Source: `{feat['file']}`* | {feat['steps']} steps\n\n"
                if feat['scenarios']:
                    md += "### Scenarios\n\n"
                    for s in feat['scenarios']:
                        md += f"- {s}\n"
                    md += "\n"
            (self.output_dir / 'features.md').write_text(md, encoding='utf-8')
            print(f"[write]  features.md ({len(features)} features)")

        # 2. API docs
        if apis:
            md = f"# API Documentation\n\n*Generated: {timestamp}*\n\n"
            for api in apis:
                md += f"## {api['title']} v{api['version']}\n\n"
                md += f"{api['description']}\n\n"
                md += "| Method | Path | Summary | Params | Responses |\n"
                md += "|--------|------|---------|--------|-----------|\n"
                for ep in api['endpoints']:
                    responses = ', '.join(ep['responses'])
                    md += (f"| `{ep['method']}` | `{ep['path']}` | "
                           f"{ep['summary']} | {ep['parameters']} | {responses} |\n")
                md += "\n"
            (self.output_dir / 'api.md').write_text(md, encoding='utf-8')
            print(f"[write]  api.md ({sum(len(a['endpoints']) for a in apis)} endpoints)")

        # 3. Test docs
        if tests:
            md = f"# Test Documentation\n\n*Generated: {timestamp}*\n\n"
            total_tests = sum(t['total_tests'] for t in tests)
            total_documented = sum(len(t['documented_tests']) for t in tests)
            pct = total_documented / max(total_tests, 1) * 100
            md += f"**Total tests:** {total_tests}  \n"
            md += f"**Documented:** {total_documented} ({pct:.0f}%)\n\n---\n\n"
            for t in sorted(tests, key=lambda x: x['file']):
                md += f"## `{t['file']}`\n\n"
                md += (f"Tests: {t['total_tests']} | Documented: "
                       f"{len(t['documented_tests'])} | Coverage: {t['doc_coverage']:.0f}%\n\n")
                for dt in t['documented_tests']:
                    md += f"### `{dt['name']}`\n\n{dt['description']}\n\n"
                if t['all_test_names']:
                    undoc = [n for n in t['all_test_names']
                             if n not in [d['name'] for d in t['documented_tests']]]
                    if undoc:
                        md += "**Undocumented:** " + ', '.join(f'`{n}`' for n in undoc) + "\n\n"
            (self.output_dir / 'tests.md').write_text(md, encoding='utf-8')
            print(f"[write]  tests.md ({total_tests} tests)")

        # 4. Index
        md = f"# Living Documentation Index\n\n*Generated: {timestamp}*\n\n"
        md += f"| Section | Count |\n|---------|-------|\n"
        md += f"| [Feature Specs](features.md) | {len(features)} features |\n"
        md += f"| [API Endpoints](api.md) | {sum(len(a['endpoints']) for a in apis)} endpoints |\n"
        md += f"| [Test Cases](tests.md) | {sum(t['total_tests'] for t in tests)} tests |\n"
        (self.output_dir / 'index.md').write_text(md, encoding='utf-8')

    def run(self):
        """Execute the full pipeline."""
        print(f"{'='*50}")
        print(f"Living Documentation Pipeline")
        print(f"{'='*50}")

        features = self.parse_feature_files()
        apis = self.parse_openapi_specs()
        tests = self.parse_test_files()
        self.render_docs(features, apis, tests)

        print(f"\n{'='*50}")
        print(f"[done]   Living docs generated in {self.output_dir}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Living Docs Pipeline')
    parser.add_argument('--project', required=True, help='Project directory')
    parser.add_argument('--output', default='./docs', help='Output directory')
    args = parser.parse_args()

    pipeline = LivingDocsPipeline(args.project, args.output)
    pipeline.run()
