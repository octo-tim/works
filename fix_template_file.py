
def fix_file():
    path = "templates/work_templates.html"
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # 0-indexed: line 347 is index 346.
    # Check if content matches the corrupted pattern
    # 347: "name": {{ t.name | tojson } (missing comma, closing brace?)
    
    # Scan for the corrupted line
    target_idx = -1
    for i, line in enumerate(lines):
        if '"name": {{ t.name | tojson }' in line and '}},' not in line:
            print(f"Found corrupted line at {i+1}: {line.strip()}")
            target_idx = i
            break
            
    if target_idx == -1:
        print("Corrupted line not found. Maybe line 347 is correct?")
        # Check line 347 anyway
        if len(lines) > 346:
            print(f"Line 347 content: {lines[346].strip()}")
        return

    # We expect 4 corrupted lines:
    # "name": ...
    # },
    # "category": ...
    # "description": ...
    
    # We want to replace these with 3 correct lines.
    
    new_lines = [
        '            "name": {{ t.name | tojson }},\n',
        '            "category": {{ t.category | tojson }},\n',
        '            "description": {{ t.description | tojson }},\n'
    ]
    
    # Replace lines target_idx to target_idx + 4
    # i.e. remove 4 lines, insert 3 lines.
    
    final_lines = lines[:target_idx] + new_lines + lines[target_idx+4:]
    
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(final_lines)
    print("File patched successfully.")

if __name__ == "__main__":
    fix_file()
