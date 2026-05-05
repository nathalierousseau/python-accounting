from sqlalchemy import select
from python_accounting.models import Entity
from python_accounting.models.user import User


def test_user_entity(session, entity):
    """Tests the relationship between a user and its associated entity"""

    user = User(name="Test User", email="test@example.com", entity_id=entity.id)
    session.add(user)
    session.commit()

    user = session.get(User, user.id)
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.entity.name == "Test Entity"


def test_user_repr(session, entity):
    """Tests the string representation of a user"""

    user = User(name="John Doe", email="john@example.com", entity_id=entity.id)
    session.add(user)
    session.commit()

    user = session.get(User, user.id)
    assert repr(user) == "John Doe <john@example.com>"


def test_user_isolation(session, entity):
    """Tests the isolation of user objects by entity"""

    entity2 = Entity(name="Test Entity Two")
    session.add(entity2)
    session.flush()
    entity2 = session.get(Entity, entity2.id)

    user1 = User(name="User One", email="one@example.com", entity_id=entity.id)
    user2 = User(name="User Two", email="two@example.com", entity_id=entity2.id)
    session.add_all([user1, user2])
    session.commit()

    users = session.scalars(select(User)).all()
    assert len(users) == 1
    assert users[0].name == "User One"

    session.entity = entity2
    users = session.scalars(select(User)).all()
    assert len(users) == 1
    assert users[0].name == "User Two"


def test_user_entity_relationship(session, entity):
    """Tests that users appear in the entity's users list"""

    user1 = User(name="User A", email="a@example.com", entity_id=entity.id)
    user2 = User(name="User B", email="b@example.com", entity_id=entity.id)
    session.add_all([user1, user2])
    session.commit()

    entity = session.get(Entity, entity.id)
    assert len(entity.users) == 2
    user_names = [u.name for u in entity.users]
    assert "User A" in user_names
    assert "User B" in user_names
