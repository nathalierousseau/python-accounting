import pytest
from datetime import datetime
from python_accounting.models import (
    Account,
    LineItem,
    Category,
)
from python_accounting.transactions import CashSale
from python_accounting.exceptions import (
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
