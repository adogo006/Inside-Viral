from konlpy.tag import Okt

okt = Okt()
text = "방에서 Don't look back in anger나 실컷 들으면서 쉬고싶다! ㅋㅋ"

# 1. 형태소 추출
print(f"--- 형태소 추출 ---\n{okt.morphs(text)}")

# 2. 명사만 추출
print(f"\n--- 명사 추출 ---\n{okt.nouns(text)}")

# 3. 품사 태깅
print(f"\n--- 품사 태깅 ---\n{okt.pos(text)}")