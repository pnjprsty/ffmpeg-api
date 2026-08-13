#!/usr/bin/env python3
"""Test script to verify subtitle wrapping logic"""

def format_subtitle_text(text: str) -> str:
    """
    Format subtitle text with:
    1. Maximum 3 words per line
    2. Maximum 20 characters per line (including spaces)
    3. If 3 words exceed 20 chars, use max 2 words
    4. Each line centered horizontally based on its width
    5. Line breaks before rendering
    """
    # Clean up extra whitespace
    words = text.strip().split()
    
    # Group words into lines following rules
    lines = []
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        
        # Check both constraints:
        # 1. Less than 3 words (or exactly 3)
        # 2. Total characters <= 20
        if len(current_line) < 3 and len(test_line) <= 20:
            current_line.append(word)
        else:
            # Can't add this word to current line
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    
    # Add the last line if it has words
    if current_line:
        lines.append(" ".join(current_line))
    
    return "\n".join(lines)


# Test cases
test_cases = [
    "Teman sering minta pinjam uang tapi lupa bayar",
    "Ini adalah test singkat",
    "Kata demi kata dipisah dengan rapi di setiap baris",
    "A B C D E F G H I J",
]

print("=" * 60)
print("SUBTITLE WRAPPING TEST")
print("=" * 60)

for i, text in enumerate(test_cases, 1):
    result = format_subtitle_text(text)
    lines = result.split("\n")
    
    print(f"\nTest Case {i}:")
    print(f"Input: {text}")
    print(f"Output ({len(lines)} lines):")
    
    for j, line in enumerate(lines, 1):
        word_count = len(line.split())
        char_count = len(line)
        print(f"  Line {j}: '{line}'")
        print(f"    - Words: {word_count}, Characters: {char_count}")
        
        # Validation
        if word_count > 3:
            print(f"    ❌ ERROR: More than 3 words ({word_count})")
        if char_count > 20:
            print(f"    ❌ ERROR: More than 20 characters ({char_count})")
        if word_count <= 3 and char_count <= 20:
            print(f"    ✓ OK")

print("\n" + "=" * 60)
print("CENTER ALIGNMENT SIMULATION")
print("=" * 60)

# Simulate center alignment
example = "Teman sering minta pinjam uang tapi lupa bayar"
result = format_subtitle_text(example)
lines = result.split("\n")

video_width = 1080

print(f"\nExample: {example}")
print(f"Video width: {video_width}px")
print(f"\nFormatted subtitle with center alignment:")
print()

for line in lines:
    text_width = len(line) * 8  # Approximate: ~8px per character at fontsize 60
    x_pos = (video_width - text_width) // 2
    print(f"{line.center(60)}")
    print(f"Text width: ~{text_width}px, X position: {x_pos}px")
    print()

print("=" * 60)
