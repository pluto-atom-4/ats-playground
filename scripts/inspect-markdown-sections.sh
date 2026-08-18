#!/bin/bash
# Inspect MarkdownSpanRuler behavior (Issue #284 POC)

set -e

uv run python -c "
import json
import sys
from pathlib import Path

from src.poc.tweak.multi_line_paragraph import MarkdownSpanRuler, MarkdownSection
import spacy

print('✓ Imports successful')

# Load spaCy model
try:
    nlp = spacy.load('en_core_web_md')
    print('✓ Loaded spaCy model: en_core_web_md')
except OSError:
    print('⚠ en_core_web_md not found, trying en_core_web_sm...')
    nlp = spacy.load('en_core_web_sm')
    print('✓ Loaded spaCy model: en_core_web_sm')

# Initialize ruler
ruler = MarkdownSpanRuler(nlp)
print('✓ Initialized MarkdownSpanRuler')

# Test markdown

test_markdown = '''# Senior Python Developer

Exciting opportunity to join our team.

## Responsibilities

* Design and implement scalable systems
* Lead code reviews
* Mentor junior developers

## Requirements

* 5+ years of Python experience
* Strong understanding of REST APIs
* Experience with Docker and Kubernetes

###

Base Pay Range for:

WA applicants is $99,201.00 - $138,880.35

**Background Check**

* Required for all positions: Blue’s Standard Background Check
* Required for Certain Job Profiles: Defense Biometric Identification System (DBIDS) background check if at any time the role requires one to be on a military installation

**Benefits**

* Benefits include: Medical, dental, vision, basic and supplemental life insurance, paid parental leave, short and long-term disability, 401(k) with a company match of up to 5%, and an Education Support Program.
* Stock Options for all regular employees (working at least 20 hours/week)


**Equal Employment Opportunity**

Purple Town is proud to be an Equal Opportunity/Affirmative Action Employer and is committed to attracting, retaining, and developing a highly qualified and dedicated work force. Purple Town hires and promotes people on the basis of their qualifications, performance, and abilities. We support the establishment and maintenance of a workplace that fosters trust, equality, and teamwork.

**Affirmative Action and Disability Accommodation**

Applicants wishing to receive information on Purple Town’s Affirmative Action Plans, or applicants requiring a reasonable accommodation in order to participate in the application and/or interview process, please contact us at EEOCompliance@purpletown.com. Please note this is a publicly managed inbox. Please do not include any personal medical information in your request.'''

print()
print('=' * 70)
print('PARSING TEST MARKDOWN')
print('=' * 70)

sections = ruler.parse(test_markdown)
print(f'✓ Parsed {len(sections)} sections')
print()

# Display sections
for i, section in enumerate(sections, 1):
    level_name = f'H{section.level}' if section.level > 0 else 'BOLD'
    title = section.title or '(no title)'
    print(f'{i}. [{level_name}] {title}')
    print(f'   Lines {section.start_line}-{section.end_line} | {section.line_count} lines | {section.word_count} words | has_list={section.has_list}')
    print()

# Export to JSON
print('=' * 70)
print('JSON EXPORT')
print('=' * 70)
output_dict = ruler.to_dict(sections)
print(json.dumps(output_dict, indent=2))

# Summary stats
print()
print('=' * 70)
print('SUMMARY')
print('=' * 70)
total_sections = len(sections)
total_words = sum(s.word_count for s in sections)
total_lines = sum(s.line_count for s in sections)
sections_with_lists = sum(1 for s in sections if s.has_list)

print(f'Total sections: {total_sections}')
print(f'Total words: {total_words}')
print(f'Total lines: {total_lines}')
print(f'Sections with lists: {sections_with_lists}')
print()
print('✓ MarkdownSpanRuler inspection complete')
"
