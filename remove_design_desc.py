
import sys

input_file = "working/ppt-20260112-123607/session.yaml"
output_file = "working/ppt-20260112-123607/session-gemini.yaml"

with open(input_file, 'r') as f:
    lines = f.readlines()

output_lines = []
in_remove_block = False
remove_indent = 0

for line in lines:
    stripped = line.lstrip()
    # Skip empty lines if we are just moving through the file, 
    # but strictly check indentation if we are inside a block we want to remove.
    # Actually, empty lines inside a text block are part of it.
    # Empty lines between keys are safer to keep, but if we are "inside" a removal, we drop them.
    
    if not stripped:
        if in_remove_block:
            continue
        else:
            output_lines.append(line)
            continue

    indent = len(line) - len(stripped)
    
    if stripped.startswith("design_description:"):
        in_remove_block = True
        remove_indent = indent
        continue
        
    if in_remove_block:
        # If we see a line with same or smaller indentation, the block is over
        if indent <= remove_indent:
            in_remove_block = False
        else:
            # We are inside the indented block of design_description
            continue
            
    output_lines.append(line)

with open(output_file, 'w') as f:
    f.writelines(output_lines)

print(f"Processed {len(lines)} lines. Output to {output_file}")
