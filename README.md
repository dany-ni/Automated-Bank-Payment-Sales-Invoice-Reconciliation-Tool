
# Automated Bank Payment–Sales Invoice Reconciliation Tool

A Python tool that automatically matches incoming bank payments to sales 
invoices, including split/combined payments and early-payment discount (*Skonto*) validation, flags ambiguous cases for manual review and produces Excel reports.

Throughout this document, "invoice" refers to a sales invoice (*Ausgangsrechnung*) issued by the company, and "payment" refers to an incoming payment (*Zahlungseingang*) recorded on the bank statement.


## Note on data
All example data in this repository (`data/` and `reports/`) is synthetic. It was generated for demonstration purposes only and does not represent any real person, company, bank account, or transaction.

## The problem

When finance goes through the bank statement (*Kontoauszug*) and checks incoming payments against the list of sales invoices (*Ausgangsrechnungen*), these questions are often raised:
Which invoice does this payment belong to?
Is the amount correct? Did the customer take an early-payment discount, and
if so, was it still within the deadline? Were several invoices paid in one
transfer, or was one invoice paid in several transfers?

This tool helps finance answer these questions efficiently while avoiding a lot of repetitive manual work and mistakes.


## Core assumptions

This tool has the following assumptions:

1. The invoice number appears in the payment reference text (*Verwendungszweck*). The tool tolerates common formatting variations and tries to match them to the standard format. If no invoice number can be extracted, the payment falls into Report 1 for manual review. 

2. The standard format of an invoice is "RE-4 digits-4 digits", e.g., RE-2026-0003. The tool can not only match the standard format, but also match formatting variations, e.g. RE 2026-0006, re-2026-0011, RE/2026/0015, RE20260004. 

3. An early-payment discount (*Skonto*) is valid if the Wertstellungsdatum in the bank statement (*Kontoauszug*) is earlier than or equal to the Skontodatum in the list of sales invoices (*Ausgangsrechnungen*).

If you want to match different standard formats of invoices, you could change INVOICE_NUMBER_PATTERN in config.py.

Tolerance (±0.01) is only used when an early-payment discount (*Skonto*) is considered, because applying the Skonto percentage to the invoice amount may cause a tiny rounding discrepancy. You could change the tolerance by changing TOLERANCE_SKONTO in config.py.



## What this tool does

It takes two CSV exports — the bank statement and the sales invoice list — and:

1. **Extracts invoice numbers** from each payment's reference text
   (*Verwendungszweck*), including informal formats.
2. **Groups** payments and invoices by the invoice numbers they reference.
   One payment can reference one invoice, or several invoices, and several payments can
   reference one invoice, or several invoices.
3. **Checks the amounts**, including whether a shortfall matches a valid
   early-payment discount (*Skonto*) based on the payment date (*Wertstellungsdatum*). 
4. **Produces four Excel reports**, showing what is
   confirmed and what still needs manual review.

## Output: four reports

*(Report 3 is generated in two language versions — English and German — so five Excel files are produced in total.)*

| # | Report | What it contains | What to do with it |
|---|--------|-------------------|---------------------|
| 1 | Incoming Payments Without a Recognizable Sales Invoice Number (*Zahlungseingänge ohne erkennbare Ausgangsrechnungsnummer*) | Payments whose reference text contains no invoice number matching INVOICE_NUMBER_PATTERN (e.g., a typo, or contains no invoice number) | Check the reference text manually |
| 2 | Incoming Payments With an Untraceable Sales Invoice Number (*Zahlungseingänge mit nicht zuordenbarer Ausgangsrechnungsnummer*) | Payments where at least one extracted invoice number does not match any invoice on the list of sales invoices (e.g. a typo, or an invoice from a different period) | Verify the extracted invoice number against the list of sales invoices |
| 3 | Incoming Payments With a Traceable Sales Invoice Number (*Zahlungseingänge mit zuordenbarer Ausgangsrechnungsnummer*) | Every payment that could be linked to invoice(s) on the list of sales invoices. For patterns the tool can fully evaluate (one-to-one, split, and combined payments), it shows the invoice amount, the paid amount, any difference, and a plain-language result (see the note below). Many-to-many patterns skip the amount comparison entirely and require manual review. | Review anything not marked as a clean match |
| 4 | Sales Invoices Without a Traceable Incoming Payment (*Ausgangsrechnungen ohne zuordenbaren Zahlungseingang*) | Invoices on the list of sales invoices that do not appear in Report 3 | Check the invoice manually |

**Report 3** classifies every match into one of these outcomes:

- **Exact matched 1:1** — one payment matched to exactly one invoice, and the amounts agree exactly.
- **Skonto matched 1:1** — one payment matched to exactly one invoice; the shortfall matched the invoice's early-payment discount, and the payment was made within the discount deadline.
- **Invalid Skonto 1:1** — one payment matched to exactly one invoice; the shortfall matched the discount amount, but the payment was made after the discount deadline, so the discount is not valid and should be manually reviewed.
- **Wrong amount 1:1** — one payment matched to exactly one invoice; the amounts do not match, and the difference is not equal to a discount.
- **Split payment matched / unmatched N:1** — several payments together reference one invoice; "matched" means the total amount of payments agrees with the invoice amount.
- **Combined payment matched / unmatched 1:N** — one payment references several invoices; "matched" means the payment agrees with the total amount of invoices.
- **Unsupported pattern N:M (many-to-many)** — several payments collectively reference several invoices; the tool flags this for manual review.


**A note on Reports 2 and 4:** 
the same invoice number can show
up in both. Report 2 flags a payment where at least one of the invoice numbers extracted from the reference text is not on the list of sales invoices. Report 4 flags an invoice that is on the list of sales invoices but not given any status in report 3. If an invoice shows up in Report 4 with the
`mögliche_zahlung_mit_nicht_zuordenbarer_ausgangsrechnungsnummer` flag set to **Y**, it means a payment
does mention this invoice number, but that same payment also mentions
another number that is not on the list of sales invoices. It is worth checking this invoice in Report 2. If the flag is **N**, it means
Report 2 did not find such a clue. This does not rule out a possible match already flagged in Report 1. It is worth checking Report 1 before regarding an invoice as unpaid.


## Known limitations

These are deliberate, conservative design choices rather than oversights.
In a finance context, it is safer for the tool to flag something as
needing human review than to guess:

- **Early-payment discount (Skonto) validity is only evaluated for one-to-one payment–invoice matches.** For split or combined payments, any price difference is marked as "unmatched" without checking for early-payment discounts. Automatically allocating a discount across multiple payments or invoices could easily be wrong, since they may have different payment dates, discount rates, or deadlines.

- **Many-to-many patterns are not resolved automatically.** 
The tool flags these cases as "unsupported" rather than attempting to split and compare amounts between them, because an automatic allocation could easily be wrong.


- **Matching relies on the invoice number in the payment reference text.**
If the payment reference text does not include an invoice number, or include a number the regular expression can not recognize, the payment falls into Report 1 or 2 for
manual review.


## Project structure

| File | Responsibility |
|------|----------------|
| `bank_invoice_parse.py` | Loads and cleans the two raw CSV files; extracts invoice numbers from payment references |
| `grouping.py` | Groups payments and invoices by which invoice numbers they reference (1:1, N:1, 1:N, N:M) |
| `matcher.py` | Applies the matching and discount-validity rules to each group |
| `reports.py` | Builds Report 3 (in English and German) and writes all 5 report files to Excel |
| `translations.py` | Provides English and German versions for report 3 |
| `main.py` | Runs the full pipeline end to end |
