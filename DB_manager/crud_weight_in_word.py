from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
import DB_manager.models as models

def save_in_weights(db: Session, weight_list: list):
    if not weight_list:
        return 0

    normalized_weight_list = []
    for item in weight_list:
        if "word" not in item or "weight" not in item:
            continue
        normalized_weight_list.append(
            {"word": item["word"], "weight": float(item["weight"])}
        )

    if not normalized_weight_list:
        print("save_in_weights: 저장 가능한 weight 데이터가 없습니다.")
        return -1

    stmt = insert(models.WeightInWord).values(normalized_weight_list)
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