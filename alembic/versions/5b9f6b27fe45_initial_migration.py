"""Initial migration

Revision ID: 5b9f6b27fe45
Revises: 
Create Date: 2025-12-10 17:30:20.597128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5b9f6b27fe45'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создание enum типов
    connection = op.get_bind()
    
    # Проверяем и создаем типы только если их нет
    transaction_type_exists = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'transactiontype'")
    ).fetchone()
    if not transaction_type_exists:
        connection.execute(sa.text("CREATE TYPE transactiontype AS ENUM ('INCOME', 'EXPENSE')"))
    
    group_role_exists = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'grouprole'")
    ).fetchone()
    if not group_role_exists:
        connection.execute(sa.text("CREATE TYPE grouprole AS ENUM ('OWNER', 'MEMBER')"))
    
    # Создаем объекты ENUM для использования в таблицах
    transaction_type_enum = postgresql.ENUM('INCOME', 'EXPENSE', name='transactiontype', create_type=False)
    group_role_enum = postgresql.ENUM('OWNER', 'MEMBER', name='grouprole', create_type=False)
    
    # Создание таблицы users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=False),
        sa.Column('last_name', sa.String(length=100), nullable=False),
        sa.Column('login', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_login'), 'users', ['login'], unique=True)
    
    # Создание таблицы groups
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_groups_id'), 'groups', ['id'], unique=False)
    
    # Создание таблицы transactions
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', transaction_type_enum, nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)
    
    # Создание таблицы user_groups
    op.create_table(
        'user_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('role', group_role_enum, nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_groups_id'), 'user_groups', ['id'], unique=False)


def downgrade() -> None:
    # Удаление таблиц в обратном порядке
    op.drop_index(op.f('ix_user_groups_id'), table_name='user_groups')
    op.drop_table('user_groups')
    
    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_table('transactions')
    
    op.drop_index(op.f('ix_groups_id'), table_name='groups')
    op.drop_table('groups')
    
    op.drop_index(op.f('ix_users_login'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    
    # Удаление enum типов
    connection = op.get_bind()
    
    # Удаляем типы только если они существуют
    transaction_type_exists = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'transactiontype'")
    ).fetchone()
    if transaction_type_exists:
        connection.execute(sa.text("DROP TYPE IF EXISTS transactiontype CASCADE"))
    
    group_role_exists = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'grouprole'")
    ).fetchone()
    if group_role_exists:
        connection.execute(sa.text("DROP TYPE IF EXISTS grouprole CASCADE"))

