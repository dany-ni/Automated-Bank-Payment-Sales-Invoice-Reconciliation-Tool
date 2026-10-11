import pandas as pd
import re
import config
from decimal import Decimal 



def _parse_amount(amount):
    """
    Convert german amount string to .
    e.g. "1.000,10" to "1000.10" 
    """
    if pd.isna(amount):
        return float('nan')
    cleaned = str(amount).strip().replace(".","").replace(",",".")
    if cleaned == "":
        return float("nan")
    return Decimal(cleaned)


def _extract_invoice_number(verwendungszweck):
    """
    Extract formal invoice number from verwendungszweck in bank statement, e.g. RE-2026-0003
    Also extract informal invoice numbers, e.g. RE 2026-0006, re-2026-0011, RE/2026/0015, RE20260004 
    """
    # If verwendungszweck is not a string, return []
    if not isinstance(verwendungszweck, str):
        return []
    matches = config.INVOICE_NUMBER_PATTERN.findall(verwendungszweck)
    invoice_number_list = []
    for prefix, number in matches:
        digits = re.sub(r"\D", "", number)   
        invoice_number_list.append(f"{prefix.upper()}-{digits[:4]}-{digits[4:]}")
    return invoice_number_list


def load_bank_statement(path):
    """
    Load and clean Kontoauszug.csv, export into a DataFrame
    """
    df = pd.read_csv(path, delimiter=config.DELIMITER, dtype=str)
    df.columns = [c.strip().lower() for c in df.columns]

    # Clean date column
    df["buchungstag"] = pd.to_datetime(df["buchungstag"], format=config.DATE_FORMAT)
    df["wertstellung"] = pd.to_datetime(df["wertstellung"], format=config.DATE_FORMAT)

    # Parse amount column: 
    df["betrag"] = df["betrag"].apply(_parse_amount)

    # Clean string columns: strip stray whitespace
    df["verwendungszweck"] = df["verwendungszweck"].str.strip()
    df["auftraggeber_empfaenger"] = df["auftraggeber_empfaenger"].str.strip()
    df["iban"] = df["iban"].str.strip()

    # Add extract_invoice_number column
    df["extrahierte_rechnungsnummer"] = df["verwendungszweck"].apply(_extract_invoice_number)

    return df


def load_invoices(path):
    """
    Load and clean Rechnungen.csv, export into a DataFrame
    """    
    df = pd.read_csv(path, delimiter=config.DELIMITER, dtype=str)
    df.columns = [c.strip().lower() for c in df.columns]

    # Clean date column
    df["faelligkeitsdatum"] = pd.to_datetime(df["faelligkeitsdatum"], format=config.DATE_FORMAT)
    df["rechnungsdatum"] = pd.to_datetime(df["rechnungsdatum"], format=config.DATE_FORMAT)
    df["skonto_datum"] = pd.to_datetime(df["skonto_datum"], format=config.DATE_FORMAT)

    # Parse amount column: 
    df["rechnungsbetrag"] = df["rechnungsbetrag"].apply(_parse_amount)
    df["nettobetrag"] = df["nettobetrag"].apply(_parse_amount)
    df["ust_satz"] = df["ust_satz"].apply(_parse_amount)
    df["skonto_prozent"] = df["skonto_prozent"].apply(_parse_amount)

    # Clean day column
    df["skonto_frist_tage"] = df["skonto_frist_tage"].astype(int)

    # Clean string columns: strip stray whitespace
    df["rechnungsnummer"] = df["rechnungsnummer"].str.strip()
    df["kunde"] = df["kunde"].str.strip()
    df["kunde_iban"] = df["kunde_iban"].str.strip()

    return df













