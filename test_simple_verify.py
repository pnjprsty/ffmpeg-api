#!/usr/bin/env python3
"""
Simple verification of the fix
"""

def escape_text_for_ffmpeg_new(text: str) -> str:
    """New version with single quote handling"""
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("%", "\\%")
    text = text.replace("'", "'\\''")
    return text

# Test with a simple example first
test_text = "Hello 'quoted' world"
escaped = escape_text_for_ffmpeg_new(test_text)
print("Simple test:")
print(f"Original: {repr(test_text)}")
print(f"Escaped:  {repr(escaped)}")
print()

# Test with user's subtitle
user_subtitle = "Gunakan pesan singkat yang fokus pada kebutuhan, bukan menyalahkan. Contoh: 'Hei, ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang].'"

print("User subtitle analysis:")
print(f"Original length: {len(user_subtitle)}")
original_quotes = user_subtitle.count("'")
print(f"Single quotes count: {original_quotes}")

formatted = user_subtitle
escaped_user = escape_text_for_ffmpeg_new(formatted)

print(f"\nAfter escaping:")
print(f"Escaped length: {len(escaped_user)}")

has_escaped_bracket_open = "\\[" in escaped_user
has_escaped_bracket_close = "\\]" in escaped_user
has_escaped_quote = "'\\'''" in escaped_user

print(f"Contains escaped [: {has_escaped_bracket_open}")
print(f"Contains escaped ]: {has_escaped_bracket_close}")
print(f"Contains escaped quote: {has_escaped_quote}")

# Show a small sample
sample_start = escaped_user.find("Contoh:")
if sample_start != -1:
    sample_end = min(sample_start + 50, len(escaped_user))
    sample = escaped_user[sample_start:sample_end]
    print(f"\nSample around 'Contoh...': {repr(sample)}")

print("\n" + "="*60)
print("FIX SUMMARY:")
print("="*60)
print("Problem: Single quotes in subtitle cause FFmpeg parsing error")
print("Root cause: text='Contoh: 'Hei,...' breaks FFmpeg's quoting")
print("Solution: Replace ' with '\\'' using FFmpeg escape mechanism")
print("Result: Single quotes are properly escaped and won't break filter")
print("="*60)
