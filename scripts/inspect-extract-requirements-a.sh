uv run python -c "
from src.poc.extract_requirements import extract_requirements_from_markdown

job_md = '''# Carbon Robotics

## Requirements
- Must have 5+ years of Python experience
- Essential knowledge of Django
- Experience with PostgreSQL
'''

output = extract_requirements_from_markdown(job_md)
print(f'Company: {output.company}')
print(f'Requirements: {output.requirements_count}')
for req in output.requirements[:3]:
    print(f'  - {req.text} (confidence: {req.confidence})')
" 2>&1
