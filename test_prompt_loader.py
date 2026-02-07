"""Unit tests for prompt_loader.py"""
import pytest
import tempfile
import os
from pathlib import Path
from prompt_loader import PromptLoader
from jinja2 import TemplateNotFound


class TestPromptLoader:
    """Test PromptLoader class"""
    
    def test_init_with_nonexistent_dir(self):
        """Test initialization with non-existent directory raises error"""
        with pytest.raises(FileNotFoundError) as exc_info:
            PromptLoader("nonexistent_dir")
        assert "Templates directory not found" in str(exc_info.value)
    
    def test_init_with_existing_dir(self):
        """Test successful initialization with existing directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = PromptLoader(temp_dir)
            assert loader.templates_dir == Path(temp_dir)
            assert loader.env is not None
    
    def test_render_simple_template(self):
        """Test rendering a simple template"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test template
            template_path = Path(temp_dir) / "test.j2"
            template_path.write_text("Hello {{ name }}!")
            
            loader = PromptLoader(temp_dir)
            result = loader.render("test.j2", name="World")
            
            assert result == "Hello World!"
    
    def test_render_with_variables(self):
        """Test rendering template with multiple variables"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create template with multiple variables
            template_content = """
Job: {{ job_title }}
Experience: {{ years }} years
Skills: {% for skill in skills %}{{ skill }}{% if not loop.last %}, {% endif %}{% endfor %}
"""
            template_path = Path(temp_dir) / "job.j2"
            template_path.write_text(template_content)
            
            loader = PromptLoader(temp_dir)
            result = loader.render("job.j2", 
                                 job_title="Python Developer",
                                 years=5,
                                 skills=["Python", "Django", "SQL"])
            
            assert "Job: Python Developer" in result
            assert "Experience: 5 years" in result
            assert "Skills: Python, Django, SQL" in result
    
    def test_render_nonexistent_template(self):
        """Test rendering non-existent template raises error"""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = PromptLoader(temp_dir)
            
            with pytest.raises(RuntimeError) as exc_info:
                loader.render("nonexistent.j2")
            assert "Error rendering template" in str(exc_info.value)
    
    def test_get_version_with_header(self):
        """Test extracting version from template header"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create template with version header
            template_content = """
{# Version: 1.2.3 #}
{# Description: Test template #}
Hello {{ name }}!
"""
            template_path = Path(temp_dir) / "versioned.j2"
            template_path.write_text(template_content)
            
            loader = PromptLoader(temp_dir)
            version = loader.get_version("versioned.j2")
            
            assert version == "1.2.3"
    
    def test_get_version_without_header(self):
        """Test version extraction for template without version header"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create template without version
            template_path = Path(temp_dir) / "unversioned.j2"
            template_path.write_text("Hello {{ name }}!")
            
            loader = PromptLoader(temp_dir)
            version = loader.get_version("unversioned.j2")
            
            assert version == "unknown"
    
    def test_get_version_caching(self):
        """Test that version info is cached after first lookup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_content = "{# Version: 2.0.0 #}\nTest content"
            template_path = Path(temp_dir) / "cached.j2"
            template_path.write_text(template_content)
            
            loader = PromptLoader(temp_dir)
            
            # First call should read from file
            version1 = loader.get_version("cached.j2")
            
            # Second call should use cache
            version2 = loader.get_version("cached.j2")
            
            assert version1 == version2 == "2.0.0"
            assert "cached.j2" in loader._version_cache
