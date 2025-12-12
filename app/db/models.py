"""ORM модели для базы данных."""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.base import BaseModel


class TransactionType(enum.Enum):
    """Тип транзакции."""

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class GroupRole(enum.Enum):
    """Роль участника группы."""

    OWNER = "OWNER"
    MEMBER = "MEMBER"


class User(BaseModel):
    """Модель пользователя."""

    __tablename__ = "users"

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    login = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    owned_groups = relationship("Group", back_populates="owner", foreign_keys="Group.owner_id")
    user_groups = relationship("UserGroup", back_populates="user")

    def __repr__(self):
        """Строковое представление объекта."""
        return f"<User id={self.id} login='{self.login}' name='{self.first_name} {self.last_name}'>"


class Transaction(BaseModel):
    """Модель транзакции."""

    __tablename__ = "transactions"

    name = Column(String(255), nullable=False)
    type = Column(Enum(TransactionType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    category = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    # Relationships
    user = relationship("User", back_populates="transactions")
    group = relationship("Group", back_populates="transactions")

    def __repr__(self):
        """Строковое представление объекта."""
        return f"<Transaction id={self.id} name='{self.name}' type='{self.type}' amount={self.amount}>"


class Group(BaseModel):
    """Модель группы."""

    __tablename__ = "groups"

    name = Column(String(200), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="owned_groups", foreign_keys=[owner_id])
    user_groups = relationship("UserGroup", back_populates="group")
    transactions = relationship("Transaction", back_populates="group")

    def __repr__(self):
        """Строковое представление объекта."""
        return f"<Group id={self.id} name='{self.name}'>"


class UserGroup(BaseModel):
    """Связь пользователей и групп."""

    __tablename__ = "user_groups"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    role = Column(Enum(GroupRole), nullable=False, default=GroupRole.MEMBER)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="user_groups")
    group = relationship("Group", back_populates="user_groups")

    def __repr__(self):
        """Строковое представление объекта."""
        return f"<UserGroup id={self.id} user_id={self.user_id} group_id={self.group_id} role='{self.role}'>"
