# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 22:46:10 2026

@author: TARS
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
import subprocess
import threading
import ast
import shutil

class PyAppChanger(tk.Tk):
    # Pythonの標準ライブラリ
    STDLIB_MODULES = {
        "os", "sys", "re", "math", "datetime", "time", "json", "random", "collections",
        "itertools", "functools", "urllib", "sqlite3", "tkinter", "csv", "argparse",
        "subprocess", "threading", "multiprocessing", "logging", "pathlib", "shutil",
        "socket", "hashlib", "hmac", "base64", "uuid", "copy", "pickle", "traceback",
        "ast", "typing", "io", "string", "warnings", "tempfile", "glob", "zipfile", "tarfile"
    }
    if hasattr(sys, 'stdlib_module_names'):
        STDLIB_MODULES.update(sys.stdlib_module_names)

    # import名とpipパッケージ名が異なる代表的なモジュール
    IMPORT_TO_PIP = {
        "cv2": "opencv-python",
        "PIL": "pillow",
        "sklearn": "scikit-learn",
        "yaml": "pyyaml",
        "bs4": "beautifulsoup4",
        "dotenv": "python-dotenv",
        "dateutil": "python-dateutil",
        "fitz": "pymupdf",
        "jwt": "pyjwt",
        "discord": "discord.py",
        "github": "pygithub"
    }

    # --collect-all が必要になりやすい厄介なライブラリ群
    COLLECT_ALL_TARGETS = {
        "PIL", "pillow", "cv2", "opencv-python", "matplotlib", "scipy", "pandas", 
        "numpy", "pygame", "mediapipe", "pyzbar", "customtkinter", "moviepy", 
        "soundfile", "librosa", "plotly", "pyqt5", "pyqt6", "pyside2", "pyside6", "docx"
    }

    # --copy-metadata が必要なライブラリ群
    COPY_METADATA_TARGETS = {
        "pillow", "scikit-learn", "pandas", "pymupdf", "pyjwt"
    }

    def __init__(self):
        super().__init__()
        self.title("PyApp_changemaster")
        self.geometry("680x750")
        self.process = None
        self.is_cancelled = False

        self._create_widgets()

    def _create_widgets(self):
        # --- Root container with scrollbar ---
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # --- Original widgets go into scrollable_frame ---
        padding_opts = {'padx': 10, 'pady': 5}

        # --- ファイル設定エリア ---
        frame_file = ttk.LabelFrame(scrollable_frame, text="ファイル・環境設定")
        frame_file.pack(fill=tk.X, **padding_opts)

        ttk.Label(frame_file, text="対象のpyファイル:").grid(row=0, column=0, sticky=tk.W, **padding_opts)
        self.py_file_var = tk.StringVar()
        self.py_file_var.trace_add("write", self._on_py_file_changed)
        ttk.Entry(frame_file, textvariable=self.py_file_var, width=50).grid(row=0, column=1, **padding_opts)
        ttk.Button(frame_file, text="参照", command=self.browse_py).grid(row=0, column=2, **padding_opts)

        ttk.Label(frame_file, text="出力先フォルダ:").grid(row=1, column=0, sticky=tk.W, **padding_opts)
        self.out_dir_var = tk.StringVar()
        ttk.Entry(frame_file, textvariable=self.out_dir_var, width=50).grid(row=1, column=1, **padding_opts)
        ttk.Button(frame_file, text="参照", command=self.browse_out).grid(row=1, column=2, **padding_opts)

        ttk.Label(frame_file, text="アイコン(.ico) [任意]:").grid(row=2, column=0, sticky=tk.W, **padding_opts)
        self.icon_var = tk.StringVar()
        ttk.Entry(frame_file, textvariable=self.icon_var, width=50).grid(row=2, column=1, **padding_opts)
        ttk.Button(frame_file, text="参照", command=self.browse_icon).grid(row=2, column=2, **padding_opts)

        ttk.Label(frame_file, text="追加データ [自動/手動]:").grid(row=3, column=0, sticky=tk.W, **padding_opts)
        self.data_dir_var = tk.StringVar()
        ttk.Entry(frame_file, textvariable=self.data_dir_var, width=50).grid(row=3, column=1, **padding_opts)
        
        btn_frame_data = ttk.Frame(frame_file)
        btn_frame_data.grid(row=3, column=2, sticky=tk.W, **padding_opts)
        ttk.Button(btn_frame_data, text="参照", command=self.browse_data, width=5).pack(side=tk.LEFT, padx=(0, 2))
        ttk.Button(btn_frame_data, text="自動", command=lambda: self.auto_detect_data(silent=False), width=5).pack(side=tk.LEFT)

        # 追加インストール(pip)エリア
        ttk.Label(frame_file, text="追加インストール(pip)\n※スペース区切り:").grid(row=4, column=0, sticky=tk.W, **padding_opts)
        self.pip_packages_var = tk.StringVar()
        ttk.Entry(frame_file, textvariable=self.pip_packages_var, width=50).grid(row=4, column=1, **padding_opts)
        
        btn_frame_pip = ttk.Frame(frame_file)
        btn_frame_pip.grid(row=4, column=2, sticky=tk.W, **padding_opts)
        ttk.Button(btn_frame_pip, text="自動", command=lambda: self.auto_detect_pip(silent=False), width=5).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(btn_frame_pip, text="例: pandas", foreground="gray").pack(side=tk.LEFT)

        # --- オプションエリア ---
        frame_opt = ttk.LabelFrame(scrollable_frame, text="オプション")
        frame_opt.pack(fill=tk.X, **padding_opts)

        self.onefile_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_opt, text="1つのファイルに纏める (--onefile) ※起動が遅くなり検知リスク増", variable=self.onefile_var).grid(row=0, column=0, columnspan=2, sticky=tk.W, **padding_opts)

        self.noconsole_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_opt, text="黒画面（コンソール）を隠す (--noconsole)", variable=self.noconsole_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, **padding_opts)

        self.bundle_runtime_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_opt, text="runtimeを同梱する (exe本体の横にポータブルPythonをコピー)", variable=self.bundle_runtime_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, **padding_opts)

        # 出力・起動方式の選択肢
        ttk.Label(frame_opt, text="出力・起動方式:").grid(row=3, column=0, sticky=tk.NW, **padding_opts)
        self.output_mode_var = tk.IntVar(value=2)
        
        radio_frame = ttk.Frame(frame_opt)
        radio_frame.grid(row=3, column=1, sticky=tk.W, **padding_opts)
        ttk.Radiobutton(radio_frame, text="Master直下に出力 [dist廃止 / セキュリティ◎]", variable=self.output_mode_var, value=2).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(radio_frame, text="distに出力 ＋ VBSランチャー作成 [フォルダ移動対応]", variable=self.output_mode_var, value=0).pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(radio_frame, text="distに出力 ＋ 標準ショートカット作成", variable=self.output_mode_var, value=1).pack(anchor=tk.W, pady=2)

        self.sac_bypass_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_opt, text="Smart App Control 誤検知対策 (UPX無効化 ＆ バージョン情報の自動付与)", variable=self.sac_bypass_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, **padding_opts)

        ttk.Label(frame_opt, text="PyInstallerの追加引数:\n※DLLエラー回避等に使用").grid(row=5, column=0, sticky=tk.W, **padding_opts)
        self.extra_args_var = tk.StringVar(value="")
        ttk.Entry(frame_opt, textvariable=self.extra_args_var, width=45).grid(row=5, column=1, sticky=tk.W, **padding_opts)
        ttk.Label(frame_opt, text="例: --copy-metadata pillow", foreground="gray").grid(row=5, column=1, sticky=tk.E, **padding_opts)

        # --- 進行状態エリア ---
        frame_prog = ttk.LabelFrame(scrollable_frame, text="進行状態")
        frame_prog.pack(fill=tk.BOTH, expand=True, **padding_opts)

        self.progress_var = tk.DoubleVar()
        self.progressbar = ttk.Progressbar(frame_prog, variable=self.progress_var, maximum=100)
        self.progressbar.pack(fill=tk.X, **padding_opts)

        self.percent_label = ttk.Label(frame_prog, text="0%")
        self.percent_label.pack()

        self.log_area = scrolledtext.ScrolledText(frame_prog, height=10, state=tk.DISABLED, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True, **padding_opts)

        # --- ボタンエリア ---
        frame_btn = tk.Frame(scrollable_frame)
        frame_btn.pack(fill=tk.X, pady=10)

        self.start_btn = tk.Button(frame_btn, text="★ 変換を開始する", font=("メイリオ", 12, "bold"), bg="#0078D7", fg="white", padx=20, pady=10, relief=tk.FLAT, command=self.start_conversion)
        self.start_btn.pack(side=tk.LEFT, padx=20)

        self.cancel_btn = tk.Button(frame_btn, text="中断", font=("メイリオ", 10), bg="#ff4c4c", fg="white", padx=15, pady=5, relief=tk.FLAT, command=self.cancel_conversion, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.RIGHT, padx=20, pady=5)

    def _on_py_file_changed(self, *args):
        self.pip_packages_var.set("")
        self.data_dir_var.set("")
        self.extra_args_var.set("")
        self.auto_detect_all(silent=True)

    def _get_clean_env(self):
        env = os.environ.copy()
        if hasattr(sys, '_MEIPASS'):
            env.pop('TCL_LIBRARY', None)
            env.pop('TK_LIBRARY', None)
            path_list = env.get('PATH', '').split(os.pathsep)
            path_list = [p for p in path_list if sys._MEIPASS not in p]
            env['PATH'] = os.pathsep.join(path_list)
        return env

    def _remove_zone_identifier(self, target_dir):
        if os.name != 'nt': return
        try:
            ps_path = target_dir.replace("'", "''")
            ps_script = f"Get-ChildItem -LiteralPath '{ps_path}' -Recurse -File | Unblock-File; Unblock-File -LiteralPath '{ps_path}'"
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)
            self.log("Zone.Identifier (セキュリティ警告) を一括削除しました。")
        except Exception as e:
            self.log(f"[警告] ZoneID削除失敗: {e}")

    def _generate_version_file(self, target_dir, app_name):
        content = f"""# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '041104b0',
        [StringStruct('CompanyName', 'MyCompany'),
        StringStruct('FileDescription', '{app_name}'),
        StringStruct('FileVersion', '1.0.0.0'),
        StringStruct('InternalName', '{app_name}'),
        StringStruct('LegalCopyright', 'Copyright (c) 2026'),
        StringStruct('OriginalFilename', '{app_name}.exe'),
        StringStruct('ProductName', '{app_name}'),
        StringStruct('ProductVersion', '1.0.0.0')])
      ]),
    VarFileInfo([VarStruct('Translation', [1041, 1200])])
  ]
)
"""
        ver_file_path = os.path.join(target_dir, "version_info.txt")
        with open(ver_file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return ver_file_path

    def _create_vbs_launcher(self, target_exe_rel, launcher_path_base):
        if os.name != 'nt': return
        
        out_dir = os.path.dirname(launcher_path_base)
        launcher_name = os.path.basename(launcher_path_base)
        vbs_name = f"{launcher_name}_launcher.vbs"
        vbs_file = os.path.abspath(os.path.join(out_dir, vbs_name))
        
        target_exe_abs = os.path.abspath(os.path.join(out_dir, target_exe_rel))
        target_exe_rel_vbs = os.path.relpath(target_exe_abs, out_dir).replace('/', '\\')
        
        vbs_code = f"""Option Explicit
Dim ws, fso, baseDir, targetPath
Set ws = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
baseDir = fso.GetParentFolderName(WScript.ScriptFullName)
targetPath = fso.BuildPath(baseDir, "{target_exe_rel_vbs}")

If fso.FileExists(targetPath) Then
    ws.Run Chr(34) & targetPath & Chr(34), 1, False
Else
    MsgBox "本体のexeが見つかりません:" & vbCrLf & targetPath, 16, "起動エラー"
End If
"""
        with open(vbs_file, "w", encoding="cp932", errors="replace") as f:
            f.write(vbs_code)
            
        shortcut_path = os.path.abspath(launcher_path_base + ".lnk")
        
        try:
            ps_shortcut = shortcut_path.replace("'", "''")
            ps_vbs_target = vbs_file.replace("'", "''")
            ps_icon_target = target_exe_abs.replace("'", "''")
            ps_work_dir = out_dir.replace("'", "''")
            
            ps_script = (
                f"$wshell = New-Object -ComObject WScript.Shell;\n"
                f"$s = $wshell.CreateShortcut('{ps_shortcut}');\n"
                f"$s.TargetPath = '{ps_vbs_target}';\n"
                f"$s.WorkingDirectory = '{ps_work_dir}';\n"
                f"$s.IconLocation = '{ps_icon_target}, 0';\n"
                f"$s.Save();"
            )
            
            result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], 
                                    creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True, text=True, encoding='cp932', errors='replace')
            
            if result.returncode != 0:
                self.log(f"[警告] ショートカット作成に失敗しました: {result.stderr}")
            else:
                self.log(f">>> ドライブ移動対応の起動用ショートカット ({launcher_name}.lnk) を作成しました。")
                
        except Exception as e:
            self.log(f"[エラー] ショートカット処理中に例外発生: {e}")

    def _create_shortcut(self, target_exe, shortcut_path):
        if os.name != 'nt': return
        try:
            target_exe = os.path.abspath(target_exe)
            shortcut_path = os.path.abspath(shortcut_path)
            work_dir = os.path.dirname(target_exe)
            
            ps_shortcut = shortcut_path.replace("'", "''")
            ps_target = target_exe.replace("'", "''")
            ps_work = work_dir.replace("'", "''")
            
            ps_script = (
                f"$wshell = New-Object -ComObject WScript.Shell;\n"
                f"$s = $wshell.CreateShortcut('{ps_shortcut}');\n"
                f"$s.TargetPath = '{ps_target}';\n"
                f"$s.WorkingDirectory = '{ps_work}';\n"
                f"$s.Save();"
            )
            
            result = subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], 
                                    creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True, text=True, encoding='cp932', errors='replace')
            
            if result.returncode != 0:
                self.log(f"[警告] ショートカット作成失敗: {result.stderr}")
            else:
                self.log(f">>> 標準ショートカット(LNK)を作成しました: {os.path.basename(shortcut_path)}")
        except Exception as e:
            self.log(f"[警告] ショートカット作成時エラー: {e}")

    def auto_detect_all(self, silent=True):
        self.auto_detect_data(silent=True)
        self.auto_detect_pip(silent=True)

    def auto_detect_data(self, silent=True):
        py_file = self.py_file_var.get()
        if not py_file or not os.path.exists(py_file): return 0

        target_py_abs = os.path.abspath(py_file)
        base_dir = os.path.dirname(target_py_abs)
        target_py_name = os.path.basename(target_py_abs).lower()

        detected_data = set()
        literals = set()

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    val = node.value.strip().replace('\\', '/')
                    if 2 < len(val) < 200 and '\n' not in val:
                        if 'runtime' in val.lower(): continue
                        if '.' in val or '/' in val:
                            literals.add(val)
        except Exception as e:
            self.log(f"[警告] データ自動解析エラー: {e}")

        file_map = {}
        exclude_dirs = {'__pycache__', '.git', '.vscode', '.idea', 'venv', 'env', '.venv', 'build', 'dist', 'node_modules', 'runtime'}
        
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d.lower() not in exclude_dirs and not d.startswith('.') and 'runtime' not in d.lower()]
            for file in files:
                if file.lower() == target_py_name or file.endswith(('.py', '.pyc', '.spec')) or 'runtime' in file.lower():
                    continue
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, base_dir).replace('\\', '/')
                if file not in file_map: file_map[file] = []
                file_map[file].append(rel_path)

        for lit in literals:
            full_path = os.path.abspath(os.path.join(base_dir, lit))
            if os.path.exists(full_path) and full_path.startswith(base_dir):
                if full_path.lower() != target_py_abs.lower():
                    detected_data.add(full_path)
                continue
            basename = os.path.basename(lit)
            if basename in file_map:
                for rel_path in file_map[basename]:
                    exact_file_path = os.path.abspath(os.path.join(base_dir, rel_path))
                    detected_data.add(exact_file_path)

        if detected_data:
            current = self.data_dir_var.get()
            detected_str = " | ".join(sorted(list(detected_data)))
            if current:
                self.data_dir_var.set(f"{current} | {detected_str}")
            else:
                self.data_dir_var.set(detected_str)
            
        if not silent:
            messagebox.showinfo("データ自動検出", f"【依存データ】 {len(detected_data)} 件を特定しました。")

        return len(detected_data)

    def auto_detect_pip(self, silent=True):
        py_file = self.py_file_var.get()
        if not py_file or not os.path.exists(py_file): return 0

        base_dir = os.path.dirname(os.path.abspath(py_file))
        detected_modules = set()

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        detected_modules.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        detected_modules.add(node.module.split('.')[0])
        except Exception as e:
            self.log(f"[警告] pip自動解析エラー: {e}")

        pip_list = []
        collect_list = []
        metadata_list = []

        for mod in detected_modules:
            if mod in self.STDLIB_MODULES:
                continue
            if os.path.exists(os.path.join(base_dir, f"{mod}.py")) or os.path.exists(os.path.join(base_dir, mod, "__init__.py")):
                continue
            
            pip_name = self.IMPORT_TO_PIP.get(mod, mod)
            pip_list.append(pip_name)

            if mod in self.COLLECT_ALL_TARGETS or pip_name in self.COLLECT_ALL_TARGETS:
                collect_list.append(pip_name)
                
            if pip_name in self.COPY_METADATA_TARGETS:
                metadata_list.append(pip_name)

        if pip_list:
            current_pip = self.pip_packages_var.get().replace(',', ' ').split()
            combined_pip = sorted(list(set(current_pip + pip_list)))
            self.pip_packages_var.set(" ".join(combined_pip))
            
        if collect_list or metadata_list:
            current_extra = self.extra_args_var.get()
            
            for c_mod in set(collect_list):
                flag = f"--collect-all {c_mod}"
                if flag not in current_extra:
                    current_extra = f"{current_extra} {flag}".strip()
                    
            for m_mod in set(metadata_list):
                flag = f"--copy-metadata {m_mod}"
                if flag not in current_extra:
                    current_extra = f"{current_extra} {flag}".strip()

            if "pillow" in pip_list:
                for h_mod in ["PIL._imaging", "PIL._tkinter"]:
                    flag = f"--hidden-import {h_mod}"
                    if flag not in current_extra:
                        current_extra = f"{current_extra} {flag}".strip()
                    
            self.extra_args_var.set(current_extra)

        if not silent:
            msg = f"【pipパッケージ】 {len(pip_list)} 件を特定しました。\n\n検出モジュール:\n{', '.join(pip_list) if pip_list else 'なし'}"
            if collect_list or metadata_list:
                msg += f"\n\n※実行時のエラーを防ぐため、以下の引数を自動適用しました:"
                if collect_list: msg += f"\n--collect-all: {', '.join(set(collect_list))}"
                if metadata_list: msg += f"\n--copy-metadata: {', '.join(set(metadata_list))}"
                if "pillow" in pip_list: msg += f"\n--hidden-import: PIL._imaging, PIL._tkinter"
            messagebox.showinfo("自動検出完了", msg)

        return len(pip_list)

    def browse_py(self):
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if path: self.py_file_var.set(path)

    def browse_out(self):
        path = filedialog.askdirectory()
        if path: self.out_dir_var.set(path)

    def browse_icon(self):
        path = filedialog.askopenfilename(filetypes=[("Icon Files", "*.ico")])
        if path: self.icon_var.set(path)

    def browse_data(self):
        path = filedialog.askdirectory(title="依存フォルダを選択")
        if not path: path = filedialog.askopenfilename(title="依存ファイルを選択")
        if path:
            cur = self.data_dir_var.get()
            self.data_dir_var.set(f"{cur} | {path}" if cur else path)

    def log(self, message):
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)

    def set_progress(self, percent):
        self.progress_var.set(percent)
        self.percent_label.config(text=f"{int(percent)}%")
        self.update_idletasks()

    def start_conversion(self):
        py_file = self.py_file_var.get()
        out_dir = self.out_dir_var.get()
        if not os.path.exists(py_file) or not os.path.exists(out_dir):
            messagebox.showerror("エラー", "ファイルまたは出力先が正しくありません。")
            return
        
        self.start_btn.config(state=tk.DISABLED, bg="#cccccc")
        self.cancel_btn.config(state=tk.NORMAL)
        self.is_cancelled = False
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)
        
        threading.Thread(target=self._run_conversion, args=(py_file, out_dir), daemon=True).start()

    def _run_conversion(self, py_file, out_dir):
        try:
            clean_env = self._get_clean_env()
            self.log(">>> プロセス開始")
            self.set_progress(2)
            
            # --- 1. Python実行環境の特定 ---
            if getattr(sys, 'frozen', False):
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            portable_python_dir = os.path.join(app_dir, "runtime")
            # Correct path for venv created by uv/venv
            portable_python = os.path.join(portable_python_dir, "Scripts", "python.exe")
            
            if os.path.exists(portable_python):
                python_exe = portable_python
                self.log(f">>> [ポータブル環境] を使用します。")
                self.log(f"    パス: {python_exe}")
            else:
                if getattr(sys, 'frozen', False):
                    python_exe = shutil.which("python")
                    if not python_exe:
                        self.log("【エラー】システムに Python が見つかりません。")
                        messagebox.showerror("環境エラー", "Pythonが見つかりません。")
                        return
                else:
                    python_exe = sys.executable
                self.log(f">>> [システム環境] を使用します。")
                self.log(f"    パス: {python_exe}")

            # --- 2. pipによる必要パッケージの自動インストール ---
            packages_to_install = []
            
            check_cmd = [python_exe, "-m", "PyInstaller", "--version"]
            check_proc = subprocess.run(check_cmd, capture_output=True, env=clean_env, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            if check_proc.returncode != 0:
                self.log(">>> PyInstallerが見つかりません。自動インストール対象に追加します。")
                packages_to_install.append("pyinstaller")

            user_pkgs_raw = self.pip_packages_var.get().replace(',', ' ').split()
            if user_pkgs_raw:
                packages_to_install.extend(user_pkgs_raw)

            if packages_to_install:
                self.set_progress(5)
                self.log(f">>> パッケージをインストール中: {', '.join(packages_to_install)}")
                pip_cmd = [python_exe, "-m", "pip", "install"] + packages_to_install
                
                self.process = subprocess.Popen(pip_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='cp932', errors='replace', env=clean_env, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                
                # Safer iteration over stdout
                if self.process.stdout:
                    for line in self.process.stdout:
                        if self.is_cancelled: return
                        self.log("  [pip] " + line.strip())
                self.process.wait()
                
                if self.process.returncode == 0:
                    self.log(">>> パッケージのインストール完了！")
                else:
                    self.log("【警告】一部パッケージのインストールに失敗した可能性がありますが、続行します。")

            self.set_progress(10)

            # --- 3. 変換先フォルダの準備 ---
            base_dir = os.path.dirname(os.path.abspath(py_file))
            base_name = os.path.splitext(os.path.basename(py_file))[0]
            m_dir = os.path.join(out_dir, f"{base_name}_Master")
            counter = 1
            while os.path.exists(m_dir):
                m_dir = os.path.join(out_dir, f"{base_name}_Master_{counter}")
                counter += 1
            os.makedirs(m_dir, exist_ok=True)

            # --- 4. PyInstaller コマンド構築 ---
            is_direct_master = (self.output_mode_var.get() == 2)
            dist_path = m_dir if is_direct_master else os.path.join(m_dir, "dist")

            cmd = [python_exe, "-m", "PyInstaller", "--name", base_name, 
                   "--workpath", os.path.join(m_dir, "build"), 
                   "--distpath", dist_path,
                   "--specpath", m_dir, "-y"]

            if self.onefile_var.get(): cmd.append("--onefile")
            if self.noconsole_var.get(): cmd.append("--noconsole")
            if self.icon_var.get(): cmd.extend(["--icon", self.icon_var.get()])

            # Smart App Control 対策
            ver_file = None  
            if self.sac_bypass_var.get():
                cmd.append("--noupx")
                self.log(">>> SAC対策: UPX無効化とバージョン情報の生成を適用します")
                ver_file = self._generate_version_file(m_dir, base_name)
                cmd.extend(["--version-file", ver_file])

            extra_args = self.extra_args_var.get().strip()
            if extra_args:
                import shlex
                cmd.extend(shlex.split(extra_args))

            data_raw = self.data_dir_var.get()
            if data_raw:
                for p in data_raw.split('|'):
                    p = p.strip()
                    if os.path.exists(p):
                        try:
                            rel = os.path.relpath(p, base_dir)
                            if rel.startswith(".."):
                                dest = os.path.basename(p) if os.path.isdir(p) else "."
                            else:
                                if os.path.isdir(p): dest = rel
                                else:
                                    dest = os.path.dirname(rel)
                                    if not dest: dest = "."
                        except ValueError:
                            dest = os.path.basename(p) if os.path.isdir(p) else "."
                        cmd.extend(["--add-data", f"{p}{os.pathsep}{dest}"])

            cmd.append(py_file)
            
            # --- 5. PyInstaller 実行 ---
            self.log(">>> PyInstaller 実行中...")
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='cp932', errors='replace', env=clean_env, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

            # Safer iteration over stdout
            if self.process.stdout:
                for line in self.process.stdout:
                    if self.is_cancelled: break
                    self.log(line.strip())
                    if "Building EXE" in line: self.set_progress(70)
            self.process.wait()

            if self.is_cancelled: return

            # --- 5.5. フォルダ階層の整理 (PyInstallerが勝手に作る不要なサブフォルダをフラット化) ---
            if not self.onefile_var.get():
                built_sub_dir = os.path.join(dist_path, base_name)
                if os.path.exists(built_sub_dir) and os.path.isdir(built_sub_dir):
                    self.log(">>> 余分なフォルダ階層を整理して見やすくしています...")
                    for item in os.listdir(built_sub_dir):
                        src_path = os.path.join(built_sub_dir, item)
                        dst_path = os.path.join(dist_path, item)
                        
                        # 上書き回避処理
                        if os.path.exists(dst_path):
                            if os.path.isdir(dst_path): shutil.rmtree(dst_path)
                            else: os.remove(dst_path)
                            
                        shutil.move(src_path, dist_path)
                    os.rmdir(built_sub_dir)

            # --- 6. 仕上げ処理 (ランチャー・ショートカット作成) ---
            self.log(">>> 起動用ファイルのセットアップ中...")
            
            shortcut_base = os.path.join(m_dir, base_name)
            
            # 階層整理により、exeの場所は常に dist_path 直下になります
            target_exe = os.path.join(dist_path, f"{base_name}.exe")
            
            if is_direct_master:
                # [モード2] Master直下の場合、本体がすぐ見つかるためショートカットは作成不要
                self.log(">>> exe本体がMaster直下にあるため、ショートカット作成をスキップします。")
            else:
                # [モード0, 1] distフォルダを利用する場合
                mode = self.output_mode_var.get()
                if mode == 0:
                    if self.onefile_var.get():
                        self._create_shortcut(target_exe, shortcut_base + ".lnk")
                    else:
                        target_rel = os.path.relpath(target_exe, m_dir).replace('/', '\\')
                        self._create_vbs_launcher(target_rel, shortcut_base)
                elif mode == 1:
                    self._create_shortcut(target_exe, shortcut_base + ".lnk")

            self.log(">>> セキュリティ保護処理 (ZoneID除去)")
            self.set_progress(85)
            self._remove_zone_identifier(m_dir)

            # --- 7. runtime の同梱処理 ---
            if self.bundle_runtime_var.get():
                self.log(">>> runtime を同梱中 (コピーしています...)")
                dest_runtime = os.path.join(dist_path, "runtime")

                if os.path.exists(portable_python_dir):
                    try:
                        shutil.copytree(portable_python_dir, dest_runtime)
                        self.log(">>> runtime の同梱が完了しました。")
                    except Exception as e:
                        self.log(f"[警告] runtime のコピーに失敗しました: {e}")
                else:
                    self.log("[警告] ツール側に runtime フォルダが見つからないため、同梱をスキップします。")

            self.set_progress(100)
            self.log(">>> すべて完了！")
            
            messagebox.showinfo("成功", f"exe化が完了しました！\n\n出力先: {m_dir}")
            
            self.pip_packages_var.set("")
            self.data_dir_var.set("")
            self.extra_args_var.set("")

        except Exception as e:
            self.log(f"エラー発生: {e}")
        finally:
            self.start_btn.config(state=tk.NORMAL, bg="#0078D7")
            self.cancel_btn.config(state=tk.DISABLED)

    def cancel_conversion(self):
        if self.process:
            self.is_cancelled = True
            self.process.terminate()
            self.log("!!! 中断されました !!!")

if __name__ == "__main__":
    app = PyAppChanger()
    app.mainloop()