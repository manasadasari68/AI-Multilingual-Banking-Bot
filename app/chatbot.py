import logging
from typing import Dict, List, Tuple

import requests

from app.config import (
    MAX_HISTORY_MESSAGES,
    OPENROUTER_API_BASE,
    OPENROUTER_API_KEY,
    OPENROUTER_APP_NAME,
    OPENROUTER_HTTP_REFERER,
    OPENROUTER_MODEL,
    TOP_K,
)
from app.customer_data import find_customer_from_history, find_customer_in_text
from app.language_detector import detect_language
from app.translator import translate_text

logger = logging.getLogger(__name__)

BANKING_SYSTEM_PROMPT = """
You are an AI multilingual banking support assistant.
Answer only with information grounded in the retrieved banking context when it is relevant.
If the documents do not contain the answer, say that clearly and provide a safe, general banking guidance note.
Keep answers concise, practical, and customer-friendly.
Prioritize these topics when they appear: loans, KYC, credit cards, account opening, fraud awareness, and ATM support.
Never invent policy numbers, interest rates, or eligibility rules that are not present in the context.
""".strip()


def build_chatbot(vector_store) -> Dict[str, object]:
    return {
        "retriever": vector_store.as_retriever(search_kwargs={"k": TOP_K}),
    }


def _resolve_language(query: str, preferred_language: str | None) -> Dict[str, str]:
    if preferred_language:
        return {
            "code": preferred_language,
            "name": preferred_language,
            "confidence": "1.00",
        }
    detected = detect_language(query)
    return detected


def _normalize_language_name(language_code: str) -> str:
    language_names = {
        "en": "English",
        "hi": "Hindi",
        "te": "Telugu",
        "ta": "Tamil",
    }
    return language_names.get(language_code, "English")


def _looks_like_ascii_text(text: str) -> bool:
    return text.isascii()


def _translate_query_with_llm(query: str, language_code: str) -> str:
    response = requests.post(
        f"{OPENROUTER_API_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": OPENROUTER_HTTP_REFERER,
            "X-Title": OPENROUTER_APP_NAME,
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_MODEL,
            "temperature": 0.0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Convert the user's banking question to clear English. "
                        "The user may have typed a Telugu, Hindi, or Tamil sentence using English letters. "
                        "Return only the English translation."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Language code: {language_code}\nText: {query}",
                },
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    return payload["choices"][0]["message"]["content"].strip()


def _translate_for_retrieval(query: str, language_code: str) -> str:
    translated_query = query if language_code == "en" else translate_text(query, dest="en", source=language_code)
    if language_code != "en" and _looks_like_ascii_text(query):
        llm_translation = _translate_query_with_llm(query, language_code)
        if llm_translation:
            translated_query = llm_translation
    return translated_query


def _handle_small_talk(query_en: str) -> str | None:
    normalized = " ".join(query_en.lower().split())
    thanks_patterns = ["thank you", "thanks", "okay thank you", "ok thank you", "thanks a lot"]
    greeting_patterns = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]

    if normalized in thanks_patterns or any(normalized.startswith(pattern) for pattern in thanks_patterns):
        return "You're welcome. Let me know if you need any more help with your banking questions."
    if normalized in greeting_patterns:
        return "Hello. How can I help you with your banking needs today?"
    return None


def _format_history(history: List[Dict[str, str]]) -> str:
    trimmed_history = history[-MAX_HISTORY_MESSAGES:]
    if not trimmed_history:
        return "No prior conversation."

    lines = []
    for item in trimmed_history:
        role = item.get("role", "user").capitalize()
        content = item.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines) if lines else "No prior conversation."


def _format_context(documents) -> Tuple[str, List[Dict[str, str]]]:
    if not documents:
        return "No relevant document context found.", []

    context_blocks: List[str] = []
    sources: List[Dict[str, str]] = []
    for index, doc in enumerate(documents, start=1):
        source_name = doc.metadata.get("source", "Unknown source")
        page_number = doc.metadata.get("page")
        page_label = str(page_number + 1) if isinstance(page_number, int) else "N/A"
        excerpt = " ".join(doc.page_content.split())
        context_blocks.append(f"[Source {index} | {source_name} | page {page_label}] {excerpt}")
        sources.append(
            {
                "source": source_name,
                "page": page_label,
                "snippet": excerpt[:220],
            }
        )
    return "\n\n".join(context_blocks), sources


def _contains_any(text: str, patterns: List[str]) -> bool:
    lowered = text.lower()
    return any(pattern in lowered for pattern in patterns)


def _contains_pronoun_reference(text: str) -> bool:
    lowered = f" {text.lower()} "
    pronouns = [" my ", " mine ", " me ", " his ", " her ", " their ", " our "]
    return any(pronoun in lowered for pronoun in pronouns)


def _is_customer_intent_query(text: str) -> bool:
    lowered = text.lower()
    customer_terms = [
        "customer name",
        "full name",
        "full_name",
        "name on account",
        "customer id",
        "customer_id",
        "cust",
        "balance",
        "account number",
        "acct number",
        "branch",
        "ifsc",
        "registered mobile",
        "mobile number",
        "phone number",
        "account type",
        "type of account",
        "transactions",
        "transaction",
        "mini statement",
        "statement",
        "bank details",
        "account details",
    ]
    pronoun_terms = ["his", "her", "their", "my", "mine", "our"]
    return any(term in lowered for term in customer_terms) or any(term in lowered.split() for term in pronoun_terms)


def _has_explicit_unknown_customer_reference(
    query: str,
    translated_query: str,
    customers: List[Dict[str, object]],
) -> bool:
    if find_customer_in_text(query, customers) or find_customer_in_text(translated_query, customers):
        return False

    original_lower = query.lower()
    translated_lower = translated_query.lower()

    if _contains_pronoun_reference(query) or _contains_pronoun_reference(translated_query):
        return False

    markers = [" account", " khata", " katha", " ఖాతా"]
    for marker in markers:
        index = original_lower.find(marker)
        if index > 0:
            preceding = original_lower[:index].strip().split()
            if preceding:
                candidate = preceding[-1].strip(".,?!")
                if candidate and candidate not in {"my", "your", "his", "her", "their", "the"}:
                    return True

    if "'s" in translated_lower:
        return True

    words = [word.strip(".,?!") for word in translated_lower.split()]
    account_words = {"account", "balance", "branch", "ifsc", "transactions", "details"}
    for i, word in enumerate(words[:-1]):
        next_word = words[i + 1]
        if next_word in account_words and word not in {"my", "your", "his", "her", "their", "the"}:
            return True

    return False


def _is_account_type_query(text: str) -> bool:
    lowered = text.lower()
    return "type" in lowered and any(term in lowered for term in ["account", "acount", "acct"])


def _mentions_customer_explicitly(text: str, customer: Dict[str, object]) -> bool:
    lowered = text.lower()
    full_name = str(customer["full_name"]).lower()
    first_name = full_name.split()[0]
    return full_name in lowered or first_name in lowered


def _is_self_query(text: str, customer: Dict[str, object], from_history_only: bool) -> bool:
    lowered = text.lower()
    if _mentions_customer_explicitly(text, customer) or " her " in f" {lowered} " or " his " in f" {lowered} " or " their " in f" {lowered} ":
        return False
    self_markers = [" my ", " me ", " mine ", " i ", " i'm ", " i am ", "can i", "what is my", "my account"]
    padded = f" {lowered} "
    if any(marker in padded for marker in self_markers):
        return True
    return from_history_only and not _mentions_customer_explicitly(text, customer)


def _subject(customer: Dict[str, object], self_query: bool) -> str:
    return "your" if self_query else f"{customer['full_name']}'s"


def _mask_account_number(account_number: str) -> str:
    return f"XXXXXX{account_number[-4:]}"


def _format_currency(amount: float, currency: str) -> str:
    if currency == "INR":
        return f"Rs. {amount:,.2f}"
    return f"{currency} {amount:,.2f}"


def _recent_transactions_text(customer: Dict[str, object], count: int = 3) -> str:
    transactions = list(customer["last_transactions"])[:count]
    numbered = [f"{index}. {item}" for index, item in enumerate(transactions, start=1)]
    return " ".join(numbered)


def _build_customer_response(query_en: str, customer: Dict[str, object], self_query: bool) -> str:
    subject = _subject(customer, self_query)
    parts: List[str] = []

    wants_customer_name = _contains_any(query_en, ["customer name", "full name", "full_name", "name on account"])
    wants_customer_id = _contains_any(query_en, ["customer id", "customer_id", "cust id", "cust"])
    wants_balance = _contains_any(query_en, ["balance", "bank balance", "available balance"])
    wants_account_number = _contains_any(query_en, ["account number", "acct number"])
    wants_branch = _contains_any(query_en, ["branch", "home branch"])
    wants_ifsc = _contains_any(query_en, ["ifsc", "branch code"])
    wants_mobile = _contains_any(query_en, ["mobile", "phone", "registered number"])
    wants_account_type = _contains_any(query_en, ["account type", "type of account"]) or _is_account_type_query(query_en)
    wants_transactions = _contains_any(query_en, ["mini statement", "recent transactions", "last transactions", "transactions"])
    wants_details = _contains_any(query_en, ["details", "account details", "my details", "bank details"])

    transaction_count = 3
    lowered_query = query_en.lower()
    if "last 2" in lowered_query or "recent 2" in lowered_query or "two transactions" in lowered_query:
        transaction_count = 2

    if wants_customer_name:
        parts.append(f"The customer name for {subject} account is {customer['full_name']}.")
    if wants_balance:
        parts.append(
            f"The available balance in {subject} account is "
            f"{_format_currency(customer['available_balance'], customer['currency'])}."
        )
    if wants_customer_id:
        parts.append(f"The customer ID for {subject} account is {customer['customer_id']}.")
    if wants_account_number:
        parts.append(
            f"The account number for {subject} account ends with "
            f"{_mask_account_number(customer['account_number'])}."
        )
    if wants_branch:
        parts.append(f"The branch for {subject} account is {customer['branch']}.")
    if wants_ifsc:
        parts.append(f"The IFSC code for {subject} account is {customer['ifsc']}.")
    if wants_mobile:
        parts.append(f"The registered mobile number for {subject} account is {customer['registered_mobile']}.")
    if wants_account_type:
        parts.append(f"{subject.capitalize()} account type is {customer['account_type']}.")
    if wants_transactions:
        parts.append(
            f"The recent transactions for {subject} account are: "
            f"{_recent_transactions_text(customer, count=transaction_count)}"
        )
    if wants_details:
        parts.append(
            f"Here are the account details for {subject} account: "
            f"customer ID {customer['customer_id']}, account type {customer['account_type']}, branch {customer['branch']}, "
            f"IFSC {customer['ifsc']}, registered mobile {customer['registered_mobile']}, "
            f"and account number ending with {_mask_account_number(customer['account_number'])}."
        )

    if parts:
        return " ".join(parts)

    return (
        f"I found the demo bank record for {customer['full_name']}. "
        "You can ask about balance, account type, branch, IFSC, registered mobile, or recent transactions."
    )


def _handle_customer_lookup(
    query: str,
    translated_query: str,
    history: List[Dict[str, str]],
    customers: List[Dict[str, object]],
) -> str | None:
    if not _is_customer_intent_query(translated_query):
        return None

    customer_from_history = False
    customer = find_customer_in_text(query, customers)
    if customer is None:
        customer = find_customer_in_text(translated_query, customers)
    if customer is None:
        if _has_explicit_unknown_customer_reference(query, translated_query, customers):
            return (
                "I could not find that customer account in the demo records. "
                "Please create an account or contact your branch or customer support for help."
            )
        customer = find_customer_from_history(history, customers)
        customer_from_history = customer is not None

    if customer is None:
        if _is_customer_intent_query(translated_query) or _is_account_type_query(translated_query):
            return (
                "I can help with demo customer account details. "
                "Please provide the customer name, customer ID, or account number first, for example Ravi Kumar, CUST1014, or account 451278903214."
            )
        return None

    self_query = _is_self_query(query, customer, customer_from_history) or _is_self_query(translated_query, customer, customer_from_history)
    return _build_customer_response(translated_query, customer, self_query)


def answer_question(
    chatbot: Dict[str, object],
    query: str,
    history: List[Dict[str, str]] | None = None,
    preferred_language: str | None = None,
    customers: List[Dict[str, object]] | None = None,
) -> Dict[str, object]:
    conversation_history = history or []
    resolved_language = _resolve_language(query, preferred_language)
    language_code = resolved_language["code"]
    language_name = _normalize_language_name(language_code)
    translated_query = _translate_for_retrieval(query, language_code)

    small_talk_answer = _handle_small_talk(translated_query)
    if small_talk_answer is not None:
        localized_answer = (
            small_talk_answer if language_code == "en" else translate_text(small_talk_answer, dest=language_code, source="en")
        )
        updated_history = conversation_history + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": localized_answer},
        ]
        return {
            "language": language_name,
            "language_code": language_code,
            "translated_query": translated_query,
            "response": localized_answer,
            "response_in_english": small_talk_answer,
            "sources": [],
            "history": updated_history[-MAX_HISTORY_MESSAGES:],
        }

    customer_answer = _handle_customer_lookup(
        query=query,
        translated_query=translated_query,
        history=conversation_history,
        customers=customers or [],
    )
    if customer_answer is not None:
        localized_answer = (
            customer_answer if language_code == "en" else translate_text(customer_answer, dest=language_code, source="en")
        )
        updated_history = conversation_history + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": localized_answer},
        ]
        return {
            "language": language_name,
            "language_code": language_code,
            "translated_query": translated_query,
            "response": localized_answer,
            "response_in_english": customer_answer,
            "sources": [{"source": "mock_customers.json", "page": "N/A", "snippet": "Demo customer record response"}],
            "history": updated_history[-MAX_HISTORY_MESSAGES:],
        }

    retriever = chatbot["retriever"]
    docs = retriever.get_relevant_documents(translated_query)
    context, sources = _format_context(docs)

    prompt = f"""
Conversation history:
{_format_history(conversation_history)}

User question in English:
{translated_query}

Retrieved banking context:
{context}

Write the answer in English first. Mention when the answer is based on the documents.
If context is missing, say you could not find a confirmed answer in the provided documents.
""".strip()

    logger.info("Answering query in language '%s'", language_code)
    response = requests.post(
        f"{OPENROUTER_API_BASE}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": OPENROUTER_HTTP_REFERER,
            "X-Title": OPENROUTER_APP_NAME,
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_MODEL,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": BANKING_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    answer_in_english = payload["choices"][0]["message"]["content"].strip()
    localized_answer = (
        answer_in_english
        if language_code == "en"
        else translate_text(answer_in_english, dest=language_code, source="en")
    )

    updated_history = conversation_history + [
        {"role": "user", "content": query},
        {"role": "assistant", "content": localized_answer},
    ]

    return {
        "language": language_name,
        "language_code": language_code,
        "translated_query": translated_query,
        "response": localized_answer,
        "response_in_english": answer_in_english,
        "sources": sources,
        "history": updated_history[-MAX_HISTORY_MESSAGES:],
    }
