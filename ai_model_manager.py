import json
import shutil
import sys
import threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ollama_service import OllamaError, OllamaService
from ui_theme import COLORS, configure_styles, create_badge, create_card, create_count_badge, get_font
from models import MODELS


APP_TITLE = "포시드 AI 모델 관리자"
APP_SUBTITLE = "로컬 AI 모델 등록·삭제 및 Ollama 실행 환경 관리"


class PosidAIModelManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry("1100x820")
        self.root.minsize(900, 700)
        self.root.configure(bg=COLORS["background"])
        configure_styles(self.root)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.root.bind("<Control-r>", lambda event: self.refresh())
        self.root.bind("<Escape>", lambda event: self.root.focus_set())
        self.root.bind("<Return>", self._on_enter)

        if getattr(sys, "frozen", False):
            self.root_dir = Path(sys.executable).parent
            self.assets_dir = Path(sys._MEIPASS) / "assets"
        else:
            self.root_dir = Path(__file__).parent.resolve()
            self.assets_dir = self.root_dir / "assets"
        self.models_dir = self.root_dir / "models"
        self.embedding_dir = self.models_dir / "embedding"
        self.generated_dir = self.root_dir / "generated"
        self.modelfiles_dir = self.generated_dir / "modelfiles"
        self.installed_models_file = self.generated_dir / "installed_models.json"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_dir.mkdir(parents=True, exist_ok=True)
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self.modelfiles_dir.mkdir(parents=True, exist_ok=True)

        self._set_window_icon()
        self.service = OllamaService(self.modelfiles_dir)
        self.ollama_available = False
        self.available_models = []
        self.registered_models = []
        self.catalog = []
        self.external_models = []
        self.selected_available = None
        self.selected_registered = None
        self.operation_running = False
        self.history = []
        self.last_refresh = "확인 전"
        self._build_ui()
        self.root.after(50, self.refresh)

    def _set_window_icon(self):
        icon_path = self.assets_dir / "posid" / "posid_logo.ico"
        if icon_path.exists():
            try:
                self.root.iconbitmap(str(icon_path))
            except (tk.TclError, OSError):
                pass

    def _build_ui(self):
        main = ttk.Frame(self.root, style="App.TFrame", padding=(20, 16, 20, 14))
        main.pack(fill=tk.BOTH, expand=True)
        main.rowconfigure(2, weight=1)
        main.columnconfigure(0, weight=1)

        header = ttk.Frame(main, style="Header.TFrame", padding=(0, 0, 0, 14))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)
        logo_path = self.assets_dir / "posid" / "posid_logo.png"
        if logo_path.exists():
            try:
                from PIL import Image, ImageTk
                pil_img = Image.open(str(logo_path))
                pil_img.thumbnail((48, 48), Image.LANCZOS)
                self._logo_photo = ImageTk.PhotoImage(pil_img)
                icon = tk.Label(header, image=self._logo_photo, bg=COLORS["background"])
            except ImportError:
                try:
                    raw = tk.PhotoImage(file=str(logo_path))
                    w, h = raw.width(), raw.height()
                    scale = max(1, (h + 47) // 48)
                    self._logo_photo = raw.subsample(scale, scale)
                    icon = tk.Label(header, image=self._logo_photo, bg=COLORS["background"])
                except tk.TclError:
                    icon = tk.Label(header, text="✦", bg=COLORS["primary"], fg="white", font=get_font(20, "bold"), width=2, height=1)
        else:
            icon = tk.Label(header, text="✦", bg=COLORS["primary"], fg="white", font=get_font(20, "bold"), width=2, height=1)
        icon.grid(row=0, column=0, rowspan=2, padx=(0, 12))
        ttk.Label(header, text=APP_TITLE, style="Title.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Label(header, text=APP_SUBTITLE, style="Subtitle.TLabel").grid(row=1, column=1, sticky="w", pady=(2, 0))
        status_box = ttk.Frame(header, style="Header.TFrame")
        status_box.grid(row=0, column=2, rowspan=2, sticky="e")
        self.status_badge = create_badge(status_box, "●  연결 확인 중", COLORS["warning"], "#FFF7E6")
        self.status_badge.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(status_box, text="↻", style="Secondary.TButton", command=self.refresh).pack(side=tk.LEFT)

        self.summary_frame = ttk.Frame(main, style="App.TFrame")
        self.summary_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        for col in range(4):
            self.summary_frame.columnconfigure(col, weight=1, uniform="summary")
        self.summary_values = []
        summary_labels = ("등록 가능한 모델", "등록된 모델", "선택한 모델", "마지막 확인")
        for index, label in enumerate(summary_labels):
            card = create_card(self.summary_frame, 10)
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0))
            card.columnconfigure(0, weight=1)
            ttk.Label(card, text=label, style="SummaryLabel.TLabel").grid(row=0, column=0, sticky="w")
            value = ttk.Label(card, text="0개", style="SummaryValue.TLabel")
            value.grid(row=0, column=1, sticky="e", padx=(8, 0))
            self.summary_values.append(value)

        content = ttk.Frame(main, style="App.TFrame")
        content.grid(row=2, column=0, sticky="nsew", pady=(0, 8))
        content.rowconfigure(0, weight=1)
        content.rowconfigure(1, weight=0)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        self.available_card = self._build_model_card(content, 0, "등록 가능한 모델", "available")
        self.registered_card = self._build_model_card(content, 1, "등록된 Ollama 모델", "registered")
        self.detail_card = create_card(content, 0)
        self.detail_card.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
        self.detail_card.columnconfigure(0, weight=1)
        self.detail_text = tk.Text(self.detail_card, height=6, bg=COLORS["card"], fg=COLORS["text"], font=get_font(11), relief="flat", bd=0, padx=14, pady=4, wrap="word", state="disabled")
        self.detail_text.grid(row=0, column=0, sticky="nsew")
        detail_scrollbar = ttk.Scrollbar(self.detail_card, orient="vertical", command=self.detail_text.yview)
        detail_scrollbar.grid(row=0, column=1, sticky="ns")
        self.detail_text.configure(yscrollcommand=detail_scrollbar.set)
        self.detail_card.rowconfigure(0, weight=1)
        self._show_empty_detail()

        footer = ttk.Frame(main, style="App.TFrame")
        footer.grid(row=3, column=0, sticky="ew")
        footer.columnconfigure(1, weight=1)
        self.operation_label = ttk.Label(footer, text="작업 상태: 대기 중", style="Muted.TLabel")
        self.operation_label.grid(row=0, column=0, sticky="w")
        self.progress = ttk.Progressbar(footer, mode="indeterminate", style="Horizontal.TProgressbar", length=180)
        self.progress.grid(row=0, column=1, sticky="ew", padx=16)
        left_buttons = ttk.Frame(footer, style="App.TFrame")
        left_buttons.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 0))
        ttk.Button(left_buttons, text="새로고침", style="Secondary.TButton", command=self.refresh).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(left_buttons, text="폴더 추가", style="Secondary.TButton", command=self.add_folder).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(left_buttons, text="작업 내역", style="Secondary.TButton", command=self._show_history).pack(side=tk.LEFT)
        right_buttons = ttk.Frame(footer, style="App.TFrame")
        right_buttons.grid(row=1, column=2, sticky="e", pady=(10, 0))
        self.register_button = ttk.Button(right_buttons, text="선택 모델 등록", style="Primary.TButton", command=self.register_selected)
        self.register_button.pack(side=tk.LEFT, padx=(0, 8))
        self.delete_button = ttk.Button(right_buttons, text="선택한 모델 삭제", style="Danger.TButton", command=self.delete_selected)
        self.delete_button.pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(right_buttons, text="닫기", style="Secondary.TButton", command=self.root.destroy).pack(side=tk.LEFT)
        self._update_action_buttons()

    def _build_model_card(self, parent, column, title, kind):
        card = create_card(parent, 14)
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0))
        card.rowconfigure(1, weight=1)
        card.columnconfigure(0, weight=1)
        header = ttk.Frame(card, style="Card.TFrame")
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(header, text=title, style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 10))
        count = create_count_badge(header, "0개")
        count.grid(row=0, column=1, sticky="e", padx=(12, 0), pady=(0, 10))
        if kind == "available":
            self.available_count_badge = count
        else:
            self.registered_count_badge = count
        canvas = tk.Canvas(card, bg=COLORS["card"], highlightthickness=0)
        canvas.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(card, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        canvas.configure(yscrollcommand=scrollbar.set)
        rows = tk.Frame(canvas, bg=COLORS["card"])
        window = canvas.create_window((0, 0), window=rows, anchor="nw")
        rows.bind("<Configure>", lambda event, c=canvas: c.configure(scrollregion=c.bbox("all")))
        canvas.bind("<Configure>", lambda event, c=canvas, w=window: c.itemconfigure(w, width=event.width))
        canvas.bind_all("<MouseWheel>", lambda event, c=canvas: c.yview_scroll(int(-event.delta / 120), "units"))
        if kind == "available":
            self.available_canvas, self.available_rows = canvas, rows
        else:
            self.registered_canvas, self.registered_rows = canvas, rows
        return card

    def _scan_models(self):
        models = []
        known_filenames = set()
        for model in MODELS:
            entry = dict(model)
            filename = entry["file"]
            known_filenames.add(filename)
            found = list(self.models_dir.rglob(filename))
            if found:
                entry["file"] = str(found[0].relative_to(self.root_dir)).replace("\\", "/")
            models.append(entry)
        known_ollama_names = {model["ollama_name"] for model in models}
        for path in self.models_dir.rglob("*.gguf"):
            if path.name in known_filenames:
                continue
            relative = path.relative_to(self.root_dir)
            relative_text = str(relative).replace("\\", "/")
            stem = path.stem
            model_type = "embedding" if "embedding" in relative_text.lower() else "llm"
            ollama_name = stem.lower().replace("_", "-") + ":latest"
            if ollama_name in known_ollama_names:
                continue
            models.append({"file": relative_text, "ollama_name": ollama_name, "type": model_type, "display_name": stem.replace("-", " ").replace("_", " ").title(), "description": "문서 검색 전용 embedding 모델입니다." if model_type == "embedding" else "로컬 GGUF LLM 모델입니다.", "is_dynamic": True})
            known_filenames.add(path.name)
        models_by_filename = {m["file"]: m for m in MODELS}
        for ext_model in self.external_models:
            ext_filename = Path(ext_model["file"]).name
            if ext_filename in models_by_filename:
                base = models_by_filename[ext_filename]
                entry = dict(base)
                entry["file"] = ext_model["file"]
                entry["is_external"] = True
                entry["is_dynamic"] = True
                models.append(entry)
            elif ext_model["ollama_name"] not in known_ollama_names:
                models.append(dict(ext_model))
        return models

    def add_folder(self):
        folder = filedialog.askdirectory(title="GGUF 모델 파일이 있는 폴더 선택")
        if not folder:
            return
        folder_path = Path(folder)
        gguf_files = list(folder_path.rglob("*.gguf"))
        if not gguf_files:
            messagebox.showinfo("폴더 추가", "선택한 폴더에 GGUF 파일이 없습니다.")
            return
        existing_paths = {m["file"] for m in self.external_models}
        models_by_filename = {m["file"]: m for m in MODELS}
        added = 0
        for path in gguf_files:
            abs_path = str(path).replace("\\", "/")
            if abs_path in existing_paths:
                continue
            filename = path.name
            if filename in models_by_filename:
                base = models_by_filename[filename]
                self.external_models.append({"file": abs_path, "ollama_name": base["ollama_name"], "type": base["type"], "display_name": base["display_name"], "description": base["description"], "is_dynamic": True, "is_external": True})
            else:
                stem = path.stem
                model_type = "embedding" if "embedding" in stem.lower() else "llm"
                self.external_models.append({"file": abs_path, "ollama_name": stem.lower().replace("_", "-") + ":latest", "type": model_type, "display_name": stem.replace("-", " ").replace("_", " ").title(), "description": "외부 폴더에서 추가된 " + ("embedding 모델입니다." if model_type == "embedding" else "LLM 모델입니다."), "is_dynamic": True, "is_external": True})
            existing_paths.add(abs_path)
            added += 1
        if added:
            self.operation_label.config(text=f"작업 상태: 폴더에서 {added}개 모델 추가됨")
            self.refresh()
        else:
            messagebox.showinfo("폴더 추가", "새로운 GGUF 파일이 없습니다. 이미 추가된 파일일 수 있습니다.")

    def refresh(self):
        if self.operation_running:
            return
        self._set_status("확인 중", "warning")
        self.operation_label.config(text="작업 상태: 목록을 새로고침하고 있습니다.")
        self._set_refresh_enabled(False)
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        available = []
        registered = []
        connected = self.service.check_connection()
        if connected:
            try:
                registered = self.service.list_models()
            except OllamaError:
                connected = False
        catalog = self._scan_models()
        registered_set = set(registered)
        available = []
        for model in catalog:
            if model["ollama_name"] in registered_set:
                continue
            if model.get("is_external"):
                if Path(model["file"]).exists():
                    available.append(model)
            else:
                if (self.root_dir / model["file"]).exists():
                    available.append(model)
        self.root.after(0, lambda: self._apply_refresh(connected, registered, available, catalog))

    def _apply_refresh(self, connected, registered, available, catalog):
        self.ollama_available = connected
        self.registered_models = registered
        self.available_models = available
        self.catalog = catalog
        self.last_refresh = datetime.now().strftime("%H:%M")
        self._set_status("연결됨" if connected else "연결 안 됨", "success" if connected else "error")
        self._render_available()
        self._render_registered()
        self._update_summary()
        self._set_refresh_enabled(True)
        self._save_installed_models()
        self.operation_label.config(text="작업 상태: 대기 중" if connected else "작업 상태: Ollama에 연결할 수 없습니다.")
        self._update_action_buttons()

    def _render_available(self):
        self._clear_rows(self.available_rows)
        self.available_count_badge.config(text=f"{len(self.available_models)}개")
        if not self.available_models:
            self._empty_row(self.available_rows, "새로 등록할 수 있는 모델이 없습니다.", "현재 설정된 모델 파일과 Ollama 등록 상태를 확인해주세요.")
        for model in self.available_models:
            self._model_row(self.available_rows, model, True)

    def _render_registered(self):
        self._clear_rows(self.registered_rows)
        self.registered_count_badge.config(text=f"{len(self.registered_models)}개")
        if not self.registered_models:
            self._empty_row(self.registered_rows, "현재 Ollama에 등록된 모델이 없습니다.", "왼쪽 목록에서 등록할 모델을 선택해주세요.")
        for name in self.registered_models:
            model = self._registered_metadata(name)
            self._model_row(self.registered_rows, model, False)

    def _model_row(self, parent, model, available):
        selected = model.get("ollama_name") == self.selected_available if available else model.get("ollama_name") == self.selected_registered
        background = COLORS["selected"] if selected else COLORS["card"]
        row = tk.Frame(parent, bg=background, highlightbackground=COLORS["primary"] if selected else COLORS["border"], highlightthickness=1, padx=8, pady=4, cursor="hand2")
        row.pack(fill=tk.X, pady=(0, 3))
        row.columnconfigure(0, weight=1)
        title = model.get("display_name", model["ollama_name"])
        tk.Label(row, text=title, bg=background, fg=COLORS["text"], font=get_font(11, "bold"), anchor="w").grid(row=0, column=0, sticky="ew")
        state = "등록 가능" if available else "사용 가능"
        badge = create_badge(row, state, COLORS["primary"] if available else COLORS["success"], "#EEF5FF" if available else "#ECFDF3")
        badge.grid(row=0, column=1, sticky="e", padx=(6, 0))
        if model.get("is_external"):
            file_path = Path(model["file"]) if model.get("file") else None
        else:
            file_path = self.root_dir / model["file"] if model.get("file") else None
        size = self._format_file_size(file_path) if file_path and file_path.exists() else "파일 크기 확인 불가"
        meta = f"{model['ollama_name']}  ·  {self._purpose(model)}  ·  {size}"
        tk.Label(row, text=meta, bg=background, fg=COLORS["muted"], font=get_font(9), anchor="w").grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 0))
        for widget in (row, *row.winfo_children()):
            widget.bind("<Button-1>", lambda event, m=model, a=available: self._select_model(m, a))
            widget.bind("<Enter>", lambda event, target=row, a=available: target.config(bg=COLORS["selected"] if not selected else COLORS["selected"]))
            widget.bind("<Leave>", lambda event, target=row, a=available: target.config(bg=background))
        row.bind("<space>", lambda event, m=model, a=available: self._select_model(m, a))

    def _empty_row(self, parent, title, subtitle):
        row = tk.Frame(parent, bg=COLORS["card"], pady=24)
        row.pack(fill=tk.X)
        tk.Label(row, text=title, bg=COLORS["card"], fg=COLORS["text"], font=get_font(13, "bold")).pack()
        tk.Label(row, text=subtitle, bg=COLORS["card"], fg=COLORS["muted"], font=get_font(11), wraplength=380).pack(pady=(5, 0))

    def _select_model(self, model, available):
        if available:
            name = model["ollama_name"]
            self.selected_available = None if self.selected_available == name else name
        else:
            self.selected_registered = model["ollama_name"]
        self._show_detail(model, available)
        self._render_available()
        self._render_registered()
        self._update_summary()
        self._update_action_buttons()

    def _show_detail(self, model, available):
        values = [("모델명", model.get("display_name")), ("Ollama 태그", model.get("ollama_name")), ("모델 계열", model.get("type")), ("주요 용도", self._purpose(model)), ("설명", model.get("description", "확인할 수 없음")), ("등록 상태", "등록 가능" if available else "사용 가능")]
        file_value = model.get("file", "")
        if file_value:
            path = Path(file_value) if model.get("is_external") else self.root_dir / file_value
            values.append(("모델 파일", str(path)))
        if not available and self.ollama_available:
            ollama_info = self.service.show_model(model["ollama_name"])
            if ollama_info:
                for key in ("family", "parameter_size", "quantization_level", "context_length"):
                    if key in ollama_info:
                        label_map = {"family": "모델 패밀리", "parameter_size": "파라미터 크기", "quantization_level": "양자화", "context_length": "컨텍스트 길이"}
                        values.append((label_map[key], ollama_info[key]))
        lines = []
        for label, value in values:
            lines.append(f"{label}: {value or '확인할 수 없음'}")
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert("1.0", "\n".join(lines))
        self.detail_text.configure(state="disabled")

    def _show_empty_detail(self):
        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert("1.0", "모델을 선택하면 상세정보가 표시됩니다.")
        self.detail_text.configure(state="disabled")

    def register_selected(self):
        model = next((m for m in self.available_models if m["ollama_name"] == self.selected_available), None)
        if not model or not self.ollama_available or self.operation_running:
            return
        self._run_operation("register", [model])

    def delete_selected(self):
        if not self.selected_registered or not self.ollama_available or self.operation_running:
            return
        model = self._registered_metadata(self.selected_registered)
        if not messagebox.askyesno("모델 삭제 확인", f"{model.get('display_name', self.selected_registered)} 모델을 Ollama에서 삭제하시겠습니까?\n\n삭제한 모델을 다시 사용하려면 모델 등록 작업을 다시 진행해야 합니다."):
            return
        self._run_operation("delete", [model])

    def _run_operation(self, operation, models):
        self.operation_running = True
        self._update_action_buttons()
        self.progress.start(10)
        self._set_refresh_enabled(False)
        threading.Thread(target=self._operation_worker, args=(operation, models), daemon=True).start()

    def _operation_worker(self, operation, models):
        successes = []
        errors = []
        for model in models:
            self.root.after(0, lambda m=model: self.operation_label.config(text=f"작업 상태: {m.get('display_name', m['ollama_name'])} 처리 중…"))
            try:
                if operation == "register":
                    self.service.create_model(model, self.root_dir, lambda line: None)
                else:
                    self.service.delete_model(model["ollama_name"])
                successes.append(model)
            except OllamaError as error:
                errors.append((model, error))
        self.root.after(0, lambda: self._finish_operation(operation, successes, errors))

    def _finish_operation(self, operation, successes, errors):
        self.operation_running = False
        self.progress.stop()
        self.selected_available = None
        self.selected_registered = None
        for model in successes:
            self._add_history(operation, model, True, "완료")
        for model, error in errors:
            self._add_history(operation, model, False, error.detail)
        if errors:
            self._show_operation_error(operation, errors)
        else:
            names = ", ".join(model.get("display_name", model["ollama_name"]) for model in successes)
            self.operation_label.config(text=f"작업 상태: {names} {('등록' if operation == 'register' else '삭제')} 완료")
        self.refresh()

    def _show_operation_error(self, operation, errors):
        model, error = errors[0]
        action = "등록" if operation == "register" else "삭제"
        messagebox.showerror("작업 실패", f"{model.get('display_name', model['ollama_name'])} 모델 {action}에 실패했습니다.\n\nOllama 실행 상태와 모델 파일 경로를 확인해주세요.\n\n상세 오류:\n{error.detail}")

    def _show_history(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("작업 내역")
        dialog.geometry("680x380")
        dialog.configure(bg=COLORS["background"])
        dialog.transient(self.root)
        card = create_card(dialog, 16)
        card.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
        ttk.Label(card, text="작업 내역", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 10))
        text = tk.Text(card, bg=COLORS["card"], fg=COLORS["text"], relief="flat", font=get_font(10), wrap="word")
        text.pack(fill=tk.BOTH, expand=True)
        if not self.history:
            text.insert(tk.END, "아직 작업 내역이 없습니다.")
        else:
            for item in reversed(self.history):
                text.insert(tk.END, f"{item['time']}  ·  {item['operation']}  ·  {item['model']}  ·  {item['result']}\n{item['detail']}\n\n")
        text.config(state=tk.DISABLED)
        ttk.Button(card, text="닫기", style="Secondary.TButton", command=dialog.destroy).pack(anchor="e", pady=(10, 0))
        dialog.bind("<Escape>", lambda event: dialog.destroy())

    def _add_history(self, operation, model, success, detail):
        self.history.append({"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "operation": "등록" if operation == "register" else "삭제", "model": model.get("display_name", model["ollama_name"]), "result": "성공" if success else "실패", "detail": detail})

    def _save_installed_models(self):
        models_data = []
        for model in self.catalog:
            if model["ollama_name"] in self.registered_models:
                models_data.append({"name": model["ollama_name"], "display_name": model.get("display_name", model["ollama_name"]), "type": model.get("type", "llm"), "provider": "ollama", "summary": model.get("description", ""), "source_file_relative": model.get("file"), "installed": True})
        llm_models = [model for model in models_data if model["type"] == "llm"]
        embedding_models = [model for model in models_data if model["type"] == "embedding"]
        recommended = {"chat_model": llm_models[0]["name"] if llm_models else None, "fallback_chat_model": llm_models[1]["name"] if len(llm_models) > 1 else None, "lite_chat_model": None, "embedding_model": embedding_models[0]["name"] if embedding_models else None}
        try:
            self.installed_models_file.write_text(json.dumps({"ollama_base_url": "http://localhost:11434", "models": models_data, "recommended": recommended}, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _registered_metadata(self, name):
        for model in self.catalog:
            if model["ollama_name"] == name:
                return model
        for model in MODELS:
            if model["ollama_name"] == name:
                return dict(model)
        return {"display_name": name, "ollama_name": name, "type": "알 수 없음", "description": "Ollama에 등록된 모델입니다. MODELS 또는 로컬 폴더에서 감지되지 않은 모델입니다."}

    def _purpose(self, model):
        if model.get("type") == "embedding":
            return "문서 검색"
        description = model.get("description", "")
        return description.split(".")[0] if description else "LLM 문서 업무"

    def _format_file_size(self, path):
        try:
            size = path.stat().st_size / (1024 ** 3)
            return f"{size:.2f} GB" if size >= 1 else f"{size * 1024:.2f} MB"
        except OSError:
            return "확인할 수 없음"

    def _clear_rows(self, rows):
        for widget in rows.winfo_children():
            widget.destroy()

    def _set_status(self, text, status):
        colors = {"success": (COLORS["success"], "#ECFDF3"), "error": (COLORS["error"], "#FFF1F2"), "warning": (COLORS["warning"], "#FFF7E6")}
        color, background = colors[status]
        self.status_badge.config(text=f"●  {text}", fg=color, bg=background)

    def _update_summary(self):
        self.summary_values[0].config(text=f"{len(self.available_models)}개")
        self.summary_values[1].config(text=f"{len(self.registered_models)}개")
        self.summary_values[2].config(text=f"{(1 if self.selected_available else 0) + (1 if self.selected_registered else 0)}개")
        self.summary_values[3].config(text=self.last_refresh)

    def _update_action_buttons(self):
        can_register = bool(self.selected_available) and self.ollama_available and not self.operation_running
        can_delete = bool(self.selected_registered) and self.ollama_available and not self.operation_running
        self.register_button.config(state=tk.NORMAL if can_register else tk.DISABLED, text="선택 모델 등록" if not self.operation_running else "작업 중…")
        self.delete_button.config(state=tk.NORMAL if can_delete else tk.DISABLED)

    def _set_refresh_enabled(self, enabled):
        state = tk.NORMAL if enabled and not self.operation_running else tk.DISABLED
        for widget in self.root.winfo_children():
            self._set_refresh_in(widget, state)

    def _set_refresh_in(self, widget, state):
        try:
            if isinstance(widget, ttk.Button) and widget.cget("text") in ("↻", "새로고침"):
                widget.config(state=state)
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            self._set_refresh_in(child, state)

    def _on_enter(self, event):
        if self.selected_available and self.ollama_available and not self.operation_running:
            self.register_selected()

    def run(self):
        self.root.mainloop()


def main():
    PosidAIModelManager().run()


if __name__ == "__main__":
    main()
