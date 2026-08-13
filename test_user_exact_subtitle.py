#!/usr/bin/env python3
"""Test dengan subtitle EXACT dari user"""

def format_subtitle_text(text: str) -> str:
    words = text.strip().split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        if len(current_line) < 3 and len(test_line) <= 20:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    return "\n".join(lines)

# Exact subtitle dari user
user_subtitle = "Gunakan pesan singkat yang fokus pada kebutuhan, bukan menyalahkan. Contoh: 'Hei, ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang].'"

print("=" * 80)
print("USER'S EXACT SUBTITLE")
print("=" * 80)
print(f"Original ({len(user_subtitle)} chars):")
print(repr(user_subtitle))

print("\n" + "=" * 80)
print("AFTER FORMATTING")
print("=" * 80)
formatted = format_subtitle_text(user_subtitle)
print(f"Formatted ({len(formatted)} chars):")
print(repr(formatted))

print("\n" + "=" * 80)
print("LINE BY LINE")
print("=" * 80)
for i, line in enumerate(formatted.split('\n'), 1):
    print(f"Line {i}: {repr(line)} ({len(line)} chars)")

print("\n" + "=" * 80)
print("PROBLEM ANALYSIS")
print("=" * 80)

# Check if the substring from error message is in formatted text
error_substring = "ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang]"
print(f"Is error substring in formatted text?")
print(f"  Full text: {error_substring in formatted}")
print(f"  Without formatting: {error_substring in user_subtitle}")

# Count newlines
print(f"\nNewlines in formatted: {formatted.count(chr(10))}")
print(f"Newlines in original: {user_subtitle.count(chr(10))}")

# Check word count
print(f"\nWord count: {len(user_subtitle.split())}")
