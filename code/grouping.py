from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple


@dataclass
class Group:
    transaction_ids: List[int]
    invoice_numbers: List[str]
    shape_label: str  # "1:1" / "N:1" / "1:N" / "N:M"


def build_groups(valid_invoice_incoming_bank_statement_df):
    
    # key = sorted extracted invoice number tuple, value = transaction_id list
    # e.g., ("RE002"):[1],  ("RE002", "RE003"):[2],  ("RE010"):[1, 2],  ("RE011", "RE012"):[3]
    tx_by_invoice_combo: Dict[Tuple[str, ...], List[int]] = defaultdict(list)

    for tx_id, row in valid_invoice_incoming_bank_statement_df.iterrows():
        extracted_list = row["extrahierte_rechnungsnummer"]
        combo_key = tuple(sorted(set(extracted_list)))
        tx_by_invoice_combo[combo_key].append(tx_id)


    # key = 1 invoice number, value = sorted extracted invoice number tuple set
    # e.g., "RE002": {("RE002"), ("RE002", "RE003")},  "RE010": {("RE010")},  "RE011": {("RE011", "RE012")}, "RE012": {("RE011", "RE012")}
    invoice_to_combos: Dict[str, Set[Tuple[str, ...]]] = defaultdict(set)
    for combo_key in tx_by_invoice_combo:
        for invoice_no in combo_key:
            invoice_to_combos[invoice_no].add(combo_key)    


    # Check if any invoice number appears in two different tuples of extracted invoices
    # "RE002": {("RE002"), ("RE002", "RE003")},  "RE004": { ("RE004", "RE005"), ("RE004", "RE006") }
    # -> conflicted_combos {("RE002"), ("RE002", "RE003"), ("RE004", "RE005"), ("RE004", "RE006")}
    conflicted_combos: Set[Tuple[str, ...]] = set()
    for invoice_no, combos in invoice_to_combos.items():
        if len(combos) > 1:
            conflicted_combos.update(combos)


    groups = []

    for combo_key, tx_ids in tx_by_invoice_combo.items():
        if combo_key in conflicted_combos:
            shape_label = "N:M"  
        else:
            n_tx, n_inv = len(tx_ids), len(combo_key)
            if n_tx == 1 and n_inv == 1:
                shape_label = "1:1"
            elif n_tx > 1 and n_inv == 1:
                shape_label = "N:1"
            elif n_tx == 1 and n_inv > 1:
                shape_label = "1:N"
            else:
                shape_label = "N:M"

        groups.append(
            Group(
                transaction_ids=sorted(tx_ids),
                invoice_numbers=sorted(combo_key),
                shape_label=shape_label,
            )
        )

    return groups
