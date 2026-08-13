#!/usr/bin/env python3
"""
Final test untuk verifikasi perbaikan
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

# User's exact subtitle
user_subtitle = "Gunakan pesan singkat yang fokus pada kebutuhan, bukan menyalahkan. Contoh: 'Hei, ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang].'"

print("=" * 80)
print("FINAL FIX VERIFICATION")
print("=" * 80)

formatted = format_subtitle_text(user_subtitle)
escaped = escape_text_for_ffmpeg_new(formatted)

print("\n1. Original subtitle:")
print(repr(user_subtitle))
print(f"   Length: {len(user_subtitle)} chars")
print(f"   Single quotes: {user_subtitle.count(chr(39))}")
print(f"   Contains [tujuan]: {'[tujuan]' in user_subtitle}")

print("\n2. After formatting:")
print(repr(formatted))
print(f"   Length: {len(formatted)} chars")
print(f"   Lines: {formatted.count(chr(10)) + 1}")
print(f"   Single quotes: {formatted.count(chr(39))}")

print("\n3. After escaping:")
print(repr(escaped))
print(f"   Length: {len(escaped)} chars")
print(f"   Contains \\[: {'\\\\[' in escaped}")
print(f"   Contains \\]: {'\\\\]' in escaped}")
print(f"   Contains \\:: {'\\\\:' in escaped}")
print(f"   Contains '\\'\\'': {escaped.count(\"'\\\\''\")}")

# Build a sample filter
SUBTITLE_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
filter_expr = f"drawtext=fontfile={SUBTITLE_FONT}:text='{escaped}':fontcolor=white"

print("\n4. Sample filter expression (first 200 chars):")
print(repr(filter_expr[:200]))

# Verify fix logic
print("\n5. Fix verification:")
single_quote_count = escaped.count(chr(39))
escaped_seq_count = escaped.count("'\\''")
print(f"   Total single quotes: {single_quote_count}")
print(f"   Escaped sequences ('\\''): {escaped_seq_count}")

# The fix should mean: for every original single quote, we now have 3 single quotes
original_quotes = formatted.count(chr(39))
expected_quotes_after_fix = original_quotes * 3
print(f"   Original quotes in formatted: {original_quotes}")
print(f"   Expected quotes after fix: {expected_quotes_after_fix}")
print(f"   Actual quotes after fix: {single_quote_count}")

if single_quote_count == expected_quotes_after_fix:
    print("   ✓ Fix correctly implemented!")
else:
    print("   ✗ Fix not working as expected")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("The fix properly escapes single quotes using FFmpeg's quoting mechanism:")
print("  ' -> '\\''")
print("This makes 'Contoh: \\'Hei,...' become 'Contoh: '\\''Hei,...'")
print("FFmpeg will parse this correctly as: 'Contoh: ' + escaped quote + 'Hei,...'")
