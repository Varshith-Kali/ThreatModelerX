import os
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
class ArchitectureAnalyzer:
    def __init__(self):
        self.components = {}
        self.relationships = []
    def analyze(self, repo_path: str) -> Dict[str, Any]:
        self._reset()
        self._scan_directory(repo_path)
        self._infer_relationships()
        return {
            "components": list(self.components.values()),
            "relationships": self.relationships
        }
    def _reset(self):
        self.components = {}
        self.relationships = []
    def _scan_directory(self, directory: str):
        for root, dirs, files in os.walk(directory):
            if any(excluded in root for excluded in ['.git', 'node_modules', '__pycache__', '.venv']):
                continue
            for file in files:
                file_path = os.path.join(root, file)
                self._analyze_file(file_path, directory)
    def _analyze_file(self, file_path: str, base_path: str):
        relative_path = os.path.relpath(file_path, base_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in ['.pyc', '.jpg', '.png', '.gif', '.svg', '.ico', '.woff', '.ttf']:
            return
        try:
            if self._is_api_file(file_path, file_ext):
                self._extract_api_routes(file_path, relative_path)
            elif self._is_config_file(file_path, file_ext):
                self._extract_config_components(file_path, relative_path)
            elif self._is_ui_component(file_path, file_ext):
                self._add_ui_component(file_path, relative_path)
        except Exception as e:
            print(f"Error analyzing file {file_path}: {str(e)}")
    def _is_api_file(self, file_path: str, file_ext: str) -> bool:
        if file_ext in ['.py', '.js', '.ts']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return bool(re.search(r'@app\.(get|post|put|delete|patch)', content) or
                           re.search(r'router\.(get|post|put|delete|patch)', content) or
                           re.search(r'app\.(get|post|put|delete|patch)\(', content))
        return False
    def _is_config_file(self, file_path: str, file_ext: str) -> bool:
        config_patterns = [
            '.json', '.yaml', '.yml', '.toml', '.ini', '.config', 
            'config.js', 'config.ts', 'settings.py'
        ]
        return file_ext in config_patterns or any(pattern in file_path for pattern in config_patterns)
    def _is_ui_component(self, file_path: str, file_ext: str) -> bool:
        ui_extensions = ['.jsx', '.tsx', '.vue', '.svelte']
        return file_ext in ui_extensions or (
            file_ext in ['.js', '.ts'] and 
            ('component' in file_path.lower() or 'view' in file_path.lower())
        )
    def _extract_api_routes(self, file_path: str, relative_path: str):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            routes = []
            flask_routes = re.findall(r'@app\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', content)
            routes.extend([{'method': method.upper(), 'path': path} for method, path in flask_routes])
            express_routes = re.findall(r'(app|router)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', content)
            routes.extend([{'method': method.upper(), 'path': path} for _, method, path in express_routes])
            if routes:
                component_id = f"api-{Path(relative_path).stem}"
                self.components[component_id] = {
                    "id": component_id,
                    "name": f"API: {Path(relative_path).stem}",
                    "type": "api",
                    "file": relative_path,
                    "routes": routes
                }
    def _extract_config_components(self, file_path: str, relative_path: str):
        component_id = f"config-{Path(relative_path).stem}"
        self.components[component_id] = {
            "id": component_id,
            "name": f"Config: {Path(relative_path).stem}",
            "type": "config",
            "file": relative_path
        }
    def _add_ui_component(self, file_path: str, relative_path: str):
        component_id = f"ui-{Path(relative_path).stem}"
        self.components[component_id] = {
            "id": component_id,
            "name": f"UI: {Path(relative_path).stem}",
            "type": "ui",
            "file": relative_path
        }
    def _infer_relationships(self):
        component_files = {comp["file"]: comp_id for comp_id, comp in self.components.items()}
        for comp_id, component in self.components.items():
            file_path = component["file"]
            try:
                with open(os.path.join(os.getcwd(), file_path), 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    for other_file, other_id in component_files.items():
                        if other_file != file_path and Path(other_file).stem in content:
                            self.relationships.append({
                                "source": comp_id,
                                "target": other_id,
                                "type": "references"
                            })
            except Exception as e:
                print(f"Error analyzing relationships in {file_path}: {str(e)}")