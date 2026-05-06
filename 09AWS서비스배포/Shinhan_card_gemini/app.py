import os
from typing import List, Dict, Tuple

import numpy as np
import pdfplumber
import faiss
import gradio as gr

from sentence_transformers import SentenceTransformer
from google import genai
from dotenv import load_dotenv


# =========================
# 환경 설정
# =========================
load_dotenv(".gemini_env")
load_dotenv()

api_key = (
    os.getenv("google_api_key")
    or os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
)

if not api_key:
    raise EnvironmentError(
        "Gemini API 키가 없습니다. "
        ".gemini_env 또는 환경변수에 google_api_key / GEMINI_API_KEY / GOOGLE_API_KEY 중 하나를 설정하세요."
    )

PDF_DIR = "./"
GENERATION_MODEL = "gemini-2.5-flash"

MAX_CHARS = 500
OVERLAP_CHARS = 150
TOP_K = 8
MAX_CONTEXT_CHARS = 5000


# =========================
# 1) 모델 초기화
# =========================
client = genai.Client(api_key=api_key)

embed_model = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


# =========================
# 2) 텍스트 분할 함수
# =========================
def split_text(text: str, max_chars: int = 500, overlap_chars: int = 150) -> List[str]:
    text = text.strip()
    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_chars
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap_chars

    return chunks


# =========================
# 3) Gemini 응답 텍스트 추출
# =========================
def extract_response_text(resp) -> str:
    if hasattr(resp, "text") and resp.text:
        return resp.text.strip()

    collected = []
    candidates = getattr(resp, "candidates", None)

    if candidates:
        for cand in candidates:
            content = getattr(cand, "content", None)
            if not content:
                continue

            parts = getattr(content, "parts", None)
            if not parts:
                continue

            for part in parts:
                txt = getattr(part, "text", None)
                if txt:
                    collected.append(txt.strip())

    if collected:
        return "\n".join(collected)

    return "죄송해요. 답변을 생성하지 못했어요."


# =========================
# 4) PDF 로딩 및 코퍼스 구축
# =========================
def build_corpus(pdf_dir: str) -> Tuple[List[str], List[Dict]]:
    if not os.path.exists(pdf_dir):
        raise FileNotFoundError(f"PDF 폴더가 없습니다: {pdf_dir}")

    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]

    if not pdf_files:
        raise FileNotFoundError(f"{pdf_dir} 폴더 안에 PDF 파일이 없습니다.")

    texts = []
    metas = []

    print("[RAG] PDF 로딩 시작")

    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        print(f"[RAG] 처리 중: {pdf_file}")

        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if not page_text:
                    continue

                chunks = split_text(
                    page_text,
                    max_chars=MAX_CHARS,
                    overlap_chars=OVERLAP_CHARS,
                )

                for chunk in chunks:
                    texts.append(chunk)
                    metas.append(
                        {
                            "file": pdf_file,
                            "page": page_idx,
                            "preview": chunk[:180].replace("\n", " "),
                        }
                    )

    if not texts:
        raise ValueError("PDF에서 유효한 텍스트를 추출하지 못했습니다.")

    print(f"[RAG] 전체 청크 수: {len(texts)}")
    return texts, metas


# =========================
# 5) 인덱스 구축
# =========================
print("[RAG] 코퍼스 구축 중...")
texts, metas = build_corpus(PDF_DIR)

print("[RAG] 임베딩 생성 중...")
vectors = embed_model.encode(
    texts,
    convert_to_numpy=True,
    show_progress_bar=False
)

dim = vectors.shape[1]
index = faiss.IndexFlatIP(dim)

norms = np.linalg.norm(vectors, axis=1, keepdims=True)
vectors = vectors / (norms + 1e-10)

index.add(vectors.astype("float32"))
print("[RAG] FAISS 인덱스 구축 완료")


# =========================
# 6) 검색 함수
# =========================
def retrieve_context(query: str) -> List[Dict]:
    q_vec = embed_model.encode([query], convert_to_numpy=True, show_progress_bar=False)[0]
    q_vec = q_vec.reshape(1, -1)

    q_norms = np.linalg.norm(q_vec, axis=1, keepdims=True)
    q_vec = q_vec / (q_norms + 1e-10)

    distances, indices = index.search(q_vec.astype("float32"), TOP_K)

    results = []
    current_len = 0

    for rank, idx in enumerate(indices[0]):
        if idx == -1:
            continue

        chunk_text = texts[idx]
        if current_len + len(chunk_text) > MAX_CONTEXT_CHARS:
            break

        results.append(
            {
                "rank": rank + 1,
                "score": float(distances[0][rank]),
                "text": chunk_text,
                "file": metas[idx]["file"],
                "page": metas[idx]["page"],
                "preview": metas[idx]["preview"],
            }
        )
        current_len += len(chunk_text)

    return results


# =========================
# 7) 답변 생성 함수
# =========================
def generate_answer(query: str, history) -> Tuple[str, List[Dict]]:
    retrieved = retrieve_context(query)

    context_block = "\n\n---\n\n".join(
        [
            f"[문서: {item['file']} / 페이지: {item['page']}]\n{item['text']}"
            for item in retrieved
        ]
    )

    history_lines = []
    if history:
        for msg in history[-6:]:
            if isinstance(msg, dict):
                role = msg.get("role", "")
                content = msg.get("content", "")
                if isinstance(content, str) and content.strip():
                    if role == "user":
                        history_lines.append(f"사용자: {content}")
                    else:
                        history_lines.append(f"상담봇: {content}")

    history_block = "\n".join(history_lines)

    system_prompt = (
        "너는 신한카드 '처음' 카드 상품 설명 챗봇이다.\n"
        "반드시 아래 컨텍스트에 있는 정보만 사용해 한국어로 답변해라.\n"
        "규칙:\n"
        "1. 이 챗봇은 신한카드 '처음' 카드 설명 전용이다.\n"
        "2. 컨텍스트에 없는 정보는 추측하지 말 것\n"
        "3. 모르면 '제공된 처음 카드 상품 설명 자료만으로는 확인되지 않습니다.'라고 말할 것\n"
        "4. 연회비, 전월실적, 혜택 한도, 기간, 조건 등 숫자는 컨텍스트의 값만 사용할 것\n"
        "5. 다른 카드와의 비교나 추천은 자료에 근거가 있을 때만 제한적으로 답할 것\n"
        "6. 말투는 친절하고 간결하게, 카드 안내 챗봇처럼 답할 것\n"
        "7. 필요하면 마지막에 핵심을 짧게 정리할 것"
    )

    full_prompt = f"""
{system_prompt}

[이전 대화]
{history_block}

[컨텍스트 시작]
{context_block}
[컨텍스트 끝]

[사용자 질문]
{query}
"""

    resp = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=full_prompt,
    )

    answer_text = extract_response_text(resp)
    return answer_text, retrieved


# =========================
# 8) 참고 문서 출력용
# =========================
def format_sources_markdown(retrieved: List[Dict]) -> str:
    if not retrieved:
        return "참고한 설명서 내용이 없습니다."

    lines = ["### 참고한 처음 카드 설명서 내용"]

    for item in retrieved:
        snippet = item["text"].replace("\n", " ").strip()
        if len(snippet) > 220:
            snippet = snippet[:220] + "..."

        lines.append(
            f"- **{item['file']}** / p.{item['page']} / 유사도 `{item['score']:.4f}`\n"
            f"  - {snippet}"
        )

    return "\n".join(lines)


# =========================
# 9) 채팅 처리 함수
# =========================
def chat(message, history):
    history = history or []

    user_message = (message or "").strip()
    if not user_message:
        return "", history, "질문을 입력해주세요."

    answer, retrieved = generate_answer(user_message, history)

    updated_history = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": answer},
    ]

    sources_md = format_sources_markdown(retrieved)

    return "", updated_history, sources_md


def reset_chat():
    return (
        "",
        [
            {
                "role": "assistant",
                "content": (
                    "안녕하세요. 신한카드 **처음** 카드 안내 챗봇입니다.\n\n"
                    "처음 카드의 연회비, 전월실적, 할인 혜택, 이용 조건을 질문해 주세요.\n"
                    "예) 처음 카드의 전월실적 조건은 뭐야?"
                ),
            }
        ],
        "아직 참고한 문서가 없습니다."
    )


# =========================
# 10) UI 스타일
# =========================
custom_css = """
:root {
  --shinhan-blue: #0046ff;
  --shinhan-deep-blue: #0037cc;
  --shinhan-light: #eef4ff;
  --shinhan-gray: #f7f9fc;
  --shinhan-text: #1f2937;
  --shinhan-border: #dbe4f3;
}

.gradio-container {
  background: linear-gradient(180deg, #f6f9ff 0%, #ffffff 100%);
  font-family: "Pretendard", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
}

#app-shell {
  max-width: 1100px;
  margin: 0 auto;
}

#brand-hero {
  background: linear-gradient(135deg, #0046ff 0%, #2b6dff 100%);
  border-radius: 22px;
  padding: 28px 30px;
  color: white;
  box-shadow: 0 14px 34px rgba(0, 70, 255, 0.18);
  margin-bottom: 14px;
}

#brand-hero h1 {
  margin: 0 0 8px 0;
  font-size: 30px;
  font-weight: 800;
}

#brand-hero p {
  margin: 0;
  opacity: 0.96;
  line-height: 1.6;
  font-size: 15px;
}

#chip-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 14px;
}

.chip {
  display: inline-block;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.22);
  font-size: 12px;
}

#shinhan-chatbot {
  border: 1px solid var(--shinhan-border);
  border-radius: 22px;
  background: white;
  box-shadow: 0 10px 30px rgba(30, 64, 175, 0.08);
}

#shinhan-chatbot .message-wrap {
  padding-top: 6px;
  padding-bottom: 6px;
}

#shinhan-chatbot .message.user .bubble {
  background: linear-gradient(135deg, #0046ff 0%, #2b6dff 100%) !important;
  color: white !important;
  border-radius: 20px 20px 6px 20px !important;
  box-shadow: 0 8px 18px rgba(0, 70, 255, 0.18);
}

#shinhan-chatbot .message.bot .bubble,
#shinhan-chatbot .message.assistant .bubble {
  background: #f5f8ff !important;
  color: #1f2937 !important;
  border: 1px solid #dbe4f3 !important;
  border-radius: 20px 20px 20px 6px !important;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
}

#input-row {
  gap: 10px;
}

#user-input textarea {
  border-radius: 16px !important;
  border: 1px solid #cdd9ee !important;
}

#send-btn {
  background: linear-gradient(135deg, #0046ff 0%, #2b6dff 100%) !important;
  border: none !important;
  color: white !important;
  border-radius: 14px !important;
  font-weight: 700 !important;
}

#clear-btn {
  border-radius: 14px !important;
}

#source-box {
  border: 1px solid var(--shinhan-border);
  border-radius: 18px;
  background: #ffffff;
}
"""


# =========================
# 11) Gradio UI
# =========================
theme = gr.themes.Soft(
    primary_hue="blue",
    secondary_hue="sky",
    neutral_hue="slate",
)

with gr.Blocks(
    theme=theme,
    css=custom_css,
    title="신한카드 처음 카드 안내 챗봇"
) as demo:

    with gr.Column(elem_id="app-shell"):
        gr.HTML("""
        <div id="brand-hero">
            <h1>신한카드 처음 카드 안내 챗봇</h1>
            <p>
                신한카드 <b>'처음'</b> 상품설명서를 바탕으로 연회비, 혜택, 전월실적, 이용조건을 안내합니다.<br>
                자료에 없는 내용은 추측하지 않고, 처음 카드 설명서 기준으로만 답변합니다.
            </p>
            <div id="chip-row">
                <span class="chip">처음 카드 전용</span>
                <span class="chip">상품설명서 기반</span>
                <span class="chip">추측 없는 답변</span>
            </div>
        </div>
        """)

        chatbot = gr.Chatbot(
            value=[
                {
                    "role": "assistant",
                    "content": (
                        "안녕하세요. 신한카드 **처음** 카드 안내 챗봇입니다.\n\n"
                        "처음 카드의 연회비, 전월실적, 할인 혜택, 이용 조건을 질문해 주세요.\n"
                        "예) 처음 카드의 전월실적 조건은 뭐야?"
                    ),
                }
            ],
            height=620,
            elem_id="shinhan-chatbot",
        )

        with gr.Row(elem_id="input-row"):
            msg = gr.Textbox(
                placeholder="처음 카드의 연회비, 혜택, 전월실적, 이용조건 등을 질문해보세요",
                lines=2,
                scale=8,
                elem_id="user-input",
                container=False,
            )
            send_btn = gr.Button(
                "보내기",
                scale=1,
                elem_id="send-btn",
                variant="primary"
            )
            clear_btn = gr.Button(
                "초기화",
                scale=1,
                elem_id="clear-btn"
            )

        with gr.Accordion("참고한 설명서 보기", open=False):
            source_md = gr.Markdown(
                value="아직 참고한 문서가 없습니다.",
                elem_id="source-box"
            )

        gr.Examples(
            examples=[
                ["처음 카드의 연회비는 얼마야?"],
                ["전월실적 조건이 어떻게 돼?"],
                ["어떤 할인 혜택이 있어?"],
                ["혜택 적용 한도나 제외 조건도 알려줘"],
            ],
            inputs=msg,
        )

        send_btn.click(
            fn=chat,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot, source_md],
        )

        msg.submit(
            fn=chat,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot, source_md],
        )

        clear_btn.click(
            fn=reset_chat,
            inputs=None,
            outputs=[msg, chatbot, source_md],
        )


# =========================
# 12) 실행
# =========================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7861))
    demo.queue()
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False
    )