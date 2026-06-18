#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
간단 Ollama 모델 등록기
Windows GUI 프로그램 - Python 표준 라이브러리만 사용
"""

import os
import sys
import json
import subprocess
import re
import shutil
from pathlib import Path

import tkinter as tk
from tkinter import messagebox


# 등록 대상 모델 정의
MODELS = [
    {
        "file": "models/gemma-3-1B-it-Q4_K_M.gguf",
        "ollama_name": "gemma3:1b-q4_k_m",
        "type": "llm",
        "display_name": "Gemma 3 (1B, Q4) - 최경량",
        "description": "매우 가벼운 설치 확인용·저사양 PC용 모델입니다. 속도와 메모리 부담은 낮지만 문서 요약, 긴 문서 분석, 참고문서AI 답변 생성 품질은 4B 이상 모델보다 부족할 수 있습니다."
    },
    {
        "file": "models/gemma-3-4B-it-Q4_K_M.gguf",
        "ollama_name": "gemma3:4b-q4_k_m",
        "type": "llm",
        "display_name": "Gemma 3 (4B, Q4) - 표준형",
        "description": "안정적인 문서작성과 요약 작업을 위한 Gemma 3 계열 모델입니다. 기본 모델이 기대와 다를 때 대체 기본 모델로 사용할 수 있습니다."
    },
    {
        "file": "models/gemma-4-E2B-it-Q4_K_M.gguf",
        "ollama_name": "gemma4:e2b-q4_k_m",
        "type": "llm",
        "display_name": "Gemma 4 (E2B, Q4) - 기본형",
        "description": "문서 요약, 문장 다듬기, 일반 질의응답에 사용할 기본 경량 모델입니다. Q4_K_M 양자화 모델로 속도와 용량 부담이 적어 AI마크다운에디터의 기본 문서작성 모델로 추천합니다."
    },
    {
        "file": "models/gemma-4-E2B-it-Q8_0.gguf",
        "ollama_name": "gemma4:e2b-q8_0",
        "type": "llm",
        "display_name": "Gemma 4 (E2B, Q8) - 경량 정밀형",
        "description": "E2B 계열에서 답변 품질을 조금 더 우선할 때 사용하는 모델입니다. Q4 모델보다 용량과 메모리 부담은 크지만 문장 품질을 더 중요하게 볼 때 선택할 수 있습니다."
    },
    {
        "file": "models/gemma-4-E4B-it-Q4_K_M.gguf",
        "ollama_name": "gemma4:e4b-q4_k_m",
        "type": "llm",
        "display_name": "Gemma 4 (E4B, Q4) - 고성능 추론형",
        "description": "고성능 추론이 필요한 작업에 적합한 모델입니다. 복잡한 논리 추론, 코드 생성, 고급 문서 분석 등에서 우수한 성능을 발휘합니다."
    },
    {
        "file": "models/embedding/KURE-v1-Q4_K_M.gguf",
        "ollama_name": "kure:v1-q4_k_m",
        "type": "embedding",
        "display_name": "KURE v1 (Q4) - 문서 검색 전용",
        "description": "AI마크다운에디터의 참고문서AI에서 문서 색인과 검색에 사용할 한국어 특화 embedding 모델입니다. 일반 채팅이나 문장 생성용이 아니라 RAG 검색용 모델입니다."
    }
]


class SimpleOllamaModelRegister:
    """간단 Ollama 모델 등록기 메인 클래스"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("간단 Ollama 모델 등록기")
        self.root.geometry("900x750")
        
        # 프로젝트 루트 경로 결정
        if getattr(sys, 'frozen', False):
            self.root_dir = Path(sys.executable).parent
        else:
            self.root_dir = Path(__file__).parent.resolve()
        
        # 폴더 경로
        self.models_dir = self.root_dir / "models"
        self.embedding_dir = self.root_dir / "models" / "embedding"
        self.generated_dir = self.root_dir / "generated"
        self.modelfiles_dir = self.generated_dir / "modelfiles"
        self.installed_models_file = self.generated_dir / "installed_models.json"
        
        # 폴더 생성
        self._ensure_directories()
        
        # 상태 변수
        self.ollama_available = False
        self.registered_models = []
        self.available_models = []
        
        # GUI 생성
        self._create_gui()
        
        # 초기화 (예외 처리 추가)
        try:
            self._check_ollama()
            self._refresh_lists()
        except Exception as e:
            messagebox.showerror("초기화 오류", f"프로그램 초기화 중 오류가 발생했습니다:\n{e}")
    
    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self.modelfiles_dir.mkdir(parents=True, exist_ok=True)
    
    def _scan_gguf_files(self):
        """models 폴더에서 gguf 파일 스캔"""
        gguf_files = []
        
        # models 폴더 및 하위 폴더 스캔
        for gguf_file in self.models_dir.rglob("*.gguf"):
            relative_path = gguf_file.relative_to(self.root_dir)
            gguf_files.append(relative_path)
        
        return gguf_files
    
    def _generate_model_metadata(self, gguf_file):
        """gguf 파일에서 모델 메타데이터 생성"""
        # 파일명에서 모델명 추출
        file_stem = gguf_file.stem  # 확장자 제거
        
        # ollama_name 생성 (파일명을 소문자로 변환하고 특수문자 처리)
        ollama_name = file_stem.lower().replace("_", "-").replace("--", ":")
        
        # 이미 콜론이 있는 경우 유지
        if ":" not in ollama_name:
            ollama_name = f"{ollama_name}:latest"
        
        # display_name 생성
        display_name = file_stem.replace("-", " ").replace("_", " ").title()
        
        # 타입 결정 (embedding 폴더에 있으면 embedding)
        model_type = "embedding" if "embedding" in str(gguf_file) else "llm"
        
        # 설명 생성
        if model_type == "embedding":
            description = f"{display_name} - 문서 검색 전용 embedding 모델입니다."
        else:
            description = f"{display_name} - LLM 모델입니다."
        
        return {
            "file": str(gguf_file),
            "ollama_name": ollama_name,
            "type": model_type,
            "display_name": display_name,
            "description": description,
            "is_dynamic": True  # 동적으로 감지된 모델 표시
        }
    
    def _create_gui(self):
        """GUI 생성"""
        # 상단 안내 영역
        info_frame = tk.Frame(self.root)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = tk.Label(info_frame, text="간단 Ollama 모델 등록기", 
                               font=("맑은 고딕", 14, "bold"))
        title_label.pack(pady=(0, 5))
        
        guide_label = tk.Label(info_frame, 
                              text="등록할 모델을 선택한 뒤 [선택 모델 등록]을 누르세요.\n"
                                   "이미 등록된 모델은 왼쪽 목록에서 제외됩니다.",
                              font=("맑은 고딕", 9))
        guide_label.pack(pady=(0, 5))
        
        self.status_label = tk.Label(info_frame, text="Ollama 상태 확인 중...", 
                                     font=("맑은 고딕", 9), fg="blue")
        self.status_label.pack(pady=(0, 5))
        
        self.registered_count_label = tk.Label(info_frame, text="등록된 모델: 0개", 
                                               font=("맑은 고딕", 9), fg="green")
        self.registered_count_label.pack(pady=(0, 5))
        
        self.current_register_label = tk.Label(info_frame, text="", 
                                              font=("맑은 고딕", 9), fg="orange")
        self.current_register_label.pack(pady=(0, 5))
        
        # 중간 영역 (왼쪽: 등록 가능, 오른쪽: 등록됨)
        middle_frame = tk.Frame(self.root)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # 왼쪽: 등록 가능한 모델
        left_frame = tk.Frame(middle_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        left_label = tk.Label(left_frame, text="등록 가능한 모델", 
                              font=("맑은 고딕", 10, "bold"))
        left_label.pack(pady=(0, 5))
        
        # 체크박스 리스트를 위한 캔버스와 스크롤바
        left_list_frame = tk.Frame(left_frame)
        left_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.available_canvas = tk.Canvas(left_list_frame, highlightthickness=0)
        self.available_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        left_scrollbar = tk.Scrollbar(left_list_frame, command=self.available_canvas.yview)
        left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.available_canvas.config(yscrollcommand=left_scrollbar.set)
        
        # 체크박스를 담을 프레임
        self.available_check_frame = tk.Frame(self.available_canvas)
        self.available_canvas_window = self.available_canvas.create_window((0, 0), window=self.available_check_frame, anchor="nw")
        
        # 체크박스 변수들 저장
        self.available_check_vars = []
        self.available_check_buttons = []
        
        # 오른쪽: 등록된 모델
        right_frame = tk.Frame(middle_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        right_label = tk.Label(right_frame, text="현재 등록된 Ollama 모델", 
                               font=("맑은 고딕", 10, "bold"))
        right_label.pack(pady=(0, 5))
        
        right_list_frame = tk.Frame(right_frame)
        right_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.registered_listbox = tk.Listbox(right_list_frame, font=("맑은 고딕", 9), 
                                             selectmode=tk.SINGLE)
        self.registered_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.registered_listbox.bind('<<ListboxSelect>>', self._on_registered_select)
        
        right_scrollbar = tk.Scrollbar(right_list_frame, command=self.registered_listbox.yview)
        right_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.registered_listbox.config(yscrollcommand=right_scrollbar.set)
        
        # 하단 설명 영역
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        desc_label = tk.Label(bottom_frame, text="설명", font=("맑은 고딕", 10, "bold"))
        desc_label.pack(pady=(0, 5))
        
        desc_text_frame = tk.Frame(bottom_frame)
        desc_text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.desc_text = tk.Text(desc_text_frame, font=("맑은 고딕", 9), height=8)
        self.desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.desc_text.config(state=tk.DISABLED)
        
        desc_scrollbar = tk.Scrollbar(desc_text_frame, command=self.desc_text.yview)
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.desc_text.config(yscrollcommand=desc_scrollbar.set)
        
        # 버튼 영역
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.refresh_btn = tk.Button(button_frame, text="새로고침", command=self._refresh_lists,
                                     font=("맑은 고딕", 9))
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.register_btn = tk.Button(button_frame, text="선택 모델 등록", 
                                      command=self._register_selected,
                                      font=("맑은 고딕", 9))
        self.register_btn.pack(side=tk.LEFT, padx=5)
        
        self.delete_btn = tk.Button(button_frame, text="선택 등록 모델 삭제",
                                   command=self._delete_selected,
                                   font=("맑은 고딕", 9))
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        
        close_btn = tk.Button(button_frame, text="닫기", command=self.root.quit,
                             font=("맑은 고딕", 9))
        close_btn.pack(side=tk.RIGHT, padx=5)
    
    def _check_ollama(self):
        """Ollama 사용 가능 여부 확인"""
        try:
            result = subprocess.run(["ollama", "--version"], 
                                   capture_output=True, text=True, timeout=5,
                                   encoding='utf-8', errors='replace')
            if result.returncode == 0:
                self.ollama_available = True
                self.status_label.config(text="Ollama 사용 가능", fg="green")
            else:
                self.ollama_available = False
                self.status_label.config(text="Ollama가 설치되어 있지 않거나 PATH에 없습니다.", fg="red")
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            self.ollama_available = False
            self.status_label.config(text="Ollama가 설치되어 있지 않거나 PATH에 없습니다.", fg="red")
        
        # 버튼 상태 업데이트
        state = tk.NORMAL if self.ollama_available else tk.DISABLED
        self.register_btn.config(state=state)
        self.delete_btn.config(state=state)
    
    def _get_registered_models(self):
        """현재 등록된 Ollama 모델 목록 가져오기"""
        if not self.ollama_available:
            return []
        
        try:
            result = subprocess.run(["ollama", "list"], 
                                   capture_output=True, text=True, timeout=10,
                                   encoding='utf-8', errors='replace')
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                models = []
                for line in lines[1:]:  # 첫 줄은 헤더
                    if line.strip():
                        parts = line.split()
                        if parts:
                            models.append(parts[0])
                return models
        except subprocess.TimeoutExpired:
            pass
        
        return []
    
    def _get_disk_space(self):
        """디스크 여유 공간 확인 (GB 단위)"""
        try:
            usage = shutil.disk_usage(self.root_dir)
            free_gb = usage.free / (1024 ** 3)
            return free_gb
        except Exception:
            return 0
    
    def _get_model_size(self, model_file_path):
        """모델 파일 크기 확인 (GB 단위)"""
        try:
            size_bytes = model_file_path.stat().st_size
            size_gb = size_bytes / (1024 ** 3)
            return size_gb
        except Exception:
            return 0
    
    def _format_size(self, size_gb):
        """크기를 읽기 쉬운 형식으로 변환"""
        if size_gb >= 1:
            return f"{size_gb:.2f} GB"
        else:
            size_mb = size_gb * 1024
            return f"{size_mb:.2f} MB"
    
    def _refresh_lists(self):
        """목록 새로고침"""
        try:
            # 등록된 모델 목록 가져오기
            self.registered_models = self._get_registered_models()
            
            # 등록 가능한 모델 목록 생성
            self.available_models = []
            
            # 1. 하드코딩된 MODELS에서 추가
            for model in MODELS:
                model_file = self.root_dir / model["file"]
                # 파일이 존재하고 아직 등록되지 않은 모델만
                if model_file.exists() and model["ollama_name"] not in self.registered_models:
                    self.available_models.append(model)
            
            # 2. 동적으로 감지된 gguf 파일에서 추가
            gguf_files = self._scan_gguf_files()
            registered_ollama_names = {m["ollama_name"] for m in MODELS}
            
            for gguf_file in gguf_files:
                # 이미 MODELS에 있는 파일은 건너뜀
                if any(gguf_file == m["file"] for m in MODELS):
                    continue
                
                # 메타데이터 생성
                model_metadata = self._generate_model_metadata(gguf_file)
                
                # 이미 등록된 모델이면 건너뜀
                if model_metadata["ollama_name"] in self.registered_models:
                    continue
                
                # ollama_name이 이미 MODELS에 있으면 건너뜀 (중복 방지)
                if model_metadata["ollama_name"] in registered_ollama_names:
                    continue
                
                self.available_models.append(model_metadata)
            
            # 왼쪽 목록 업데이트 (체크박스)
            # 기존 체크박스 제거
            for widget in self.available_check_frame.winfo_children():
                widget.destroy()
            
            self.available_check_vars = []
            self.available_check_buttons = []
            
            # 디스크 여유 공간 확인
            free_disk_space = self._get_disk_space()
            
            for model in self.available_models:
                var = tk.BooleanVar()
                self.available_check_vars.append(var)
                
                # 모델 파일 크기 확인
                model_file = self.root_dir / model["file"]
                model_size = self._get_model_size(model_file)
                
                # 디스크 공간 확인
                can_register = model_size <= free_disk_space
                
                # 체크박스와 라벨을 한 줄에 배치
                row_frame = tk.Frame(self.available_check_frame)
                row_frame.pack(fill=tk.X, pady=1)
                
                checkbox = tk.Checkbutton(row_frame, variable=var, font=("맑은 고딕", 9),
                                         state=tk.NORMAL if can_register else tk.DISABLED)
                checkbox.pack(side=tk.LEFT, padx=5)
                
                label = tk.Label(row_frame, text=model["display_name"], font=("맑은 고딕", 9),
                               fg="black" if can_register else "gray")
                label.pack(side=tk.LEFT)
                
                # 라벨 클릭 시 설명 표시
                label.bind('<Button-1>', lambda e, m=model, s=model_size, f=free_disk_space: self._on_available_select(m, s, f))
                
                self.available_check_buttons.append((checkbox, label, model, can_register))
            
            # 캔버스 스크롤 영역 업데이트
            self.available_check_frame.update_idletasks()
            bbox = self.available_canvas.bbox("all")
            if bbox:
                self.available_canvas.config(scrollregion=bbox)
            else:
                self.available_canvas.config(scrollregion=(0, 0, 1, 1))
        except Exception as e:
            messagebox.showerror("오류", f"목록 새로고침 중 오류 발생: {e}")
            return
        
        # 오른쪽 목록 업데이트
        self.registered_listbox.delete(0, tk.END)
        for model_name in self.registered_models:
            # 이 프로그램에서 관리하는 모델은 표시 이름으로, 그 외는 모델명으로 표시
            display_name = None
            for model in MODELS:
                if model["ollama_name"] == model_name:
                    display_name = model["display_name"]
                    break
            
            if display_name:
                self.registered_listbox.insert(tk.END, display_name)
            else:
                self.registered_listbox.insert(tk.END, model_name)
        
        # 설명 영역 초기화
        self._clear_description()
        
        # 등록된 모델 수 업데이트
        managed_count = sum(1 for name in self.registered_models if any(m["ollama_name"] == name for m in MODELS))
        self.registered_count_label.config(text=f"등록된 모델: {managed_count}개 (총 {len(self.registered_models)}개)")
    
    def _on_available_select(self, model, model_size, free_disk_space):
        """등록 가능 모델 선택 시 설명 표시"""
        # 디스크 공간 정보 추가
        size_info = f"\n\n필요 공간: {self._format_size(model_size)} / 여유 공간: {self._format_size(free_disk_space)}"
        
        if model_size > free_disk_space:
            size_info += f"\n⚠️ 디스크 공간 부족으로 등록할 수 없습니다!"
        
        description_text = f"파일명: {model['file']}\n표시명: {model['display_name']}\nOllama 등록명: {model['ollama_name']}{size_info}\n\n{model['description']}"
        self._show_description(model["display_name"], description_text)
    
    def _on_registered_select(self, event):
        """등록된 모델 선택 시 모델명 표시"""
        selection = self.registered_listbox.curselection()
        if selection:
            index = selection[0]
            model_name = self.registered_models[index]
            self._show_description(f"등록된 모델: {model_name}", 
                                   f"Ollama 등록명: {model_name}")
    
    def _show_description(self, title, text):
        """설명 표시"""
        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete(1.0, tk.END)
        self.desc_text.insert(tk.END, f"{title}\n\n{text}")
        self.desc_text.config(state=tk.DISABLED)
    
    def _clear_description(self):
        """설명 영역 초기화"""
        self.desc_text.config(state=tk.NORMAL)
        self.desc_text.delete(1.0, tk.END)
        self.desc_text.insert(tk.END, "모델을 선택하면 설명이 표시됩니다.")
        self.desc_text.config(state=tk.DISABLED)
    
    def _register_selected(self):
        """선택한 모델 등록"""
        selected_models = []
        for i, var in enumerate(self.available_check_vars):
            if var.get():
                selected_models.append(self.available_models[i])
        
        if not selected_models:
            messagebox.showwarning("경고", "등록할 모델을 선택하세요.")
            return
        
        # 등록 진행
        success_count = 0
        for model in selected_models:
            if self._register_model(model):
                success_count += 1
        
        if success_count > 0:
            messagebox.showinfo("완료", f"{success_count}개 모델 등록 완료")
            self._refresh_lists()
            self._save_installed_models()
        else:
            messagebox.showerror("오류", "모델 등록 실패")
    
    def _register_model(self, model):
        """단일 모델 등록"""
        try:
            # 현재 등록 중인 모델 표시
            self.current_register_label.config(text=f"등록 중: {model['display_name']}")
            self.root.update()
            
            # Modelfile 생성
            model_file = self.root_dir / model["file"]
            modelfile_name = model["ollama_name"].replace(":", "_")
            modelfile_path = self.modelfiles_dir / f"{modelfile_name}.Modelfile"
            
            with open(modelfile_path, "w", encoding="utf-8") as f:
                f.write(f'FROM "{model_file}"\n')
            
            # 로그 영역 초기화 및 시작 메시지
            self._show_log(f"모델 등록 시작: {model['display_name']}\n")
            self._show_log(f"Ollama 등록명: {model['ollama_name']}\n")
            self._show_log(f"Modelfile: {modelfile_path}\n")
            self._show_log("-" * 50 + "\n")
            
            # ollama create 실행 (실시간 로그)
            process = subprocess.Popen(
                ["ollama", "create", model["ollama_name"], "-f", str(modelfile_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            
            # 실시간 로그 읽기 (ANSI escape sequences 제거 및 중복 필터링)
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            
            last_line = ""
            for line in process.stdout:
                line = line.rstrip('\r\n')
                if not line:  # 빈 라인 무시
                    continue
                
                # ANSI escape sequences 제거
                clean_line = ansi_escape.sub('', line)
                
                # 빈 라인이 되면 무시
                if not clean_line:
                    continue
                
                # 같은 라인이 반복되면 마지막 라인 대체 (프로그래스바)
                if clean_line == last_line:
                    self._show_log(clean_line, replace_last=True)
                else:
                    self._show_log(clean_line)
                    last_line = clean_line
                
                self.root.update()  # GUI 업데이트
            
            process.wait()
            
            self._show_log("-" * 50 + "\n")
            if process.returncode == 0:
                self._show_log(f"✓ {model['display_name']} 등록 완료\n\n")
            else:
                self._show_log(f"✗ {model['display_name']} 등록 실패 (코드: {process.returncode})\n\n")
            
            # 현재 등록 중인 모델 표시 초기화
            self.current_register_label.config(text="")
            self.root.update()
            
            return process.returncode == 0
        except subprocess.TimeoutExpired:
            self._show_log("✗ 등록 시간 초과\n\n")
            self.current_register_label.config(text="")
            self.root.update()
            return False
        except Exception as e:
            self._show_log(f"✗ 등록 중 오류: {e}\n\n")
            self.current_register_label.config(text="")
            self.root.update()
            return False
    
    def _show_log(self, message, replace_last=False):
        """로그 메시지 표시"""
        self.desc_text.config(state=tk.NORMAL)
        
        # 메시지가 비어있으면 무시
        if not message:
            self.desc_text.config(state=tk.DISABLED)
            return
        
        if replace_last:
            # 마지막 라인을 대체 (프로그래스바 업데이트용)
            # 텍스트가 비어있지 않을 때만 대체
            if self.desc_text.get("1.0", tk.END).strip():
                self.desc_text.delete("end-1l linestart", "end-1l lineend")
                self.desc_text.insert("end-1l lineend", message)
            else:
                # 비어있으면 그냥 추가
                self.desc_text.insert(tk.END, message + '\n')
        else:
            # 일반 메시지는 새 라인에 추가
            if not message.endswith('\n'):
                message += '\n'
            self.desc_text.insert(tk.END, message)
        
        self.desc_text.see(tk.END)  # 자동 스크롤
        self.desc_text.config(state=tk.DISABLED)
    
    def _delete_selected(self):
        """선택한 등록 모델 삭제"""
        selection = self.registered_listbox.curselection()
        if not selection:
            messagebox.showwarning("경고", "삭제할 모델을 선택하세요.")
            return
        
        index = selection[0]
        model_name = self.registered_models[index]
        
        # 확인
        if not messagebox.askyesno("확인", f"선택한 Ollama 모델을 삭제하시겠습니까?\n\n{model_name}"):
            return
        
        # 삭제 실행
        try:
            result = subprocess.run(
                ["ollama", "rm", model_name],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                messagebox.showinfo("완료", "모델 삭제 완료")
                self._refresh_lists()
                self._save_installed_models()
            else:
                messagebox.showerror("오류", f"모델 삭제 실패:\n{result.stderr}")
        except subprocess.TimeoutExpired:
            messagebox.showerror("오류", "모델 삭제 시간 초과")
        except Exception as e:
            messagebox.showerror("오류", f"모델 삭제 중 오류:\n{e}")
    
    def _save_installed_models(self):
        """installed_models.json 저장"""
        try:
            # 현재 등록된 모델 목록 다시 가져오기
            current_registered = self._get_registered_models()
            
            # 이 프로그램에서 관리하는 모델만 필터링
            managed_names = [m["ollama_name"] for m in MODELS]
            installed = [name for name in current_registered if name in managed_names]
            
            # models 배열 생성
            models_data = []
            for model in MODELS:
                if model["ollama_name"] in installed:
                    models_data.append({
                        "name": model["ollama_name"],
                        "display_name": model["display_name"],
                        "type": model["type"],
                        "provider": "ollama",
                        "summary": model["description"],
                        "source_file_relative": model["file"],
                        "installed": True
                    })
            
            # recommended 설정
            llm_models = [m for m in models_data if m["type"] == "llm"]
            embedding_models = [m for m in models_data if m["type"] == "embedding"]
            
            recommended = {
                "chat_model": None,
                "fallback_chat_model": None,
                "lite_chat_model": None,
                "embedding_model": None
            }
            
            if llm_models:
                # 기본 채팅 모델
                if any(m["name"] == "nuni-gemma4-e2b-fast:latest" for m in llm_models):
                    recommended["chat_model"] = "nuni-gemma4-e2b-fast:latest"
                else:
                    recommended["chat_model"] = llm_models[0]["name"]
                
                # 대체 채팅 모델
                if any(m["name"] == "nuni-gemma3-4b-stable:latest" for m in llm_models):
                    recommended["fallback_chat_model"] = "nuni-gemma3-4b-stable:latest"
                elif len(llm_models) > 1:
                    recommended["fallback_chat_model"] = llm_models[1]["name"]
                
                # 라이트 채팅 모델
                if any(m["name"] == "nuni-gemma3-1b-lite:latest" for m in llm_models):
                    recommended["lite_chat_model"] = "nuni-gemma3-1b-lite:latest"
            
            if embedding_models:
                if any(m["name"] == "nuni-embed-kure:latest" for m in embedding_models):
                    recommended["embedding_model"] = "nuni-embed-kure:latest"
            
            # JSON 저장
            data = {
                "ollama_base_url": "http://localhost:11434",
                "models": models_data,
                "recommended": recommended
            }
            
            with open(self.installed_models_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            print(f"installed_models.json 저장 실패: {e}")
    
    def run(self):
        """GUI 실행"""
        self.root.mainloop()


def main():
    """메인 함수"""
    app = SimpleOllamaModelRegister()
    app.run()


if __name__ == "__main__":
    main()
