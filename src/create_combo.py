


def normalize_combo(text):

    if not isinstance(text, str):
        return text

    text = text.lower()

    # -----------------------------------------
    # normalize separators/spaces
    # -----------------------------------------
    text = re.sub(r'\s*/\s*', '/', text)
    text = re.sub(r'\s*-\s*', '-', text)
    text = re.sub(r'\s+', ' ', text).strip()

    # ==========================================================
    # CASE 1
    # levodopa carbidopa 100/25mg
    # levodopa/carbidopa 100/25
    #
    # -> carbidopa/levodopa 25/100
    # ==========================================================
    pattern_reverse_pair = re.compile(
        r'''
        levodopa
        \s*
        (?:/|\s+)
        \s*
        carbidopa
        \s+
        (\d+\.?\d*)
        \s*[/\-]\s*
        (\d+\.?\d*)
        \s*(?:mg)?
        ''',
        flags=re.I | re.X
    )
    
    def reverse_pair_repl(m):

        levo = m.group(1)
        carb = m.group(2)

        return f"carbidopa/levodopa {carb}/{levo}"

    text = pattern_reverse_pair.sub(reverse_pair_repl, text)

    # ==========================================================
    # CASE 2
    # carbidopa/levodopa/entacapone 25/100/200
    #
    # -> carbidopa/entacapone/levodopa 25/200/100
    # ==========================================================
    pattern_triple = re.compile(
        r'''
        carbidopa
        \s*[/\-]\s*
        levodopa
        \s*[/\-]\s*
        entacapone
        \s+
        (\d+\.?\d*)
        \s*[/\-]\s*
        (\d+\.?\d*)
        \s*[/\-]\s*
        (\d+\.?\d*)
        \s*(?:mg)?
        ''',
        flags=re.I | re.X
    )

    def reorder_triple(m):

        carb = m.group(1)
        levo = m.group(2)
        enta = m.group(3)

        return (
            f"carbidopa/entacapone/levodopa "
            f"{carb}/{enta}/{levo}"
        )

    text = pattern_triple.sub(reorder_triple, text)

    # ==========================================================
    # CASE 3
    # levodopa/carbidopa/entacapone 100/25/200
    # levodopa carbidopa entacapone 100/25/200
    #
    # -> carbidopa/entacapone/levodopa 25/200/100
    # ==========================================================
    pattern_reverse_triple = re.compile(
        r'''
        levodopa
        \s*
        (?:/|\s+)
        \s*
        carbidopa
        \s*
        (?:/|\s+)
        \s*
        entacapone
        \s+
        (\d+\.?\d*)
        \s*[/\-]\s*
        (\d+\.?\d*)
        \s*[/\-]\s*
        (\d+\.?\d*)
        \s*(?:mg)?
        ''',
        flags=re.I | re.X
    )

    def reverse_triple_repl(m):

        levo = m.group(1)
        carb = m.group(2)
        enta = m.group(3)

        return (
            f"carbidopa/entacapone/levodopa "
            f"{carb}/{enta}/{levo}"
        )

    text = pattern_reverse_triple.sub(reverse_triple_repl, text)

    return text


df[output_col] = df[output_col].apply(normalize_combo)