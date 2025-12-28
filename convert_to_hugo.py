"""
Convert existing markdown news files to Hugo format
"""
import os
import re
import shutil
from pathlib import Path
from datetime import datetime


def extract_metadata_from_content(content):
    """Extract metadata from markdown content"""
    # Extract title (first h1)
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else "IT News Digest"

    # Extract date from title or filename
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', title)
    date = date_match.group(1) if date_match else datetime.now().strftime('%Y-%m-%d')

    # Extract categories based on section headers
    categories = []
    tags = []

    if '🧠 인공지능' in content or 'AI' in content or '인공지능' in content:
        categories.append('AI')
        tags.append('인공지능')

    if '💻 개발 뉴스' in content or 'Dev.to' in content:
        categories.append('개발')
        tags.append('개발뉴스')

    if '🤖 로보틱스' in content or '로봇' in content:
        categories.append('로보틱스')
        tags.append('로봇')

    # Default category if none found
    if not categories:
        categories = ['IT News']

    # Add date-based tag
    tags.append(date)

    return {
        'title': title,
        'date': date,
        'categories': categories,
        'tags': tags
    }


def create_hugo_frontmatter(metadata):
    """Create Hugo front matter from metadata"""
    frontmatter = "---\n"
    frontmatter += f"title: \"{metadata['title']}\"\n"
    frontmatter += f"date: {metadata['date']}\n"
    frontmatter += f"draft: false\n"

    # Categories
    if metadata['categories']:
        frontmatter += "categories:\n"
        for cat in metadata['categories']:
            frontmatter += f"  - \"{cat}\"\n"

    # Tags
    if metadata['tags']:
        frontmatter += "tags:\n"
        for tag in metadata['tags']:
            frontmatter += f"  - \"{tag}\"\n"

    frontmatter += "---\n\n"
    return frontmatter


def convert_markdown_file(input_file, output_dir):
    """Convert a single markdown file to Hugo format"""
    # Read original content
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract metadata
    metadata = extract_metadata_from_content(content)

    # Create front matter
    frontmatter = create_hugo_frontmatter(metadata)

    # Combine front matter with content
    hugo_content = frontmatter + content

    # Create output filename based on date
    output_filename = f"{metadata['date']}-news.md"
    output_path = output_dir / output_filename

    # Write Hugo-formatted file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(hugo_content)

    print(f"[OK] Converted: {input_file.name} -> {output_filename}")
    return output_path


def main():
    """Main conversion function"""
    # Paths
    project_root = Path(__file__).parent
    markdown_input_dir = project_root / 'output' / 'markdown'
    hugo_content_dir = project_root / 'blog' / 'content' / 'posts'

    # Create output directory if it doesn't exist
    hugo_content_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Converting Markdown Files to Hugo Format")
    print("=" * 60)
    print(f"Input:  {markdown_input_dir}")
    print(f"Output: {hugo_content_dir}")
    print()

    # Check if input directory exists
    if not markdown_input_dir.exists():
        print(f"Error: Input directory not found: {markdown_input_dir}")
        return

    # Get all markdown files
    markdown_files = list(markdown_input_dir.glob('*.md'))

    if not markdown_files:
        print(f"No markdown files found in {markdown_input_dir}")
        return

    print(f"Found {len(markdown_files)} markdown file(s)")
    print()

    # Convert each file
    converted_count = 0
    for md_file in markdown_files:
        try:
            convert_markdown_file(md_file, hugo_content_dir)
            converted_count += 1
        except Exception as e:
            print(f"[ERROR] Error converting {md_file.name}: {e}")

    print()
    print("=" * 60)
    print(f"Conversion Complete: {converted_count}/{len(markdown_files)} files")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review the converted files in blog/content/posts/")
    print("2. Run 'cd blog && ../tools/hugo.exe server' to preview")
    print("3. Build with 'cd blog && ../tools/hugo.exe'")


if __name__ == "__main__":
    main()
