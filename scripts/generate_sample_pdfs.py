from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

DOCUMENTS = {
    "banking_faq.pdf": {
        "title": "Banking Frequently Asked Questions",
        "content": [
            "A savings account allows customers to deposit money, earn interest, and withdraw funds while following the bank's transaction rules.",
            "To open a standard savings account, customers usually need Aadhaar or another government ID, PAN, address proof, and a recent passport-size photograph.",
            "Banks may ask for an initial deposit amount depending on product type, branch policy, and account category.",
            "Customers who want to check account balance can use mobile banking, internet banking, ATMs, passbook updates, SMS banking, or call official customer care after verification.",
            "Before discussing account details such as registered mobile number, branch, account status, or last transactions, the bank should verify the customer using secure authentication steps.",
            "If a customer asks for sensitive account information in chat, the safe response is to guide them to logged-in banking channels or branch support instead of exposing private data directly.",
            "If a debit card is lost, customers should block the card immediately through mobile banking, internet banking, customer care, or the branch.",
            "ATM cash withdrawal limits and daily transfer limits vary by bank and account profile.",
        ],
    },
    "account_services.pdf": {
        "title": "Account Services and Balance Support",
        "content": [
            "Customers may request balance enquiry, mini statement, cheque book status, debit card status, branch details, and account service requests through secure authenticated channels.",
            "Banks should not reveal full account numbers, complete balances, or recent transaction history in an unauthenticated public chat session.",
            "For balance-related requests, the assistant should ask the customer to use secure channels such as mobile banking, internet banking, ATM, passbook printing, or official phone banking after identity verification.",
            "If a customer cannot access their balance because of app login issues, they should reset credentials using official recovery steps or contact bank support.",
            "When a customer asks about account status, the assistant can explain the process, required verification, and available support channels without exposing private account data.",
        ],
    },
    "rbi_guidelines.pdf": {
        "title": "RBI Customer Awareness and Safe Banking Guidance",
        "content": [
            "Customers should never share OTPs, ATM PINs, CVV numbers, or internet banking passwords with anyone, including someone claiming to be from the bank.",
            "Before using an ATM, customers should inspect the keypad, card slot, and surrounding area for suspicious devices that could indicate skimming.",
            "Suspicious digital payment or account activity should be reported immediately to the bank's fraud helpline and to the cybercrime reporting system.",
            "Banks should follow customer due diligence and KYC practices to verify identity, address, and risk indicators at onboarding and during periodic updates.",
            "Account opening and service changes may require re-validation of customer information when there is a mismatch or expired documentation.",
        ],
    },
    "loan_policy.pdf": {
        "title": "Retail Loan Policy Overview",
        "content": [
            "Home loan assessment usually considers income stability, repayment capacity, property documents, age, and credit profile.",
            "Typical home loan documents include Aadhaar, PAN, salary slips or business income proof, bank statements, property papers, and photographs.",
            "Personal loan approval may depend on employer profile, minimum income, past repayment behavior, and existing obligations.",
            "Banks may request additional documents when the property is under construction, jointly owned, or located in a restricted legal zone.",
            "Final loan sanction is subject to internal verification, legal clearance, valuation, and policy checks.",
        ],
    },
    "credit_card_guidelines.pdf": {
        "title": "Credit Card Support and Usage Guidelines",
        "content": [
            "Credit card applications generally require identity proof, address proof, income proof, and a completed application form.",
            "If a credit card transaction is disputed, customers should contact support promptly and share the transaction date, amount, and merchant details.",
            "Customers should review billing statements each month and report unauthorized transactions without delay.",
            "Cardholders should avoid using public Wi-Fi for card payments unless the connection and merchant are trusted.",
            "Replacement cards for damaged or expired cards are usually sent after customer verification and address confirmation.",
        ],
    },
    "fraud_awareness.pdf": {
        "title": "Fraud Awareness for Banking Customers",
        "content": [
            "Phishing attacks often use urgent language, fake login links, or reward claims to trick customers into sharing credentials.",
            "A genuine bank representative will not ask for OTP, MPIN, full card details, or internet banking password over phone, SMS, or email.",
            "If fraud is suspected, customers should block affected channels immediately and raise a complaint with the bank.",
            "Customers should enable transaction alerts so they can detect unusual account activity quickly.",
            "Fraud complaints are easier to investigate when the customer keeps screenshots, timestamps, and reference numbers.",
        ],
    },
}


def generate_pdf(file_name: str, title: str, paragraphs: list[str]) -> None:
    path = DATA_DIR / file_name
    doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=50, leftMargin=50, topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    title_style = styles["Heading1"]
    body_style = styles["BodyText"]
    body_style.leading = 16
    body_style.spaceAfter = 10

    story = [Paragraph(title, title_style), Spacer(1, 16)]
    for paragraph in paragraphs:
        story.append(Paragraph(paragraph, body_style))
        story.append(Spacer(1, 8))

    doc.build(story)


def generate_markdown(file_name: str, title: str, paragraphs: list[str]) -> None:
    markdown_name = Path(file_name).with_suffix(".md")
    markdown_path = DATA_DIR / markdown_name
    lines = [f"# {title}", ""]
    for paragraph in paragraphs:
        lines.append(f"- {paragraph}")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


for name, payload in DOCUMENTS.items():
    generate_pdf(name, payload["title"], payload["content"])
    generate_markdown(name, payload["title"], payload["content"])

print(f"Generated {len(DOCUMENTS)} sample PDFs and Markdown files in {DATA_DIR}")
