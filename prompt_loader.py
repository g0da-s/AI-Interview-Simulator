"""Utility for loading and rendering Jinja2 prompt templates"""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
from typing import Dict, Any
import re


class PromptLoader:
    """Manages loading and rendering of prompt templates with version tracking"""
    def __init__(self, templates_dir: str = "prompts"):
        """
        Initialize the prompt loader

        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = Path(templates_dir)
        if not self.templates_dir.exists():
            raise FileNotFoundError(
                f"Templates directory not found: {self.templates_dir}. "
                "Please create it and add your .j2 template files."
            )

        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )

        self._version_cache: Dict[str, str] = {}

    def render(self, template_name: str, **kwargs: Any) -> str:
        """
        Render a template with given variables
        
        Args:
            template_name: Name of the template file (e.g., 'system_prompt.j2')
            **kwargs: Variables to pass to the template
            
        Returns:
            Rendered template as string
            
        Example:
            loader = PromptLoader()
            prompt = loader.render('system_prompt.j2', 
                                  job_description="Senior Python Developer",
                                  max_questions=7)
        """
        try:
            template = self.env.get_template(template_name)
            return template.render(**kwargs)
        except Exception as e:
            raise RuntimeError(f"Error rendering template '{template_name}': {str(e)}")
    
    def get_version(self, template_name: str) -> str:
        """
        Extract version number from template file header comment

        Looks for version info in Jinja2 comment format:
        {# PROMPT VERSION: 1.2 | Last Updated: 2025-12-04 | Changes: ... #}

        Args:
            template_name: Name of the template file

        Returns:
            Version string (e.g., "1.2") or "unknown" if not found
        """
        if template_name in self._version_cache:
            return self._version_cache[template_name]

        try:
            template_path = self.templates_dir / template_name
            with open(template_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()

            version_pattern = r'\{#\s*PROMPT VERSION:\s*([\d.]+)'
            match = re.search(version_pattern, first_line)

            if match:
                version = match.group(1)
                self._version_cache[template_name] = version
                return version
            else:
                self._version_cache[template_name] = "unknown"
                return "unknown"

        except Exception:
            return "unknown"

    def get_all_versions(self) -> Dict[str, str]:
        """
        Get version information for all prompt templates

        Returns:
            Dictionary mapping template names to version strings
        """
        versions = {}
        for template_file in self.list_templates():
            versions[template_file] = self.get_version(template_file)
        return versions

    def list_templates(self) -> list:
        """List all available template files"""
        return [f.name for f in self.templates_dir.glob("*.j2")]


prompt_loader = PromptLoader()