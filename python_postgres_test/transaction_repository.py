# transaction_repository.py
from sqlalchemy.orm import Session
from transaction import Transaction  # импорт вашей сущности Transaction

class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, transaction: Transaction):
        # Проверяем, существует ли транзакция с таким уникальным ключом (например, по id или комбинации полей)
        existing_tx = self.db.query(Transaction).filter(
            Transaction.user_id == transaction.user_id,
            Transaction.amount == transaction.amount,
            Transaction.date == transaction.date
        ).first()
        if existing_tx:
            print(f"Транзакция уже существует. ID: {existing_tx.id}")
            return existing_tx

        # Если нет — создаём новую транзакцию
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_by_id(self, tx_id: int):
        return self.db.query(Transaction).filter(Transaction.id == tx_id).first()

    def get_all_by_user(self, user_id: int):
        return self.db.query(Transaction).filter(Transaction.user_id == user_id).all()
