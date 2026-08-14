from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal, ROUND_HALF_UP

import numpy as np
import pandas as pd
import config

# Calculate skonto amount
def _skonto_amount(invoice_row):
    skonto = Decimal(invoice_row["skonto_prozent"]) * Decimal(invoice_row["rechnungsbetrag"]) / Decimal(100)
    return skonto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Verify if skonto is valid, by comparing Wertstellungsdatum and Skontodatum
def _skonto_is_valid(invoice_row, wertstellung):
    skonto_date = invoice_row["skonto_datum"]
    # If skonto_date, or skonto_prozent is 0 or null or missing, then False
    if pd.isna(skonto_date) or pd.isna(invoice_row["skonto_prozent"]) or invoice_row["skonto_prozent"] == 0:
        return False
    # if Wertstellungsdatum is earlier than or equal to Skontodatum, then True. Otherwise, False
    return wertstellung <= skonto_date


# For skonto, check if amount difference between invoice amount and (skonto + transaction amount) is smaller than TOLERANCE_SKONTO 
def _equal_tolerated(a: Decimal, b: Decimal, tolerance: Decimal = config.TOLERANCE_SKONTO):
    if b.is_nan():
        return False
    return abs(a - b) <= tolerance 


def exclude(incoming_bank_statement_df, all_invoice_numbers_in_invoice_list) :

    # Results type 1. not found (no invoice number in Verwendungszweck) 
    # -> Report "Zahlungseingänge ohne erkennbare Rechnungsnummer"
    no_valid_invoice_incoming_bank_statement_df = incoming_bank_statement_df[
        incoming_bank_statement_df["extrahierte_rechnungsnummer"].apply(len) == 0
        ]
    report_no_valid_invoice_incoming_bank_statement_df = no_valid_invoice_incoming_bank_statement_df.copy()
    report_no_valid_invoice_incoming_bank_statement_df = report_no_valid_invoice_incoming_bank_statement_df.drop(columns=["extrahierte_rechnungsnummer"])
    for date_col in ["buchungstag", "wertstellung"]:
        report_no_valid_invoice_incoming_bank_statement_df[date_col] = report_no_valid_invoice_incoming_bank_statement_df[date_col].dt.date

    # Results type 2. not found (at least 1 extracted invoice number is not in ausgangsrechnung.csv)
    # -> Report "Zahlungseingänge mit nicht zuordenbarer Rechnungsnummer"
    def _have_extracted_invoice_not_in_list(extracted_list):
        return any( invoice_no not in all_invoice_numbers_in_invoice_list 
                   for invoice_no in extracted_list
                   )

    def _extracted_invoice_not_in_list(extracted_list):
        return [invoice_no for invoice_no in extracted_list if invoice_no not in all_invoice_numbers_in_invoice_list]

    has_invoice_number_mask = incoming_bank_statement_df["extrahierte_rechnungsnummer"].apply(len) > 0
    invoice_not_in_list = incoming_bank_statement_df["extrahierte_rechnungsnummer"].apply(_have_extracted_invoice_not_in_list) 

    have_extracted_invoice_number_not_in_list_df = incoming_bank_statement_df[has_invoice_number_mask & invoice_not_in_list].copy()                                                                          

    report_have_extracted_invoice_number_not_in_list_df = have_extracted_invoice_number_not_in_list_df.copy()
    extracted_invoice_not_in_list_series = report_have_extracted_invoice_number_not_in_list_df["extrahierte_rechnungsnummer"].apply(_extracted_invoice_not_in_list)
    report_have_extracted_invoice_number_not_in_list_df["extrahierte_rechnung_nicht_in_ausgangsrechnung"] = extracted_invoice_not_in_list_series

    for date_col in ["buchungstag", "wertstellung"]:
        report_have_extracted_invoice_number_not_in_list_df[date_col] = report_have_extracted_invoice_number_not_in_list_df[date_col].dt.date


    # Get Dataframe where all extracted invoices are in ausgangsrechnung.csv
    valid_invoice_incoming_bank_statement_df = incoming_bank_statement_df.drop(
        index=no_valid_invoice_incoming_bank_statement_df.index.union(
            have_extracted_invoice_number_not_in_list_df.index
            ))

    return report_no_valid_invoice_incoming_bank_statement_df, report_have_extracted_invoice_number_not_in_list_df, valid_invoice_incoming_bank_statement_df



@dataclass
class MatchResult:
    transaction_ids: List[int]
    invoice_numbers: List[str]
    shape_label: str          # "1:1" / "N:1" / "1:N" / "N:M"
    zuordnungsart: str        # "matched" / "unmatched" / "unsupported N:M"
    grund: str                # "exact match 1:1" / "skonto match 1:1" / ...
    betrag_diff:Optional[Decimal] = None       # invoice amount - transaction amount


def result(group, zuordnungsart, grund, betrag_diff=None):
    return MatchResult(
        transaction_ids=group.transaction_ids,
        invoice_numbers=group.invoice_numbers,
        shape_label=group.shape_label,
        zuordnungsart=zuordnungsart,
        grund=grund,
        betrag_diff=betrag_diff,
    )


def match1to1(group, invoices_df, valid_invoice_incoming_bank_statement_df):
    invoice_row = invoices_df.loc[group.invoice_numbers[0]]
    txn_row = valid_invoice_incoming_bank_statement_df.loc[group.transaction_ids[0]]

    invoice_amount = Decimal(str(invoice_row["rechnungsbetrag"]))
    txn_amount = Decimal(str(txn_row["betrag"]))
    diff = invoice_amount - txn_amount

    if diff == 0:
        # Type 3
        return result(group, "MATCHED" , "EXACT_MATCH_1_1")

    skonto_amount = _skonto_amount(invoice_row)
    skonto_matches = _equal_tolerated(diff, skonto_amount)
    skonto_valid = _skonto_is_valid(invoice_row, txn_row["wertstellung"])

    if skonto_matches and skonto_valid:
        # Type 4
        return result(group, "MATCHED" , "SKONTO_MATCH_1_1")
    elif skonto_matches and not skonto_valid:
        # Type 5
        return result(group, "UNMATCHED" , "INVALID_SKONTO_1_1", betrag_diff=diff)
    else:
        # Type 6
        return result(group, "UNMATCHED" , "WRONG_AMOUNT_1_1", betrag_diff=diff)


def matchNto1(group, invoices_df, valid_invoice_incoming_bank_statement_df):
    total_invoice_amount = sum(Decimal(str(invoices_df.loc[i, "rechnungsbetrag"])) for i in group.invoice_numbers)
    total_txn_amount = sum(Decimal(str(valid_invoice_incoming_bank_statement_df.loc[t, "betrag"])) for t in group.transaction_ids)
    diff = total_invoice_amount - total_txn_amount

    if diff == 0:
        return result(group, "MATCHED" , "SPLIT_MATCH_N_1")
    else:
        return result(group, "UNMATCHED" , "SPLIT_UNMATCH_N_1", betrag_diff=diff)


def match1toN(group, invoices_df, valid_invoice_incoming_bank_statement_df):
    total_invoice_amount = sum(Decimal(str(invoices_df.loc[i, "rechnungsbetrag"])) for i in group.invoice_numbers)
    total_txn_amount = sum(Decimal(str(valid_invoice_incoming_bank_statement_df.loc[t, "betrag"])) for t in group.transaction_ids)
    diff = total_invoice_amount - total_txn_amount

    if diff == 0:
        return result(group, "MATCHED" , "COMBINED_MATCH_1_N")
    else:
        return result(group, "UNMATCHED" , "COMBINED_UNMATCH_1_N", betrag_diff=diff)

def matchMtoN(group):
    return result(group, "UNSUPPORTED" , "UNSUPPORTED_NM")
    
def match_group(group, invoices_df, valid_invoice_incoming_bank_statement_df):
    dispatch = {
        "1:1": match1to1,
        "N:1": matchNto1,
        "1:N": match1toN,
    }
    if group.shape_label == "N:M":
        return matchMtoN(group)
    return dispatch[group.shape_label](group, invoices_df, valid_invoice_incoming_bank_statement_df)


def not_in_matching_results(invoices_df, unique_inv_no_matching, unique_inv_no_extracted_not):
    not_in_matching_results = invoices_df[~invoices_df["rechnungsnummer"].isin(unique_inv_no_matching)].copy()
    not_in_matching_results["mögliche_zahlung_mit_nicht_zuordenbarer_ausgangsrechnungsnummer"] = np.where(not_in_matching_results["rechnungsnummer"].isin(unique_inv_no_extracted_not), "Y", "")

    for date_col in ["rechnungsdatum", "faelligkeitsdatum", "skonto_datum"]:
        not_in_matching_results[date_col] = not_in_matching_results[date_col].dt.date


    return not_in_matching_results