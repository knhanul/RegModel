# 등록 대상 모델 정의
MODELS = [
    {
        "file": "gemma-3-1B-it-Q4_K_M.gguf",
        "ollama_name": "gemma3:1b-q4_k_m",
        "type": "llm",
        "display_name": "Gemma 3 (1B, Q4) - 최경량",
        "description": "매우 가벼운 설치 확인용·저사양 PC용 모델입니다. 속도와 메모리 부담은 낮지만 문서 요약, 긴 문서 분석, 참고문서AI 답변 생성 품질은 4B 이상 모델보다 부족할 수 있습니다."
    },
    {
        "file": "gemma-3-4B-it-Q4_K_M.gguf",
        "ollama_name": "gemma3:4b-q4_k_m",
        "type": "llm",
        "display_name": "Gemma 3 (4B, Q4) - 표준형",
        "description": "안정적인 문서작성과 요약 작업을 위한 Gemma 3 계열 모델입니다. 기본 모델이 기대와 다를 때 대체 기본 모델로 사용할 수 있습니다."
    },
    {
        "file": "gemma-4-E2B-it-Q4_K_M.gguf",
        "ollama_name": "gemma4:e2b-q4_k_m",
        "type": "llm",
        "display_name": "Gemma 4 (E2B, Q4) - 기본형",
        "description": "문서 요약, 문장 다듬기, 일반 질의응답에 사용할 기본 경량 모델입니다. Q4_K_M 양자화 모델로 속도와 용량 부담이 적어 AI마크다운에디터의 기본 문서작성 모델로 추천합니다."
    },
    {
        "file": "gemma-4-E2B-it-Q8_0.gguf",
        "ollama_name": "gemma4:e2b-q8_0",
        "type": "llm",
        "display_name": "Gemma 4 (E2B, Q8) - 경량 정밀형",
        "description": "E2B 계열에서 답변 품질을 조금 더 우선할 때 사용하는 모델입니다. Q4 모델보다 용량과 메모리 부담은 크지만 문장 품질을 더 중요하게 볼 때 선택할 수 있습니다."
    },
    {
        "file": "gemma-4-E4B-it-Q4_K_M.gguf",
        "ollama_name": "gemma4:e4b-q4_k_m",
        "type": "llm",
        "display_name": "Gemma 4 (E4B, Q4) - 고성능 추론형",
        "description": "고성능 추론이 필요한 작업에 적합한 모델입니다. 복잡한 논리 추론, 코드 생성, 고급 문서 분석 등에서 우수한 성능을 발휘합니다."
    },
    {
        "file": "KURE-v1-Q4_K_M.gguf",
        "ollama_name": "kure:v1-q4_k_m",
        "type": "embedding",
        "display_name": "KURE v1 (Q4) - 문서 검색 전용",
        "description": "AI마크다운에디터의 참고문서AI에서 문서 색인과 검색에 사용할 한국어 특화 embedding 모델입니다. 일반 채팅이나 문장 생성용이 아니라 RAG 검색용 모델입니다."
    }
]
