import pytest
from datetime import datetime
from python_accounting.models import (
    Account,
    Transaction,
    Balance,
    LineItem,
    Category,
)
from python_accounting.transactions import CashSale, ClientInvoice
from python_accounting.exceptions import (
    InvalidAccountTypeError,
    InvalidCategoryAccountTypeError,
    HangingTransactionsError,
)


def test_account_validate_category_mismatch(session, entity, currency):
    """Tests that an account with a mismatched category type raises InvalidCategoryAccountTypeError"""

    category = Category(
        name="Revenue Category",
        category_account_type=Account.AccountType.OPERATING_REVENUE,
        entity_id=entity.id,
    )
    session.add(category)
    session.flush()

    with pytest.raises(InvalidCategoryAccountTypeError) as e:
        account = Account(
            name="test bank account",
            account_type=Account.AccountType.BANK,
            currency_id=currency.id,
            category_id=category.id,
            entity_id=entity.id,
        )
        session.add(account)
        session.commit()
    assert "Bank" in str(e.value)
    assert "Operating Revenue" in str(e.value)


def test_account_validate_delete_with_transactions(session, entity, currency):
    """Tests that deleting an account with posted transactions raises HangingTransactionsError"""

    account1 = Account(
        name="test bank account",
        account_type=Account.AccountType.BANK,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    account2 = Account(
        name="test revenue account",
        account_type=Account.AccountType.OPERATING_REVENUE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add_all([account1, account2])
    session.flush()

    transaction = CashSale(
        narration="Test transaction",
        transaction_date=datetime.now(),
        account_id=account1.id,
        entity_id=entity.id,
    )
    session.add(transaction)
    session.flush()

    line_item = LineItem(
        narration="Test line item",
        account_id=account2.id,
        amount=100,
        entity_id=entity.id,
    )
    session.add(line_item)
    session.flush()

    transaction.line_items.add(line_item)
    session.add(transaction)
    session.flush()

    transaction.post(session)

    with pytest.raises(HangingTransactionsError) as e:
        session.delete(account1)
    assert "Account" in str(e.value)


def test_account_opening_balance(session, entity, currency):
    """Tests the opening balance calculation for an account"""

    account = Account(
        name="test receivable account",
        account_type=Account.AccountType.RECEIVABLE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add(account)
    session.flush()

    balance = Balance(
        transaction_date=datetime(datetime.today().year - 1, 6, 15),
        transaction_no="TEST001",
        transaction_type=Transaction.TransactionType.CLIENT_INVOICE,
        amount=500,
        balance_type=Balance.BalanceType.DEBIT,
        account_id=account.id,
        entity_id=entity.id,
    )
    session.add(balance)
    session.commit()

    opening = account.opening_balance(session)
    assert opening == 500


def test_account_closing_balance(session, entity, currency):
    """Tests the closing balance calculation for an account"""

    account1 = Account(
        name="test bank account",
        account_type=Account.AccountType.BANK,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    account2 = Account(
        name="test revenue account",
        account_type=Account.AccountType.OPERATING_REVENUE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add_all([account1, account2])
    session.flush()

    transaction = CashSale(
        narration="Test transaction",
        transaction_date=datetime.now(),
        account_id=account1.id,
        entity_id=entity.id,
    )
    session.add(transaction)
    session.flush()

    line_item = LineItem(
        narration="Test line item",
        account_id=account2.id,
        amount=100,
        entity_id=entity.id,
    )
    session.add(line_item)
    session.flush()

    transaction.line_items.add(line_item)
    session.add(transaction)
    session.flush()

    transaction.post(session)

    closing = account1.closing_balance(session)
    assert closing == 100


def test_account_statement(session, entity, currency):
    """Tests the account statement generation"""

    account1 = Account(
        name="test bank account",
        account_type=Account.AccountType.BANK,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    account2 = Account(
        name="test revenue account",
        account_type=Account.AccountType.OPERATING_REVENUE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add_all([account1, account2])
    session.flush()

    transaction = CashSale(
        narration="Test cash sale",
        transaction_date=datetime.now(),
        account_id=account1.id,
        entity_id=entity.id,
    )
    session.add(transaction)
    session.flush()

    line_item = LineItem(
        narration="Test line item",
        account_id=account2.id,
        amount=250,
        entity_id=entity.id,
    )
    session.add(line_item)
    session.flush()

    transaction.line_items.add(line_item)
    session.add(transaction)
    session.flush()

    transaction.post(session)

    statement = account1.statement(session)
    assert "opening_balance" in statement
    assert "transactions" in statement
    assert "closing_balance" in statement
    assert len(statement["transactions"]) == 1
    assert statement["closing_balance"] == 250


def test_account_schedule(session, entity, currency):
    """Tests the account schedule generation for receivable accounts"""

    receivable_account = Account(
        name="test receivable account",
        account_type=Account.AccountType.RECEIVABLE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    revenue_account = Account(
        name="test revenue account",
        account_type=Account.AccountType.OPERATING_REVENUE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add_all([receivable_account, revenue_account])
    session.flush()

    transaction = ClientInvoice(
        narration="Test invoice",
        transaction_date=datetime.now(),
        account_id=receivable_account.id,
        entity_id=entity.id,
    )
    session.add(transaction)
    session.flush()

    line_item = LineItem(
        narration="Test line item",
        account_id=revenue_account.id,
        amount=300,
        entity_id=entity.id,
    )
    session.add(line_item)
    session.flush()

    transaction.line_items.add(line_item)
    session.add(transaction)
    session.flush()

    transaction.post(session)

    schedule = receivable_account.statement(session, schedule=True)
    assert "total_amount" in schedule
    assert "cleared_amount" in schedule
    assert "uncleared_amount" in schedule
    assert schedule["total_amount"] == 300
    assert schedule["uncleared_amount"] == 300


def test_account_schedule_invalid_type(session, entity, currency):
    """Tests that scheduling a non-receivable/payable account raises InvalidAccountTypeError"""

    bank_account = Account(
        name="test bank account",
        account_type=Account.AccountType.BANK,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add(bank_account)
    session.flush()

    with pytest.raises(InvalidAccountTypeError) as e:
        bank_account.statement(session, schedule=True)
    assert "Receivable" in str(e.value) or "Payable" in str(e.value)


def test_account_section_balances(session, entity, currency):
    """Tests the section balances calculation"""

    account1 = Account(
        name="test bank account",
        account_type=Account.AccountType.BANK,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    account2 = Account(
        name="test revenue account",
        account_type=Account.AccountType.OPERATING_REVENUE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add_all([account1, account2])
    session.flush()

    transaction = CashSale(
        narration="Test transaction",
        transaction_date=datetime.now(),
        account_id=account1.id,
        entity_id=entity.id,
    )
    session.add(transaction)
    session.flush()

    line_item = LineItem(
        narration="Test line item",
        account_id=account2.id,
        amount=100,
        entity_id=entity.id,
    )
    session.add(line_item)
    session.flush()

    transaction.line_items.add(line_item)
    session.add(transaction)
    session.flush()

    transaction.post(session)

    balances = Account.section_balances(
        session,
        [Account.AccountType.BANK],
    )
    assert "opening" in balances
    assert "movement" in balances
    assert "closing" in balances
    assert "categories" in balances
    assert balances["closing"] == 100


def test_account_section_balances_with_category(session, entity, currency):
    """Tests section balances calculation with categorized accounts"""

    category = Category(
        name="Bank Accounts",
        category_account_type=Account.AccountType.BANK,
        entity_id=entity.id,
    )
    session.add(category)
    session.flush()

    account1 = Account(
        name="test bank account",
        account_type=Account.AccountType.BANK,
        currency_id=currency.id,
        category_id=category.id,
        entity_id=entity.id,
    )
    account2 = Account(
        name="test revenue account",
        account_type=Account.AccountType.OPERATING_REVENUE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add_all([account1, account2])
    session.flush()

    transaction = CashSale(
        narration="Test transaction",
        transaction_date=datetime.now(),
        account_id=account1.id,
        entity_id=entity.id,
    )
    session.add(transaction)
    session.flush()

    line_item = LineItem(
        narration="Test line item",
        account_id=account2.id,
        amount=200,
        entity_id=entity.id,
    )
    session.add(line_item)
    session.flush()

    transaction.line_items.add(line_item)
    session.add(transaction)
    session.flush()

    transaction.post(session)

    balances = Account.section_balances(
        session,
        [Account.AccountType.BANK],
    )
    assert "Bank Accounts" in balances["categories"]
    assert balances["categories"]["Bank Accounts"]["total"] == 200
    assert len(balances["categories"]["Bank Accounts"]["accounts"]) == 1
