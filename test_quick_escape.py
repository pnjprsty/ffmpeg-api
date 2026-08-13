#!/usr/bin/env python3
"""Quick test escaping function"""

def escape_text_for_ffmpeg(text: str) -> str:
    text = text.replace("\\", "\\\\")
    text = text.replace('"', '\\"')
    text = text.replace(":", "\\:")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    text = text.replace("%", "\\%")
    return text

# Test with user's subtitle
subtitle = "Hei, ingat waktu itu aku pinjemin uang untuk [tujuan]? Aku butuh untuk [kebutuhanmu sekarang]."

print(f"Original: {repr(subtitle)}")
escaped = escape_text_for_ffmpeg(subtitle)
print(f"Escaped:  {repr(escaped)}")

# Check specific characters
contains_bracket_open = '[' in escaped
contains_escaped_bracket_open = '\\[' in escaped
contains_bracket_close = ']' in escaped
contains_escaped_bracket_close = '\\]' in escaped
contains_colon = ':' in escaped
contains_escaped_colon = '\\:' in escaped
contains_question = '?' in escaped

print(f"\nContains '[': {contains_bracket_open}")
print(f"Contains '\\\\[': {contains_escaped_bracket_open}")
print(f"Contains ']': {contains_bracket_close}")
print(f"Contains '\\\\]': {contains_escaped_bracket_close}")
print(f"Contains ':': {contains_colon}")
print(f"Contains '\\\\:': {contains_escaped_colon}")
print(f"Contains '?': {contains_question}")

# Test formatting function too
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

formatted = format_subtitle_text(subtitle)
print(f"\nFormatted: {repr(formatted)}")

# Escape formatted text
escaped_formatted = escape_text_for_ffmpeg(formatted)
print(f"Escaped formatted: {repr(escaped_formatted)}")

# Check what happens with the specific part from error
error_part = "[kebutuhanmu sekarang].:fontcolor"
print(f"\nError part: {repr(error_part)}")
escaped_error_part = escape_text_for_ffmpeg(error_part)
print(f"Escaped error part: {repr(escaped_error_part)}")
