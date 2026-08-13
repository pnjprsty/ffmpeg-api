#!/usr/bin/env python3
"""
Verifikasi perbaikan single quote escaping
"""

def escape_text_for_ffmpeg_old(text: str) -> str:
    """Old version (with bug)"""
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("%", "\\%")
    return text

def escape_text_for_ffmpeg_new(text: str) -> str:
    """New version with single quote handling"""
    text = text.replace("\\", "\\\\")
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("%", "\\%")
    text = text.replace("'", "'\\''")
    return text

def format_subtitle_text(text: str) -> str:
    """Formatting function"""
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

# Test case dari user
user_subtitle = "Gunakan pesan singkat yang fokus pada kebutuhan, bukan menyalahkan. Contoh: 'Hei, ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang].'"

print("=" * 80)
print("VERIFYING FIX FOR SINGLE QUOTE ESCAPING")
print("=" * 80)

print(f"\nOriginal subtitle ({len(user_subtitle)} chars):")
print(repr(user_subtitle))

formatted = format_subtitle_text(user_subtitle)
print(f"\nAfter formatting ({len(formatted)} chars):")
print(repr(formatted))

escaped_old = escape_text_for_ffmpeg_old(formatted)
escaped_new = escape_text_for_ffmpeg_new(formatted)

print(f"\n" + "=" * 80)
print("OLD ESCAPING (BUGGY)")
print("=" * 80)
print(f"Escaped: {repr(escaped_old)}")
print(f"Contains single quotes: {'\'' in escaped_old}")
print(f"Contains escaped single quotes: {'\\\'' in escaped_old}")

print(f"\n" + "=" * 80)
print("NEW ESCAPING (FIXED)")
print("=" * 80)
print(f"Escaped: {repr(escaped_new)}")
print(f"Contains single quotes: {'\'' in escaped_new}")
print(f"Contains escaped single quotes pattern: {'\\\'' in escaped_new}")

# Build the filter expression
SUBTITLE_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
filter_old = f"drawtext=fontfile={SUBTITLE_FONT}:text='{escaped_old}':fontcolor=white"
filter_new = f"drawtext=fontfile={SUBTITLE_FONT}:text='{escaped_new}':fontcolor=white"

print(f"\n" + "=" * 80)
print("FILTER EXPRESSIONS")
print("=" * 80)
print(f"\nOLD (first 150 chars):")
print(repr(filter_old[:150]))

print(f"\nNEW (first 150 chars):")
print(repr(filter_new[:150]))

# Check specific problem areas
print(f"\n" + "=" * 80)
print("PROBLEM AREA ANALYSIS")
print("=" * 80)

# Check the problematic substring from error
problem_substring = "ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang]"
print(f"Problem substring in escaped_old: {problem_substring in escaped_old}")
print(f"Problem substring in escaped_new: {problem_substring in escaped_new}")

# Check for single quote issues
print(f"\nSingle quote count in original: {user_subtitle.count('\'')}")
print(f"Single quote count in formatted: {formatted.count('\'')}")
print(f"Single quote count in escaped_old: {escaped_old.count('\'')}")
print(f"Single quote count in escaped_new: {escaped_new.count('\'')}")

print(f"\n" + "=" * 80)
print("WHAT THE FIX DOES")
print("=" * 80)
print("Old escaping: single quotes remain unescaped -> FFmpeg parsing fails")
print("New escaping: ' becomes '\\'' -> Proper FFmpeg quote escaping")
print("Example: text='Example\\'s quote' -> becomes text='Example'\\''s quote'")
print("In FFmpeg: 'text' + escaped quote + 'continuation'")
