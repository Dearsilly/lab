import torch
from transformers import AutoTokenizer

from src.model import BertForEssayScoring
from src.preprocess import clean_text
from src.dataset import SCORE_RANGES, denormalize_score

MODEL_NAME = "bert-base-uncased"
MODEL_PATH = "models/best_model.pt"
TOKENIZER_PATH = "models/tokenizer"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model():
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_PATH)

    model = BertForEssayScoring(MODEL_NAME).to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    return tokenizer, model


TOKENIZER, MODEL = load_model()


def clip_score(essay_set: int, score: float) -> float:
    min_s, max_s = SCORE_RANGES[essay_set]
    return max(min(score, max_s), min_s)


def predict_score(essay_set: int, essay: str):
    if essay_set not in SCORE_RANGES:
        raise ValueError(f"essay_set must be in 1~8, got {essay_set}")

    essay = clean_text(essay)
    if not essay:
        raise ValueError("essay text is empty after cleaning")

    text = f"[SET_{essay_set}] {essay}"

    encoding = TOKENIZER(
        text,
        truncation=True,
        padding="max_length",
        max_length=512,
        return_tensors="pt"
    )

    input_ids = encoding["input_ids"].to(DEVICE)
    attention_mask = encoding["attention_mask"].to(DEVICE)

    token_type_ids = encoding.get("token_type_ids")
    if token_type_ids is not None:
        token_type_ids = token_type_ids.to(DEVICE)

    with torch.no_grad():
        output = MODEL(input_ids, attention_mask, token_type_ids)
        raw_norm_score = output.item()

    # 先从归一化分数还原
    raw_score = denormalize_score(essay_set, raw_norm_score)

    # 再裁剪到合法范围
    clipped_score = clip_score(essay_set, raw_score)
    rounded_score = round(clipped_score)

    return {
        "essay_set": essay_set,
        "raw_norm_score": raw_norm_score,
        "raw_score": raw_score,
        "clipped_score": clipped_score,
        "rounded_score": rounded_score,
    }


if __name__ == "__main__":
    essay_set = 1
    essay = (
        "Dear local newspaper I raed ur argument on the computers and I think they are a positive effect on people. The first reson I think they are a good effect is because you can do so much with them like if you live in mane and ur cuzin lives in califan you and him could have a wed chat. The second thing you could do is look up news any were in the world you could be stuck on a plane and it would be vary boring when you can take but ur computer and go on ur computer at work and start doing work. When you said it takes away from exirsis well some people use the computer for that too to chart how fast they run or how meny miles they want and sometimes what they eat. The thrid reson is some peolpe jobs are on the computers or making computers for exmple when you made this artical you didnt use a type writer you used a computer and printed it out if we didnt have computers it would make ur @CAPS1 a lot harder. Thank you for reading and whe you are thinking adout it agen pleas consiter my thrie resons."
    )

    result = predict_score(essay_set, essay)

    print(f"Essay set: {result['essay_set']}")
    print(f"Raw normalized score: {result['raw_norm_score']:.4f}")
    print(f"Raw score: {result['raw_score']:.2f}")
    print(f"Clipped score: {result['clipped_score']:.2f}")
    print(f"Rounded score: {result['rounded_score']}")