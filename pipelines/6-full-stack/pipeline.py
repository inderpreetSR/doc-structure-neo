"""
Pipeline 6: Full-Stack Documentation Pipeline
Orchestrates all 5 pipelines into one production-grade system.
Run: python pipeline.py --project ./your-project --output ./docs
"""

import os
import re
import ast
import json
import time
import hashlib
import argparse
from pathlib import Path
from datetime import datetime


class FullStackDocPipeline:
    """
    Production-grade orchestrator combining all 5 pipelines:
    1. Code-Aware Analysis (AST parsing)
    2. Git-Driven Change Detection (hash-based)
    3. RAG Vector Indexing (search chunks)
    4. Living Docs (tests, specs, features)
    5. Site Generation (HTML output)
    """

    DEFAULT_CONFIG = {
        'extensions': ['.py', '.js', '.ts', '.jsx', '.tsx', '.md'],
        'ignore_patterns': ['.git', 'node_modules', '__pycache__', '.venv', 'venv'],
        'output_format': 'html'
    }

    def __init__(self, project_dir, output_dir, config=None):
        self.project_dir = Path(project_dir).resolve()
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or self.DEFAULT_CONFIG
        self.report = {
            'started': datetime.now().isoformat(),
            'project': str(self.project_dir),
            'stages': [],
            'errors': []
        }

    def _should_skip(self, filepath):
        rel = str(filepath)
        return any(p in rel for p in self.config['ignore_patterns'])

    # ---- Stage 1: Change Detection ----

    def stage_change_detection(self):
        """Detect what changed since last run using content hashes."""
        stage = {'name': 'change_detection', 'started': time.time()}
        cache_file = self.output_dir / '.doc-cache.json'
        old_cache = {}
        if cache_file.exists():
            old_cache = json.loads(cache_file.read_text())

        new_cache = {}
        changed_files = []

        for ext in self.config['extensions']:
            for filepath in self.project_dir.rglob(f'*{ext}'):
                if self._should_skip(filepath):
                    continue
                rel = str(filepath.relative_to(self.project_dir))
                content_hash = hashlib.md5(filepath.read_bytes()).hexdigest()
                new_cache[rel] = content_hash
                if old_cache.get(rel) != content_hash:
                    changed_files.append(rel)

        cache_file.write_text(json.dumps(new_cache, indent=2))

        stage['changed_files'] = len(changed_files)
        stage['total_files'] = len(new_cache)
        stage['elapsed'] = round(time.time() - stage['started'], 3)
        self.report['stages'].append(stage)
        print(f"[stage 1] Change detection: {len(changed_files)}/{len(new_cache)} files changed")
        return changed_files

    # ---- Stage 2: Code Analysis ----

    def stage_code_analysis(self, files_to_analyze=None):
        """Analyze Python source code via AST."""
        stage = {'name': 'code_analysis', 'started': time.time()}
        analysis = {}

        py_files = list(self.project_dir.rglob('*.py'))
        if files_to_analyze:
            py_files = [self.project_dir / f for f in files_to_analyze if f.endswith('.py')]

        for filepath in py_files:
            if not filepath.exists() or self._should_skip(filepath):
                continue
            rel = str(filepath.relative_to(self.project_dir))
            try:
                source = filepath.read_text(encoding='utf-8')
                tree = ast.parse(source)
                items = {
                    'module_doc': ast.get_docstring(tree) or '',
                    'functions': [],
                    'classes': [],
                    'lines': len(source.splitlines())
                }
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        items['functions'].append({
                            'name': node.name,
                            'args': [a.arg for a in node.args.args],
                            'doc': ast.get_docstring(node) or '',
                            'line': node.lineno
                        })
                    elif isinstance(node, ast.ClassDef):
                        items['classes'].append({
                            'name': node.name,
                            'doc': ast.get_docstring(node) or '',
                            'methods': [n.name for n in node.body
                                        if isinstance(n, ast.FunctionDef)],
                            'line': node.lineno
                        })
                analysis[rel] = items
            except Exception as e:
                self.report['errors'].append(f"Parse error in {rel}: {e}")

        stage['analyzed_files'] = len(analysis)
        stage['total_functions'] = sum(len(a['functions']) for a in analysis.values())
        stage['total_classes'] = sum(len(a['classes']) for a in analysis.values())
        stage['elapsed'] = round(time.time() - stage['started'], 3)
        self.report['stages'].append(stage)
        print(f"[stage 2] Code analysis: {len(analysis)} files, "
              f"{stage['total_functions']} functions, {stage['total_classes']} classes")
        return analysis

    # ---- Stage 3: RAG Indexing ----

    def stage_rag_indexing(self, analysis):
        """Create searchable chunks from analyzed code."""
        stage = {'name': 'rag_indexing', 'started': time.time()}
        chunks = []

        for filepath, items in analysis.items():
            if items['module_doc']:
                chunks.append({
                    'id': hashlib.md5(f"{filepath}:module".encode()).hexdigest(),
                    'text': items['module_doc'],
                    'source': filepath,
                    'type': 'module_doc'
                })
            for func in items['functions']:
                text = f"Function {func['name']}({', '.join(func['args'])})"
                if func['doc']:
                    text += f"\n{func['doc']}"
                chunks.append({
                    'id': hashlib.md5(f"{filepath}:{func['name']}".encode()).hexdigest(),
                    'text': text,
                    'source': filepath,
                    'type': 'function'
                })
            for cls in items['classes']:
                text = f"Class {cls['name']}"
                if cls['doc']:
                    text += f"\n{cls['doc']}"
                text += f"\nMethods: {', '.join(cls['methods'])}"
                chunks.append({
                    'id': hashlib.md5(f"{filepath}:{cls['name']}".encode()).hexdigest(),
                    'text': text,
                    'source': filepath,
                    'type': 'class'
                })

        index_path = self.output_dir / 'search-index.json'
        index_path.write_text(json.dumps(chunks, indent=2))

        stage['total_chunks'] = len(chunks)
        stage['elapsed'] = round(time.time() - stage['started'], 3)
        self.report['stages'].append(stage)
        print(f"[stage 3] RAG indexing: {len(chunks)} searchable chunks")
        return chunks

    # ---- Stage 4: Living Docs ----

    def stage_living_docs(self):
        """Count tests, features, and API specs."""
        stage = {'name': 'living_docs', 'started': time.time()}
        docs = {'features': 0, 'api_specs': 0, 'tests': 0}

        docs['features'] = len(list(self.project_dir.rglob('*.feature')))

        for pattern in ['**/openapi.*', '**/swagger.*']:
            docs['api_specs'] += len(list(self.project_dir.glob(pattern)))

        test_files = list(self.project_dir.rglob('test_*.py'))
        test_files += list(self.project_dir.rglob('*_test.py'))
        for tf in test_files:
            if self._should_skip(tf):
                continue
            source = tf.read_text(encoding='utf-8', errors='ignore')
            docs['tests'] += len(re.findall(r'def\s+test_\w+', source))

        stage.update(docs)
        stage['elapsed'] = round(time.time() - stage['started'], 3)
        self.report['stages'].append(stage)
        print(f"[stage 4] Living docs: {docs['features']} features, "
              f"{docs['api_specs']} API specs, {docs['tests']} tests")
        return docs

    # ---- Stage 5: HTML Site Generation ----

    def stage_site_generation(self, analysis, chunks, living_docs):
        """Generate the final HTML documentation site."""
        stage = {'name': 'site_generation', 'started': time.time()}
        site_dir = self.output_dir / 'site'
        site_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        pages = 0

        # Shared CSS
        css = """
:root { --bg:#0f0f1a; --s:#1a1a2e; --a:#00d4ff; --a2:#7b61ff; --t:#e0e0f0; --td:#8888aa; --b:#2a2a44; }
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:'Segoe UI',system-ui,sans-serif; background:var(--bg); color:var(--t); line-height:1.7; }
.container { max-width:960px; margin:0 auto; padding:2rem; }
h1 { font-size:2.5rem; background:linear-gradient(135deg,var(--a),var(--a2));
     -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:2rem 0 1rem; }
h2 { color:var(--a); margin:1.5rem 0 0.8rem; }
h3 { color:var(--a2); margin:1rem 0 0.5rem; }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:1rem; margin:1.5rem 0; }
.stat { background:var(--s); border:1px solid var(--b); border-radius:12px; padding:1.2rem; text-align:center; }
.stat .num { font-size:2rem; font-weight:800; color:var(--a); }
.stat .label { color:var(--td); font-size:0.85rem; }
a { color:var(--a); }
ul { list-style:none; }
ul li { padding:0.4rem 0.8rem; border-bottom:1px solid var(--b); }
ul li:hover { background:var(--s); }
code { font-family:'Cascadia Code','Consolas',monospace; color:var(--a); font-size:0.9rem; }
.search { width:100%; padding:0.8rem 1.2rem; background:var(--s); border:1px solid var(--b);
           border-radius:8px; color:var(--t); font-size:1rem; margin:1rem 0; }
.search::placeholder { color:var(--td); }
.item { background:var(--s); border:1px solid var(--b); border-radius:12px; padding:1.5rem; margin:1rem 0; }
.item h3 { color:var(--a); margin-bottom:0.5rem; }
.item p { color:var(--td); }
.back { color:var(--a); text-decoration:none; display:inline-block; margin-bottom:1rem; }
footer { text-align:center; color:var(--td); margin-top:3rem; padding:2rem; border-top:1px solid var(--b); }
"""
        (site_dir / 'style.css').write_text(css, encoding='utf-8')

        # ---- Index Page ----
        file_links = ''
        for fp in sorted(analysis.keys()):
            safe = fp.replace(os.sep, '_').replace('.', '_')
            file_links += f'<li><a href="{safe}.html"><code>{fp}</code></a></li>\n'

        total_funcs = sum(len(a['functions']) for a in analysis.values())
        total_classes = sum(len(a['classes']) for a in analysis.values())

        index_html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Project Documentation</title><link rel="stylesheet" href="style.css"></head><body>
<div class="container">
<h1>Project Documentation</h1>
<p style="color:var(--td)">Generated on {timestamp}</p>
<div class="stats">
<div class="stat"><div class="num">{len(analysis)}</div><div class="label">Files</div></div>
<div class="stat"><div class="num">{total_funcs}</div><div class="label">Functions</div></div>
<div class="stat"><div class="num">{total_classes}</div><div class="label">Classes</div></div>
<div class="stat"><div class="num">{len(chunks)}</div><div class="label">Search Chunks</div></div>
<div class="stat"><div class="num">{living_docs.get('tests',0)}</div><div class="label">Tests</div></div>
</div>
<input class="search" type="text" placeholder="Search files..." oninput="filterFiles(this.value)">
<h2>Modules</h2>
<ul id="file-list">{file_links}</ul>
</div>
<footer>Generated by Full-Stack Documentation Pipeline</footer>
<script>
function filterFiles(q){{const items=document.querySelectorAll('#file-list li');q=q.toLowerCase();
items.forEach(li=>{{li.style.display=li.textContent.toLowerCase().includes(q)?'':'none';}})}}
</script></body></html>"""
        (site_dir / 'index.html').write_text(index_html, encoding='utf-8')
        pages += 1

        # ---- Module Pages ----
        for filepath, items in analysis.items():
            safe = filepath.replace(os.sep, '_').replace('.', '_')

            classes_html = ''
            if items['classes']:
                classes_html = '<h2>Classes</h2>\n'
                for cls in items['classes']:
                    doc = f'<p>{cls["doc"]}</p>' if cls['doc'] else ''
                    methods = ', '.join(cls['methods']) if cls['methods'] else 'none'
                    classes_html += (f'<div class="item"><h3>class {cls["name"]}</h3>'
                                     f'{doc}<p><b>Methods:</b> {methods}</p>'
                                     f'<p style="font-size:0.8rem">Line {cls["line"]}</p></div>\n')

            funcs_html = ''
            if items['functions']:
                funcs_html = '<h2>Functions</h2>\n'
                for func in items['functions']:
                    args = ', '.join(func['args'])
                    doc = f'<p>{func["doc"]}</p>' if func['doc'] else ''
                    funcs_html += (f'<div class="item"><h3>{func["name"]}({args})</h3>'
                                    f'{doc}<p style="font-size:0.8rem">Line {func["line"]}</p></div>\n')

            module_doc = f'<p style="margin:1rem 0">{items["module_doc"]}</p>' if items['module_doc'] else ''

            page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{filepath}</title><link rel="stylesheet" href="style.css"></head><body>
<div class="container">
<a href="index.html" class="back">&larr; Back to index</a>
<h1><code>{filepath}</code></h1>
<p style="color:var(--td)">{items['lines']} lines</p>
{module_doc}
{classes_html}
{funcs_html}
</div>
<footer>Generated by Full-Stack Documentation Pipeline</footer>
</body></html>"""
            (site_dir / f'{safe}.html').write_text(page, encoding='utf-8')
            pages += 1

        stage['pages'] = pages
        stage['elapsed'] = round(time.time() - stage['started'], 3)
        self.report['stages'].append(stage)
        print(f"[stage 5] Site generation: {pages} HTML pages")
        return pages

    # ---- Orchestrator ----

    def run(self):
        """Run the full pipeline end-to-end."""
        print("=" * 60)
        print("  FULL-STACK DOCUMENTATION PIPELINE")
        print(f"  Project: {self.project_dir}")
        print(f"  Output:  {self.output_dir}")
        print("=" * 60)
        start = time.time()

        changed = self.stage_change_detection()
        analysis = self.stage_code_analysis(changed if changed else None)
        chunks = self.stage_rag_indexing(analysis)
        living = self.stage_living_docs()
        pages = self.stage_site_generation(analysis, chunks, living)

        elapsed = time.time() - start
        self.report['completed'] = datetime.now().isoformat()
        self.report['elapsed_seconds'] = round(elapsed, 2)
        self.report['stats'] = {
            'files_analyzed': len(analysis),
            'search_chunks': len(chunks),
            'pages_generated': pages,
            'errors': len(self.report['errors'])
        }

        report_path = self.output_dir / 'pipeline-report.json'
        report_path.write_text(json.dumps(self.report, indent=2))

        print()
        print("=" * 60)
        print(f"  COMPLETE in {elapsed:.1f}s")
        print(f"  Files: {len(analysis)} | Chunks: {len(chunks)} | Pages: {pages}")
        if self.report['errors']:
            print(f"  Errors: {len(self.report['errors'])}")
        print(f"  Report: {report_path}")
        print(f"  Site:   {self.output_dir / 'site' / 'index.html'}")
        print("=" * 60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Full-Stack Doc Pipeline')
    parser.add_argument('--project', required=True, help='Project directory')
    parser.add_argument('--output', default='./docs', help='Output directory')
    parser.add_argument('--config', help='Optional JSON config file')
    args = parser.parse_args()

    config = None
    if args.config:
        config = json.loads(Path(args.config).read_text())

    pipeline = FullStackDocPipeline(args.project, args.output, config)
    pipeline.run()
