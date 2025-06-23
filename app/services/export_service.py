import os
import json
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from pathlib import Path
import httpx

logger = logging.getLogger(__name__)

class ExportService:
    """
    Export service for generating downloadable files in various formats
    Supports: HTML, SVG, PNG (via conversion), JSON
    """
    
    def __init__(self):
        # Create exports directory
        self.exports_dir = Path("exports")
        self.exports_dir.mkdir(exist_ok=True)
    
    async def export_screens_html(
        self, 
        screens: List[Dict[str, Any]], 
        project_name: str = "TUX Export"
    ) -> str:
        """
        Export screens as a complete HTML file with embedded styles
        
        Args:
            screens: List of screen data
            project_name: Name of the project
            
        Returns:
            HTML content as string
        """
        try:
            html_parts = [self._generate_html_header(project_name)]
            
            # Add navigation
            html_parts.append(self._generate_navigation(screens))
            
            # Add each screen
            for i, screen in enumerate(screens):
                html_parts.append(self._generate_screen_section(screen, i))
            
            # Add footer and scripts
            html_parts.append(self._generate_html_footer())
            
            return '\n'.join(html_parts)
            
        except Exception as e:
            logger.error(f"Failed to export HTML: {str(e)}")
            raise
    
    def _generate_html_header(self, project_name: str) -> str:
        """Generate HTML header with styles"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - TUX UX Design</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f8fafc;
            color: #1f2937;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 3rem;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            color: #3b82f6;
            margin-bottom: 0.5rem;
        }}
        
        .header p {{
            color: #6b7280;
            font-size: 1.125rem;
        }}
        
        .navigation {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .navigation h2 {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: #1f2937;
        }}
        
        .nav-links {{
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
        }}
        
        .nav-link {{
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: #3b82f6;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: all 0.2s;
        }}
        
        .nav-link:hover {{
            background: #2563eb;
            transform: translateY(-2px);
        }}
        
        .screen-section {{
            background: white;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .screen-header {{
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 1rem;
            margin-bottom: 2rem;
        }}
        
        .screen-header h3 {{
            font-size: 1.875rem;
            color: #1f2937;
            margin-bottom: 0.5rem;
        }}
        
        .screen-description {{
            color: #6b7280;
            font-size: 1.125rem;
        }}
        
        .screen-content {{
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            min-height: 400px;
        }}
        
        .screen-elements {{
            margin-top: 1.5rem;
        }}
        
        .screen-elements h4 {{
            font-size: 1.25rem;
            color: #374151;
            margin-bottom: 1rem;
        }}
        
        .elements-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
        }}
        
        .element-tag {{
            display: inline-block;
            padding: 0.5rem 1rem;
            background: #e0e7ff;
            color: #4338ca;
            border-radius: 6px;
            font-size: 0.875rem;
        }}
        
        .export-info {{
            margin-top: 3rem;
            padding: 1.5rem;
            background: #f3f4f6;
            border-radius: 8px;
            text-align: center;
            color: #6b7280;
        }}
        
        @media print {{
            .navigation {{
                display: none;
            }}
            .screen-section {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{project_name}</h1>
            <p>UX Design Specifications - Generated by TUX</p>
            <p style="margin-top: 0.5rem; font-size: 0.875rem;">
                Exported on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
            </p>
        </div>"""
    
    def _generate_navigation(self, screens: List[Dict[str, Any]]) -> str:
        """Generate navigation section"""
        nav_links = []
        for i, screen in enumerate(screens):
            screen_name = screen.get('name', f'Screen {i+1}')
            nav_links.append(f'<a href="#screen-{i}" class="nav-link">{screen_name}</a>')
        
        return f"""
        <div class="navigation">
            <h2>Screen Navigation</h2>
            <div class="nav-links">
                {' '.join(nav_links)}
            </div>
        </div>"""
    
    def _generate_screen_section(self, screen: Dict[str, Any], index: int) -> str:
        """Generate individual screen section"""
        screen_name = screen.get('name', f'Screen {index+1}')
        description = screen.get('description', 'No description provided')
        html_content = screen.get('html_layout', screen.get('html_content', '<p>No content available</p>'))
        elements = screen.get('elements', [])
        
        # Generate elements list
        elements_html = ''
        if elements:
            element_tags = []
            for element in elements:
                if isinstance(element, dict):
                    element_name = element.get('content', element.get('type', 'Unknown'))
                else:
                    element_name = str(element)
                element_tags.append(f'<span class="element-tag">{element_name}</span>')
            
            elements_html = f"""
            <div class="screen-elements">
                <h4>UI Elements</h4>
                <div class="elements-list">
                    {' '.join(element_tags)}
                </div>
            </div>"""
        
        return f"""
        <div id="screen-{index}" class="screen-section">
            <div class="screen-header">
                <h3>{screen_name}</h3>
                <p class="screen-description">{description}</p>
            </div>
            <div class="screen-content">
                {html_content}
            </div>
            {elements_html}
        </div>"""
    
    def _generate_html_footer(self) -> str:
        """Generate HTML footer"""
        return """
        <div class="export-info">
            <p>This document was generated by TUX - AI-Powered UX Design Generator</p>
            <p>Visit <a href="https://tuxonline.live" style="color: #3b82f6;">tuxonline.live</a> to create your own UX designs</p>
        </div>
    </div>
</body>
</html>"""
    
    async def export_screens_json(
        self, 
        screens: List[Dict[str, Any]], 
        ux_specs: Optional[Dict[str, Any]] = None,
        requirements: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Export complete project data as JSON
        
        Args:
            screens: List of screen data
            ux_specs: UX specifications
            requirements: Original requirements
            
        Returns:
            JSON string
        """
        try:
            export_data = {
                "export_version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "tux_version": "1.0.0",
                "data": {
                    "requirements": requirements,
                    "ux_specifications": ux_specs,
                    "screens": screens
                }
            }
            
            return json.dumps(export_data, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to export JSON: {str(e)}")
            raise
    
    async def export_screen_svg(
        self, 
        screen: Dict[str, Any]
    ) -> str:
        """
        Export a single screen as SVG
        
        Args:
            screen: Screen data
            
        Returns:
            SVG content as string
        """
        try:
            screen_name = screen.get('name', 'Screen')
            description = screen.get('description', '')
            elements = screen.get('elements', [])
            
            # Build SVG
            svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
    <!-- Background -->
    <rect width="800" height="600" fill="#f8fafc"/>
    
    <!-- Header -->
    <rect x="0" y="0" width="800" height="80" fill="#3b82f6"/>
    <text x="400" y="45" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="white">
        {screen_name}
    </text>
    
    <!-- Description -->
    <text x="400" y="110" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#6b7280">
        {description[:60]}{'...' if len(description) > 60 else ''}
    </text>
    
    <!-- Content Area -->
    <rect x="40" y="140" width="720" height="400" fill="white" stroke="#e5e7eb" stroke-width="2" rx="8"/>
    
    <!-- Elements -->
    <g transform="translate(60, 160)">"""
            
            # Add elements as simple rectangles/text
            y_offset = 0
            for i, element in enumerate(elements[:8]):  # Limit to 8 elements
                element_text = str(element) if not isinstance(element, dict) else element.get('content', 'Element')
                svg_content += f"""
        <rect x="0" y="{y_offset}" width="200" height="40" fill="#e0e7ff" rx="4"/>
        <text x="100" y="{y_offset + 25}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#4338ca">
            {element_text[:20]}{'...' if len(element_text) > 20 else ''}
        </text>"""
                y_offset += 50
            
            svg_content += """
    </g>
    
    <!-- Footer -->
    <text x="400" y="570" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#9ca3af">
        Generated by TUX - AI-Powered UX Design
    </text>
</svg>"""
            
            return svg_content
            
        except Exception as e:
            logger.error(f"Failed to export SVG: {str(e)}")
            raise
    
    async def save_export(
        self, 
        content: str, 
        filename: str, 
        format: str
    ) -> str:
        """
        Save export to file
        
        Args:
            content: File content
            filename: Base filename
            format: File format (html, json, svg)
            
        Returns:
            File path
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            full_filename = f"{filename}_{timestamp}.{format}"
            file_path = self.exports_dir / full_filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Saved export to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to save export: {str(e)}")
            raise 