import argparse
import requests
import os
import datetime

def is_url_working(url, timeout=10):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code >= 400:
            return response.status_code
    except requests.exceptions.RequestException as e:
        return str(e)
    return None

def line_to_dict(line):
    try:
        parts = line.strip().split('|')
        name, link = parts[1].strip().split('](')
        name = name[1:]
        link = link[:-1]
        return name, {
            'link': link,
            'description': parts[2].strip(),
            'auth': parts[3].strip(),
            'https': parts[4].strip(),
            'cors': parts[5].strip()
        }
    except Exception:
        return None, None

def parse_sections(lines):
    index = 0
    sections = {}
    while index < len(lines):
        line = lines[index]
        if line.startswith('###'):
            section_name = line[3:].strip()
            index += 3
            section_data = {}
            while index < len(lines) and 'Back to Index' not in lines[index]:
                name, row = line_to_dict(lines[index])
                if name and row:
                    section_data[name] = row
                index += 1
            sections[section_name] = section_data
        index += 1
    return sections

def collect_broken_links(sections):
    broken = []
    for section, items in sections.items():
        for title, row in items.items():
            result = is_url_working(row['link'])
            if result:
                broken.append({
                    'section': section,
                    'title': title,
                    'link': row['link'],
                    'error': result
                })
    return broken

def save_report(broken_links, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('# Manual Check Required\n\n')
        f.write('| Section | API | Error |\n')
        f.write('|---------|-----|-------|\n')
        for item in broken_links:
            f.write(f"| {item['section']} | [{item['title']}]({item['link']}) | {item['error']} |\n")
    print(f"✅ Saved {len(broken_links)} broken links to `{output_path}`")

def get_default_readme():
    candidate = os.path.join(os.path.dirname(os.getcwd()), 'README.md')
    if os.path.exists(candidate):
        return candidate
    print("❗ README.md not found. Use --file to specify path.")
    return None

def get_timestamped_filename(base="error_report"):
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    return f"{base}_{date_str}.txt"

def main():
    parser = argparse.ArgumentParser(description="Broken Link Checker for Public API README")
    parser.add_argument('--file', help='Path to README.md file')
    parser.add_argument('--output', help='Path to save error report')
    args = parser.parse_args()

    readme_path = args.file if args.file else get_default_readme()
    if not readme_path:
        return

    output_path = args.output if args.output else get_timestamped_filename()

    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        sections = parse_sections(lines)
        broken_links = collect_broken_links(sections)

        if broken_links:
            save_report(broken_links, output_path)
        else:
            print("✅ All links look good. No issues found.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main()
