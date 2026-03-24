from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import models

def save_in_weights(db: Session, weight_list: list):
    stmt = insert(models.WeightInWord).values(weight_list)
    upsert_stmt = stmt.on_conflict_do_update(
        index_elements= ['word'],
        set_= {'weight': (models.WeightInWord.weight * 4/5) + (stmt.excluded.weight * 1/5)}
    )

    try:
        db.execute(upsert_stmt)
        db.commit()
        print("데이터 저장 중!")
        return 0

    except Exception as e:
        db.rollback()
        print(f"save_in_weights: 오류 발생: {e}")
        return -1