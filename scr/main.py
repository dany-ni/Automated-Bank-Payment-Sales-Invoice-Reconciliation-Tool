from __future__ import annotations
import bank_invoice_parse
import grouping
import matcher
import reports
import config
import pandas as pd
from dataclasses import asdict


if __name__ == "__main__":

    bank_statement_df = bank_invoice_parse.load_bank_statement(config.KONTOAUSZUG_PATH)
    invoices_df = bank_invoice_parse.load_invoices(config.AUSGANGSRECHNUNGEN_PATH)

    incoming_bank_statement_df = bank_statement_df[bank_statement_df["betrag"] > 0].copy()
    excluded_bank_statement_df = bank_statement_df[bank_statement_df["betrag"] <= 0].copy()

    invoices_df = invoices_df.set_index("rechnungsnummer", drop=False)

    all_invoice_numbers_in_invoice_list = set(invoices_df["rechnungsnummer"])

    first_results = matcher.exclude(incoming_bank_statement_df, all_invoice_numbers_in_invoice_list)

    no_valid_invoice_incoming_bank_statement_df = first_results[0]
    have_extracted_invoice_number_not_in_list_df = first_results[1]
    valid_invoice_incoming_bank_statement_df = first_results[2]

    groups = grouping.build_groups(valid_invoice_incoming_bank_statement_df)

    matching_results = [matcher.match_group(g, invoices_df, valid_invoice_incoming_bank_statement_df) for g in groups]
    matching_results_df = pd.DataFrame([asdict(r) for r in matching_results])


    unique_inv_no_matching = matching_results_df["invoice_numbers"].explode().unique().tolist()
    unique_inv_no_extracted_not = have_extracted_invoice_number_not_in_list_df["extrahierte_rechnungsnummer"].explode().unique().tolist()

    not_in_matching_results_df = matcher.not_in_matching_results(invoices_df, unique_inv_no_matching, unique_inv_no_extracted_not)

    matching_results_en_df = reports.build_type3to11_report(matching_results_df, invoices_df, incoming_bank_statement_df)
    matching_results_de_df = reports.build_type3to11_report(matching_results_df, invoices_df, incoming_bank_statement_df, "de")


    reports.save_to_excel(no_valid_invoice_incoming_bank_statement_df, config.REPORT_1_PATH)
    reports.save_to_excel(have_extracted_invoice_number_not_in_list_df, config.REPORT_2_PATH)
    reports.save_to_excel(matching_results_en_df, config.REPORT_3_PATH_EN)
    reports.save_to_excel(matching_results_de_df, config.REPORT_3_PATH_DE)
    reports.save_to_excel(not_in_matching_results_df, config.REPORT_4_PATH)

