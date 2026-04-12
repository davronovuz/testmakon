"""
Kimyo Milliy Sertifikat docx → JSON parser.
TURQUOISE / BRIGHT_GREEN highlight = to'g'ri javob.
Faqat choice (A/B/C/D) savollar parse qilinadi.
"""
import re
import json
from docx import Document
from docx.enum.text import WD_COLOR_INDEX

HIGHLIGHT_COLORS = {WD_COLOR_INDEX.TURQUOISE, WD_COLOR_INDEX.BRIGHT_GREEN}


def is_highlighted(run):
    return run.font.highlight_color in HIGHLIGHT_COLORS


def parse_docx(filepath):
    doc = Document(filepath)
    paras = doc.paragraphs

    # Find real variant boundaries:
    # Must start with "N. [ball]" or "N. Question text" with A/B/C/D options
    # AND have at least 20 choice questions with highlighted correct answers
    variant_starts = find_variant_starts(paras)
    print(f"Found {len(variant_starts)} variants")

    all_mocks = []
    for idx, vs in enumerate(variant_starts):
        end = variant_starts[idx + 1] if idx + 1 < len(variant_starts) else len(paras)
        questions = parse_choice_questions(paras, vs, end)
        if len(questions) < 10:
            continue

        variant_num = idx + 1
        is_free = variant_num <= 2

        mock = {
            'subject_slug': 'kimyo',
            'mock_slug': f'kimyo-2026-{variant_num}-variant',
            'mock_title': f'Kimyo 2026 — {variant_num}-variant',
            'year': 2026,
            'version': f'{variant_num}-variant',
            'time_limit': 150,
            'is_free': is_free,
            'questions': questions,
        }
        all_mocks.append(mock)
        correct_count = sum(1 for q in questions if any(c['is_correct'] for c in q.get('choices', [])))
        print(f"  Variant {variant_num}: {len(questions)} savol, {correct_count} correct, free={is_free}")

    return all_mocks


def find_variant_starts(paras):
    """Find paragraph indices where a new variant (mock test) starts."""
    candidates = []

    for i, para in enumerate(paras):
        text = para.text.strip()
        # Match "1. [X ball]" or "1. [X,X ball]"
        if re.match(r'^1\.\s*[\[\(]\s*[\d,\.]+\s*ball', text, re.I):
            candidates.append(i)
            continue
        # Match "1. Question text" (no ball marker but has A/B/C/D)
        if re.match(r'^1\.\s+[A-ZА-ЯTQ]', text):
            # Skip sub-items like "1. BaCl2 + ...", "1. X,Y,Z...", "1. A va B..."
            if re.match(r'^1\.\s*(BaCl|X[\s,]|A\s+(va|modda)|Sxema|Dastlabki|Jarayon|Ushbu|Toʻyingan|Glyukoza)', text):
                continue
            candidates.append(i)

    # Filter: only keep candidates that have enough highlighted choice questions
    real_starts = []
    for ci, c in enumerate(candidates):
        end = candidates[ci + 1] if ci + 1 < len(candidates) else len(paras)
        # Count highlighted answers in this range
        hl_count = 0
        for j in range(c, min(end, c + 500)):
            for run in paras[j].runs:
                if is_highlighted(run):
                    m = re.match(r'^[A-D]\)', run.text.strip())
                    if m:
                        hl_count += 1
                        break
        if hl_count >= 15:
            real_starts.append(c)

    return real_starts


def parse_choice_questions(paras, start, end):
    """Parse all choice questions from a variant range."""
    questions = []
    i = start

    while i < end:
        text = paras[i].text.strip()
        if not text:
            i += 1
            continue

        # Match question: "N. [X ball] text" or "N. text"
        m = re.match(r'^(\d+)\.\s*(?:[\[\(]\s*([\d,\.]+)\s*ball\s*[\]\)]\s*)?(.+)', text)
        if not m:
            i += 1
            continue

        num = int(m.group(1))
        if num > 32 or num < 1:
            i += 1
            continue

        # Check if we already have this question number
        if any(q['number'] == num for q in questions):
            i += 1
            continue

        points_str = m.group(2)
        if points_str:
            try:
                points = float(points_str.replace(',', '.'))
            except ValueError:
                points = 1.3
        else:
            points = 1.3 if num <= 10 else 2.2

        q_text_part = m.group(3).strip()

        # Extract question text and choices from this + following paragraphs
        q, next_i = extract_question(paras, i, end, num, q_text_part, points)
        if q and q.get('choices') and len(q['choices']) >= 2:
            questions.append(q)
        i = next_i if next_i > i else i + 1

    questions.sort(key=lambda x: x['number'])
    return questions


def extract_question(paras, start_idx, end, num, initial_text, points):
    """Extract a single choice question with options."""
    q_text = initial_text
    choices = []
    correct_label = None

    # Check current paragraph for inline options and highlights
    opts = extract_all_options(paras[start_idx])
    if opts['choices']:
        choices = opts['choices']
        correct_label = opts['correct']
        # Remove options from question text
        q_text = re.split(r'\s*[A-D]\)', q_text)[0].strip()

    i = start_idx + 1

    while i < end and i < start_idx + 8:
        text = paras[i].text.strip()
        if not text:
            i += 1
            continue

        # Stop if next question starts
        if re.match(r'^\d+\.\s', text):
            nm = re.match(r'^(\d+)\.', text)
            if nm and int(nm.group(1)) != num:
                break

        # Stop at grouped section
        if re.match(r'^33[\s\-–]+35', text):
            break

        # Check for options
        opts = extract_all_options(paras[i])
        if opts['choices']:
            for c in opts['choices']:
                existing = {ch['label'] for ch in choices}
                if c['label'] not in existing:
                    choices.append(c)
            if opts['correct'] and not correct_label:
                correct_label = opts['correct']
        elif not choices:
            # Part of question text
            q_text += '\n' + text

        i += 1

    if not choices or len(choices) < 2:
        return None, i

    # Mark correct
    for c in choices:
        c['is_correct'] = (c['label'] == correct_label)

    return {
        'number': num,
        'type': 'choice',
        'text': q_text.strip(),
        'points': points,
        'choices': choices,
    }, i


def extract_all_options(para):
    """Extract A/B/C/D options from paragraph text + find highlighted correct answer."""
    text = para.text

    # Find all option patterns: "A) text", "B) text", etc.
    # Handle both single-line and multi-option paragraphs
    pattern = r'([A-D])\)\s*'
    splits = re.split(pattern, text)

    choices = []
    if len(splits) >= 3:
        # splits: [before_A, 'A', text_A, 'B', text_B, ...]
        for j in range(1, len(splits) - 1, 2):
            label = splits[j]
            opt_text = splits[j + 1].strip()
            # Clean trailing whitespace and newlines
            opt_text = re.sub(r'\s+$', '', opt_text)
            if opt_text:
                choices.append({
                    'label': label,
                    'text': opt_text,
                    'order': ord(label) - ord('A') + 1,
                })

    # Find correct answer via highlight
    correct = None
    for run in para.runs:
        if is_highlighted(run):
            m = re.match(r'^([A-D])\)', run.text.strip())
            if m:
                correct = m.group(1)
                break

    return {'choices': choices, 'correct': correct}


if __name__ == '__main__':
    filepath = '/Users/macbookpro/Desktop/1. Milliy sertifikat [2026].docx'
    mocks = parse_docx(filepath)

    print(f"\n{'='*50}")
    print(f"Jami {len(mocks)} variant")
    total_q = sum(len(m['questions']) for m in mocks)
    total_correct = sum(
        sum(1 for q in m['questions'] if any(c['is_correct'] for c in q.get('choices', [])))
        for m in mocks
    )
    print(f"Jami {total_q} savol, {total_correct} to'g'ri javob belgilangan")
    print(f"Bepul: {sum(1 for m in mocks if m['is_free'])}, Pullik: {sum(1 for m in mocks if not m['is_free'])}")

    # Save
    outpath = '/Users/macbookpro/Documents/testmakon/kimyo_cert_questions.json'
    with open(outpath, 'w', encoding='utf-8') as f:
        json.dump(mocks, f, ensure_ascii=False, indent=2)
    print(f"\nJSON saqlandi: {outpath}")
