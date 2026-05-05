import pytest
from datetime import datetime
from decimal import Decimal
from python_accounting.models import (
    Account,
    Balance,
    Transaction,
    Currency,
    ReportingPeriod,
    Entity,
    LineItem,
    Ledger,
)
from python_accounting.exceptions import (
    InvalidBalanceAccountError,
    InvalidBalanceTransactionError,
    NegativeValueError,
    InvalidBalanceDateError,
)


def test_balance_entity(session, entity, currency):
    """Tests the relationship between a balance and its associated entity"""

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
        amount=100,
        balance_type=Balance.BalanceType.DEBIT,
        account_id=account.id,
        entity_id=entity.id,
    )
    session.add(balance)
    session.commit()

    balance = session.get(Balance, balance.id)
    assert balance.entity.name == "Test Entity"
    assert balance.account.name == "Test Receivable Account"
    assert balance.amount == 100
    assert balance.balance_type == Balance.BalanceType.DEBIT
    assert balance.transaction_type == Transaction.TransactionType.CLIENT_INVOICE
    assert balance.is_posted is True
    assert balance.compound is False
    assert balance.credited is False


def test_balance_credited(session, entity, currency):
    """Tests the credited property of a balance"""

    account = Account(
        name="test payable account",
        account_type=Account.AccountType.PAYABLE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add(account)
    session.flush()

    balance = Balance(
        transaction_date=datetime(datetime.today().year - 1, 3, 10),
        transaction_no="TEST002",
        transaction_type=Transaction.TransactionType.SUPPLIER_BILL,
        amount=200,
        balance_type=Balance.BalanceType.CREDIT,
        account_id=account.id,
        entity_id=entity.id,
    )
    session.add(balance)
    session.commit()

    balance = session.get(Balance, balance.id)
    assert balance.credited is True


def test_balance_repr(session, entity, currency):
    """Tests the string representation of a balance"""

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
        amount=Decimal("150.5000"),
        balance_type=Balance.BalanceType.DEBIT,
        account_id=account.id,
        entity_id=entity.id,
    )
    session.add(balance)
    session.commit()

    balance = session.get(Balance, balance.id)
    repr_str = repr(balance)
    assert "Test Receivable Account" in repr_str
    assert "150.5000" in repr_str


def test_balance_validation_negative_amount(session, entity, currency):
    """Tests that a balance with negative amount raises NegativeValueError"""

    account = Account(
        name="test receivable account",
        account_type=Account.AccountType.RECEIVABLE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add(account)
    session.flush()

    with pytest.raises(NegativeValueError) as e:
        balance = Balance(
            transaction_date=datetime(datetime.today().year - 1, 6, 15),
            transaction_no="TEST001",
            transaction_type=Transaction.TransactionType.CLIENT_INVOICE,
            amount=-100,
            balance_type=Balance.BalanceType.DEBIT,
            account_id=account.id,
            entity_id=entity.id,
        )
        session.add(balance)
        session.commit()
    assert "Balance" in str(e.value)


def test_balance_validation_income_statement_account(session, entity, currency):
    """Tests that an income statement account cannot have a balance"""

    account = Account(
        name="test revenue account",
        account_type=Account.AccountType.OPERATING_REVENUE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add(account)
    session.flush()

    with pytest.raises(InvalidBalanceAccountError):
        balance = Balance(
            transaction_date=datetime(datetime.today().year - 1, 6, 15),
            transaction_no="TEST001",
            transaction_type=Transaction.TransactionType.CLIENT_INVOICE,
            amount=100,
            balance_type=Balance.BalanceType.DEBIT,
            account_id=account.id,
            entity_id=entity.id,
        )
        session.add(balance)
        session.commit()


def test_balance_validation_invalid_transaction_type(session, entity, currency):
    """Tests that invalid transaction types raise InvalidBalanceTransactionError"""

    account = Account(
        name="test receivable account",
        account_type=Account.AccountType.RECEIVABLE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add(account)
    session.flush()

    with pytest.raises(InvalidBalanceTransactionError):
        balance = Balance(
            transaction_date=datetime(datetime.today().year - 1, 6, 15),
            transaction_no="TEST001",
            transaction_type=Transaction.TransactionType.CASH_SALE,
            amount=100,
            balance_type=Balance.BalanceType.DEBIT,
            account_id=account.id,
            entity_id=entity.id,
        )
        session.add(balance)
        session.commit()


def test_balance_validation_invalid_date(session, entity, currency):
    """Tests that a balance date within the current period raises InvalidBalanceDateError"""

    account = Account(
        name="test receivable account",
        account_type=Account.AccountType.RECEIVABLE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add(account)
    session.flush()

    with pytest.raises(InvalidBalanceDateError):
        balance = Balance(
            transaction_date=datetime.now(),
            transaction_no="TEST001",
            transaction_type=Transaction.TransactionType.CLIENT_INVOICE,
            amount=100,
            balance_type=Balance.BalanceType.DEBIT,
            account_id=account.id,
            entity_id=entity.id,
        )
        session.add(balance)
        session.commit()


def test_balance_auto_transaction_no(session, entity, currency):
    """Tests that transaction_no is auto-generated when not provided"""

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
        transaction_type=Transaction.TransactionType.CLIENT_INVOICE,
        amount=100,
        balance_type=Balance.BalanceType.DEBIT,
        account_id=account.id,
        entity_id=entity.id,
    )
    session.add(balance)
    session.commit()

    balance = session.get(Balance, balance.id)
    assert balance.transaction_no is not None
    assert "USD" in balance.transaction_no


def test_balance_opening_trial_balance(session, entity, currency):
    """Tests the opening trial balance calculation"""

    receivable_account = Account(
        name="test receivable account",
        account_type=Account.AccountType.RECEIVABLE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    payable_account = Account(
        name="test payable account",
        account_type=Account.AccountType.PAYABLE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add_all([receivable_account, payable_account])
    session.flush()

    balance1 = Balance(
        transaction_date=datetime(datetime.today().year - 1, 6, 15),
        transaction_no="TEST001",
        transaction_type=Transaction.TransactionType.CLIENT_INVOICE,
        amount=300,
        balance_type=Balance.BalanceType.DEBIT,
        account_id=receivable_account.id,
        entity_id=entity.id,
    )
    balance2 = Balance(
        transaction_date=datetime(datetime.today().year - 1, 3, 10),
        transaction_no="TEST002",
        transaction_type=Transaction.TransactionType.SUPPLIER_BILL,
        amount=200,
        balance_type=Balance.BalanceType.CREDIT,
        account_id=payable_account.id,
        entity_id=entity.id,
    )
    session.add_all([balance1, balance2])
    session.commit()

    trial_balance = Balance.opening_trial_balance(session)
    assert trial_balance["debits"] == 300
    assert trial_balance["credits"] == -200
    assert len(trial_balance["accounts"]) == 2


def test_balance_isolation(session, entity, currency):
    """Tests the isolation of balance objects by entity"""

    account1 = Account(
        name="test account one",
        account_type=Account.AccountType.RECEIVABLE,
        currency_id=currency.id,
        entity_id=entity.id,
    )
    session.add(account1)
    session.flush()

    balance1 = Balance(
        transaction_date=datetime(datetime.today().year - 1, 6, 15),
        transaction_no="TEST001",
        transaction_type=Transaction.TransactionType.CLIENT_INVOICE,
        amount=100,
        balance_type=Balance.BalanceType.DEBIT,
        account_id=account1.id,
        entity_id=entity.id,
    )
    session.add(balance1)
    session.commit()

    trial_balance = Balance.opening_trial_balance(session)
    assert trial_balance["debits"] == 100
    assert len(trial_balance["accounts"]) == 1


def test_balance_recycling(session, entity, currency):
    """Tests the deleting, restoring and destroying functions of the balance model"""

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
        amount=100,
        balance_type=Balance.BalanceType.DEBIT,
        account_id=account.id,
        entity_id=entity.id,
    )
    session.add(balance)
    session.commit()

    balance_id = balance.id

    session.delete(balance)
    balance = session.get(Balance, balance_id)
    assert balance is None

    balance = session.get(Balance, balance_id, include_deleted=True)
    assert balance is not None
    session.restore(balance)

    balance = session.get(Balance, balance_id)
    assert balance is not None

    session.destroy(balance)
    balance = session.get(Balance, balance_id)
    assert balance is None
