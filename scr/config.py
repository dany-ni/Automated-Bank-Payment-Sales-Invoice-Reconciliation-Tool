import re
from decimal import Decimal


# Path
KONTOAUSZUG_PATH = "kontoauszug.csv"
AUSGANGSRECHNUNGEN_PATH = "ausgangsrechnung.csv"

REPORT_1_PATH = "1 Zahlungseingänge ohne erkennbare Ausgangsrechnungsnummer.xlsx"
REPORT_2_PATH = "2 Zahlungseingänge mit nicht zuordenbarer Ausgangsrechnungsnummer.xlsx"
REPORT_3_PATH_EN = "3 Zahlungseingänge mit zuordenbarer Ausgangsrechnungsnummer (EN).xlsx"
REPORT_3_PATH_DE = "3 Zahlungseingänge mit zuordenbarer Ausgangsrechnungsnummer (DE).xlsx"
REPORT_4_PATH = "4 Ausgangsrechnungen ohne zuordenbaren Zahlungseingang.xlsx"


# Parse German-format CSV 
DELIMITER = ";"
DATE_FORMAT = "%d.%m.%Y"


# Tolerance only for Skonto match, since Skonto*Skonto percentage may cause discrepancy
TOLERANCE_SKONTO = Decimal("0.01")


# Invoice number pattern 
#Extract formal invoice number from verwendungszweck in bank statement, e.g. RE-2026-0003
#Also extract informal invoice numbers, e.g. RE 2026-0006, re-2026-0011, RE/2026/0015, RE20260004 

INVOICE_NUMBER_PATTERN = re.compile(r"\b([Rr][Ee])\.?[\s\-/]?(\d{4}[\/\-]?\d{4})\b") 