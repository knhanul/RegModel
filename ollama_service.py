import re
import subprocess
from pathlib import Path


class OllamaError(RuntimeError):
    def __init__(self, operation, target, detail):
        self.operation = operation
        self.target = target
        self.detail = detail
        super().__init__(f"{operation} 실패: {target}")


class OllamaService:
    def __init__(self, modelfiles_dir):
        self.modelfiles_dir = Path(modelfiles_dir)
        self.last_error = ""

    def check_connection(self):
        try:
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5, encoding="utf-8", errors="replace")
            self.last_error = result.stderr.strip() if result.returncode else ""
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as error:
            self.last_error = str(error)
            return False

    def list_models(self):
        result = self._run(["ollama", "list"], "모델 목록 조회", "Ollama")
        lines = result.stdout.strip().splitlines()
        models = []
        for line in lines[1:]:
            parts = line.split()
            if parts:
                models.append(parts[0])
        return models

    def create_model(self, model, root_dir, on_output=None):
        if model.get("is_external"):
            model_file = Path(model["file"])
        else:
            model_file = Path(root_dir) / model["file"]
        modelfile_name = model["ollama_name"].replace(":", "_")
        modelfile_path = self.modelfiles_dir / f"{modelfile_name}.Modelfile"
        self.modelfiles_dir.mkdir(parents=True, exist_ok=True)
        modelfile_path.write_text(f'FROM "{model_file}"\n', encoding="utf-8")
        return self._stream(["ollama", "create", model["ollama_name"], "-f", str(modelfile_path)], "모델 등록", model["display_name"], on_output)

    def delete_model(self, model_name):
        return self._run(["ollama", "rm", model_name], "모델 삭제", model_name)

    def show_model(self, model_name):
        try:
            result = subprocess.run(["ollama", "show", model_name], capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
            if result.returncode != 0:
                return None
            info = {}
            for line in result.stdout.splitlines():
                if "\t" in line:
                    key, value = line.split("\t", 1)
                    info[key.strip()] = value.strip()
            return info
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None

    def _run(self, command, operation, target):
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=60, encoding="utf-8", errors="replace")
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as error:
            raise OllamaError(operation, target, str(error)) from error
        if result.returncode != 0:
            raise OllamaError(operation, target, result.stderr.strip() or result.stdout.strip() or "Ollama가 오류를 반환했습니다.")
        return result

    def _stream(self, command, operation, target, on_output=None):
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1)
            ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
            if process.stdout:
                for line in process.stdout:
                    clean_line = ansi_escape.sub("", line.rstrip("\r\n"))
                    if clean_line and on_output:
                        on_output(clean_line)
            process.wait(timeout=600)
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as error:
            if "process" in locals():
                process.kill()
            raise OllamaError(operation, target, str(error)) from error
        if process.returncode != 0:
            raise OllamaError(operation, target, "Ollama 모델 등록 명령이 실패했습니다.")
        return True
