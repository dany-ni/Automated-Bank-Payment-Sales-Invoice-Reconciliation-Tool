
ZUORDNUNGSART_LABELS = {
    "MATCHED":       {"en": "matched",       "de": "übereinstimmend"},
    "UNMATCHED":     {"en": "unmatched",     "de": "nicht übereinstimmend"},
    "UNSUPPORTED": {"en": "unsupported", "de": "nicht unterstützt"},
}

GRUND_LABELS = {
    "EXACT_MATCH_1_1":      {"en": "exact matched 1:1",                 "de": "genaue Übereinstimmung 1:1"},
    "SKONTO_MATCH_1_1":     {"en": "skonto matched 1:1",                "de": "Skonto-Übereinstimmung 1:1"},
    "INVALID_SKONTO_1_1":   {"en": "invalid skonto 1:1",              "de": "ungültiges Skonto 1:1"},
    "WRONG_AMOUNT_1_1":     {"en": "wrong amount 1:1",                "de": "falscher Betrag 1:1"},
    "SPLIT_MATCH_N_1":      {"en": "split payment matched N:1",         "de": "Teilzahlung übereinstimmend N:1"},
    "SPLIT_UNMATCH_N_1":    {"en": "split payment unmatched N:1",       "de": "Teilzahlung nicht übereinstimmend N:1"},
    "COMBINED_MATCH_1_N":   {"en": "combined payment matched 1:N",      "de": "Sammelzahlung übereinstimmend 1:N"},
    "COMBINED_UNMATCH_1_N": {"en": "combined payment unmatched 1:N",    "de": "Sammelzahlung nicht übereinstimmend 1:N"},
    "UNSUPPORTED_NM":       {"en": "unsupported complex pattern N:M", "de": "nicht unterstütztes komplexes Muster N:M"},
}


def translate_zuordnungsart(code, language):
    return ZUORDNUNGSART_LABELS[code][language]


def translate_grund(code, language):
    return GRUND_LABELS[code][language]
