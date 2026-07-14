# 포시드 AI 모델 관리자

로컬 AI 모델 등록·삭제 및 Ollama 실행 환경 관리 프로그램입니다.

영문명: POSID AI Model Manager

## 프로그램 목적

이 프로그램은 회사 업무용 AI 비서 및 문서 업무 도구에서 사용할 로컬 GGUF 모델을 Ollama에 등록하고 삭제합니다. 등록 가능한 모델과 현재 Ollama 모델을 확인하고, 검색·상세정보·작업 내역을 통해 모델 관리 상태를 확인할 수 있습니다.

## 폴더 구조

```
프로젝트루트/
├─ simple_ollama_model_register.py
├─ README_SIMPLE.md
├─ models/
│   ├─ embedding/
│   │   └─ KURE-v1-Q4_K_M.gguf
│   │
│   ├─ gemma-3-1B-it-Q4_K_M.gguf
│   ├─ gemma-3-4B-it-Q4_K_M.gguf
│   ├─ gemma-4-E2B-it-Q4_K_M.gguf
│   ├─ gemma-4-E2B-it-Q8_0.gguf
│   └─ gemma-4-E4B-it-Q4_K_M.gguf
│
└─ generated/
    ├─ modelfiles/
    └─ installed_models.json
```

## 실행 방법

프로젝트 루트에서 다음 명령으로 실행합니다.

```powershell
python ai_model_manager.py
```

실행파일을 사용하는 경우 `ai_model_manager.exe`를 프로젝트 루트에서 실행합니다. `models` 폴더의 GGUF 파일은 프로그램 시작 또는 새로고침 시 등록 가능한 모델로 검색됩니다.

## 모델 파일 위치

모델 GGUF 파일은 `models/` 폴더 또는 `models/embedding/` 폴더에 위치해야 합니다.

- LLM 모델: `models/` 폴더
- Embedding 모델: `models/embedding/` 폴더

## 지원 모델 목록

### LLM 모델

1. **Gemma 3 (1B, Q4) - 최경량**
   - 파일: `models/gemma-3-1B-it-Q4_K_M.gguf`
   - Ollama 등록명: `gemma3:1b-q4_k_m`
   - 설명: 매우 가벼운 설치 확인용·저사양 PC용 모델입니다.

2. **Gemma 3 (4B, Q4) - 표준형**
   - 파일: `models/gemma-3-4B-it-Q4_K_M.gguf`
   - Ollama 등록명: `gemma3:4b-q4_k_m`
   - 설명: 안정적인 문서작성과 요약 작업을 위한 Gemma 3 계열 모델입니다.

3. **Gemma 4 (E2B, Q4) - 기본형**
   - 파일: `models/gemma-4-E2B-it-Q4_K_M.gguf`
   - Ollama 등록명: `gemma4:e2b-q4_k_m`
   - 설명: 문서 요약, 문장 다듬기, 일반 질의응답에 사용할 기본 경량 모델입니다.

4. **Gemma 4 (E2B, Q8) - 경량 정밀형**
   - 파일: `models/gemma-4-E2B-it-Q8_0.gguf`
   - Ollama 등록명: `gemma4:e2b-q8_0`
   - 설명: E2B 계열에서 답변 품질을 조금 더 우선할 때 사용하는 모델입니다.

5. **Gemma 4 (E4B, Q4) - 고성능 추론형**
   - 파일: `models/gemma-4-E4B-it-Q4_K_M.gguf`
   - Ollama 등록명: `gemma4:e4b-q4_k_m`
   - 설명: 고성능 추론이 필요한 작업에 적합한 모델입니다.

### Embedding 모델

1. **KURE v1 (Q4) - 문서 검색 전용**
   - 파일: `models/embedding/KURE-v1-Q4_K_M.gguf`
   - Ollama 등록명: `kure:v1-q4_k_m`
   - 설명: AI마크다운에디터의 참고문서AI에서 문서 색인과 검색에 사용할 한국어 특화 embedding 모델입니다.

## 실행 방법

### Python 스크립트로 실행

```bash
python simple_ollama_model_register.py
```

### PyInstaller로 exe로 변환

```bash
pyinstaller --onefile --windowed --name SimpleOllamaModelRegister simple_ollama_model_register.py
```

생성된 exe 파일은 `dist/SimpleOllamaModelRegister.exe`에 위치합니다.

## 모델 등록 방법

1. 프로그램을 실행합니다.
2. 왼쪽 "등록 가능한 모델" 목록에서 등록할 모델을 선택합니다 (다중 선택 가능).
3. [선택 모델 등록] 버튼을 누릅니다.
4. 등록이 완료되면 왼쪽 목록에서 해당 모델이 사라지고 오른쪽 "현재 등록된 Ollama 모델" 목록에 나타납니다.

## 등록된 모델 삭제 방법

1. 오른쪽 "현재 등록된 Ollama 모델" 목록에서 삭제할 모델을 선택합니다 (단일 선택).
2. [선택 등록 모델 삭제] 버튼을 누릅니다.
3. 확인창에서 "예"를 선택하면 모델이 삭제됩니다.
4. 삭제된 모델이 이 프로그램에서 관리하는 모델이면 왼쪽 등록 가능 목록에 다시 표시됩니다.

## 중복 등록 방지

이미 Ollama에 등록된 모델은 왼쪽 "등록 가능한 모델" 목록에 표시되지 않습니다. 따라서 같은 모델을 실수로 중복 등록할 수 없습니다.

## Ollama 설치 요구사항

이 프로그램을 사용하려면 Ollama가 설치되어 있어야 하며, PATH에 포함되어 있어야 합니다.

Ollama 설치: https://ollama.com/

Ollama가 설치되어 있지 않으면:
- 상태 문구에 "Ollama가 설치되어 있지 않거나 PATH에 없습니다."라고 표시됩니다.
- 등록/삭제 버튼이 비활성화됩니다.

## installed_models.json 설명

프로그램은 모델 등록/삭제 후 `generated/installed_models.json` 파일을 생성하거나 갱신합니다.

이 JSON 파일은 다음 정보를 포함합니다:

- `ollama_base_url`: Ollama API 기본 URL
- `models`: 현재 등록된 이 프로그램 관리 모델 목록
- `recommended`: 추천 모델 설정
  - `chat_model`: 기본 채팅 모델
  - `fallback_chat_model`: 대체 채팅 모델
  - `lite_chat_model`: 라이트 채팅 모델
  - `embedding_model`: 임베딩 모델

## AI마크다운에디터 연동

AI마크다운에디터는 `generated/installed_models.json` 파일을 읽어 모델 설정에 활용할 수 있습니다.

이 파일을 통해:
- 현재 설치된 모델 목록 확인
- 추천 모델 설정 로드
- 모델 타입별 분류 (LLM, Embedding)

## 화면 구성

### 상단 안내 영역
- 프로그램 제목
- 사용 안내 문구
- Ollama 상태 표시

### 왼쪽 목록: 등록 가능한 모델
- 아직 Ollama에 등록되지 않은 모델 표시
- 다중 선택 가능
- 표시 이름으로 표시

### 오른쪽 목록: 현재 등록된 Ollama 모델
- `ollama list` 결과 표시
- 단일 선택만 허용
- 이 프로그램에서 관리하는 모델만 표시

### 하단 설명 영역
- 선택한 모델의 설명 표시
- 읽기 전용 텍스트 영역

### 버튼
- **새로고침**: 목록 새로고침
- **선택 모델 등록**: 선택한 모델 등록
- **선택 등록 모델 삭제**: 선택한 등록 모델 삭제
- **닫기**: 프로그램 종료

## 기술 사양

- Python 표준 라이브러리만 사용
- tkinter 기본 위젯만 사용 (ttk 미사용)
- 외부 pip 패키지 불필요
- 절대경로 하드코딩 없음
- 실행 위치를 프로젝트 루트로 인식

## 실행 파일 생성 (PyInstaller)

PyInstaller를 사용하여 단일 실행 파일로 변환할 수 있습니다.

### PyInstaller 설치
```bash
pip install pyinstaller
```

### 실행 파일 생성 명령어

**콘솔 창 있는 버전 (디버깅용):**
```bash
pyinstaller --onefile simple_ollama_model_register.py
```

**콘솔 창 없는 버전 (일반 사용용):**
```bash
pyinstaller --onefile --windowed simple_ollama_model_register.py
```

**아이콘 지정 (아이콘 파일이 있는 경우):**
```bash
pyinstaller --onefile --windowed --icon=icon.ico simple_ollama_model_register.py
```

생성된 실행 파일은 `dist/` 폴더에 `simple_ollama_model_register.exe`로 생성됩니다.

## 주의사항

- 이 프로그램은 1회성 모델 등록용으로 설계되었습니다.
- 복잡한 설정이나 고급 기능은 포함되어 있지 않습니다.
- 메뉴바, 탭, 로그 폴더 열기, JSON 열기 기능은 없습니다.
