======================================================================
 pyApp_changemaster_Pro.py - コード詳細解説
======================================================================

このファイルは、tkinterを使用してGUIアプリケーションを構築し、PyInstallerをバックグラウンドで実行してPythonスクリプトをWindowsの実行可能ファイル（.exe）に変換するツールです。

---
■ クラス: PyAppChanger(tk.Tk)
---
このアプリケーションのすべての機能とUIを管理するメインクラスです。tkinterのウィンドウ（tk.Tk）を継承して作られています。

---
■ クラス変数 (定数データ)
---
- STDLIB_MODULES:
  Pythonの標準ライブラリ名のセットです。自動検出機能が、`os`や`sys`のような標準ライブラリを「外部パッケージ」として誤検出し、`pip install`しようとするのを防ぐために使われます。

- IMPORT_TO_PIP:
  Pythonスクリプトで`import cv2`と書かれていても、インストールするパッケージ名は`opencv-python`である、といった名前の違いを吸収するための辞書です。

- COLLECT_ALL_TARGETS / COPY_METADATA_TARGETS:
  特定のライブラリ（例: `Pillow`, `pandas`）をexe化する際に、PyInstallerが依存ファイルを自動で見つけられないことがあります。これらのライブラリが検出された場合に、PyInstallerに「関連ファイルをすべて集めてください（`--collect-all`）」や「メタデータをコピーしてください（`--copy-metadata`）」といった特別なオプションを自動で追加するためのリストです。

---
■ メソッド解説
---

1. __init__(self) - 初期化メソッド
   - 役割: アプリケーションの起動時に最初に呼ばれ、ウィンドウの基本的な設定とUIの構築を行います。
   - 処理詳細:
     - `super().__init__()`: 親クラスである`tk.Tk`の初期化処理を呼び出します。
     - `self.title(...)`, `self.geometry(...)`: ウィンドウのタイトルと初期サイズを設定します。
     - `self.process = None`: PyInstallerのプロセスを管理するための変数を初期化します。
     - `self._create_widgets()`: アプリケーションの心臓部であるUI部品作成メソッドを呼び出します。

2. _create_widgets(self) - GUI部品の作成・配置
   - 役割: ユーザーが操作するすべてのUI要素（ボタン、入力欄、ラベル等）を生成し、ウィンドウ内にきれいに配置します。
   - 処理詳細:
     - スクロール機能: ウィンドウサイズが小さい場合でもすべての要素が見えるように、`Canvas`と`Scrollbar`を組み合わせてスクロール可能な領域を作成します。
     - 各UIエリアの作成:
       - 「ファイル・環境設定」: ファイル選択やパッケージ指定のための`Entry`（入力欄）、`Button`（ボタン）、`Label`（文字）を`grid`レイアウトで配置します。
       - 「オプション」: PyInstallerの各種オプションに対応する`Checkbutton`（チェックボックス）や`Radiobutton`（ラジオボタン）を配置します。
       - 「進行状態」: `Progressbar`（プログレスバー）と`scrolledtext.ScrolledText`（ログ表示エリア）を配置します。
       - 「ボタンエリア」: `start_conversion`と`cancel_conversion`メソッドに紐付いた「変換を開始する」「中断」ボタンを配置します。

3. ファイル参照メソッド群 (browse_*)
   - `browse_py(self)`, `browse_out(self)`, `browse_icon(self)`, `browse_data(self)`
   - 役割: 「参照」ボタンが押された際の動作を定義します。
   - 処理詳細: `filedialog`モジュールを使い、ファイル選択またはフォルダ選択のダイアログを表示します。ユーザーが選択したパスを取得し、対応する`StringVar`（UIの入力欄と連動する変数）に設定します。

4. 自動検出メソッド群 (auto_detect_*)
   - `auto_detect_data(self)`, `auto_detect_pip(self)`
   - 役割: 「自動」ボタンが押された際に、指定されたPythonスクリプトの依存関係を解析します。
   - 処理詳細:
     - `ast` (Abstract Syntax Trees)モジュール: Pythonスクリプトを「コード」としてではなく、「構造化されたデータ（木構造）」として読み込みます。
     - `ast.walk(tree)`: 木構造をたどり、`import`文や文字列リテラル（例: "data/image.png"）をすべて探し出します。
     - `STDLIB_MODULES`や`IMPORT_TO_PIP`といったクラス変数と照らし合わせ、インストールが必要なパッケージ名や、同梱が必要なデータファイルを推測し、UIに反映させます。

5. 変換実行プロセス
   - start_conversion(self):
     - 役割: 「変換を開始する」ボタンのアクション。UIの応答性を維持しつつ、時間のかかるexe化処理を開始します。
     - 処理詳細:
       - UIの無効化: 処理中にユーザーがボタンを二重押しできないように、ボタンを無効化します。
       - スレッドの起動: `threading.Thread`を使い、`_run_conversion`メソッドをバックグラウンドで実行します。これにより、UIがフリーズするのを防ぎます。

   - _run_conversion(self, py_file, out_dir):
     - 役割: exe化に関するすべての実作業を統括する、このツールの最重要メソッド。
     - 処理詳細:
       1. **環境特定**: `runtime`フォルダにあるポータブルPython（`Scripts/python.exe`）を探し、見つかればそれを使います。見つからなければ、PCにインストールされているシステムPythonを使おうとします。
       2. **パッケージインストール**: UIで指定された追加パッケージがあれば、`subprocess.Popen`を使って`pip install`コマンドを実行します。
       3. **コマンド構築**: UIのチェックボックスや入力内容を基に、`pyinstaller`に渡すコマンドライン引数のリスト（`cmd`）を動的に作成します。例えば、`--onefile`や`--noconsole`などをリストに追加していきます。
       4. **PyInstaller実行**: `subprocess.Popen`を使い、構築した`cmd`リストを実行します。`stdout`（標準出力）をパイプで受け取り、`log`メソッド経由でリアルタイムにUIのログエリアに表示します。
       5. **後処理**: PyInstallerの完了後、必要に応じて`_create_vbs_launcher`や`_create_shortcut`を呼び出してランチャーを作成したり、`_remove_zone_identifier`でWindowsの警告表示を抑制したりします。
       6. **完了通知**: `messagebox.showinfo`で、成功した旨をユーザーに伝えます。

   - cancel_conversion(self):
     - 役割: 「中断」ボタンのアクション。実行中のPyInstallerプロセスを停止させます。
     - 処理詳細: `self.process.terminate()`を呼び出し、`subprocess.Popen`で開始した外部プロセスに終了シグナルを送ります。

6. 補助メソッド
   - log(self, message): UIのログエリアに、スレッドセーフに（どのスレッドから呼ばれても問題ないように）テキストを追記します。
   - set_progress(self, percent): UIのプログレスバーの値を更新します。
   - _generate_version_file(...): PyInstallerの`--version-file`オプションで使用する、exeのプロパティ（会社名、バージョン情報など）を定義したテキストファイルを生成します。
   - _create_vbs_launcher(...), _create_shortcut(...), _remove_zone_identifier(...):
     - 役割: Windowsの特定の機能（VBScript, ショートカット, ファイルのセキュリティ属性）を操作します。
     - 処理詳細: `subprocess.run`を使って、これらの操作を専門に行う`powershell`コマンドをバックグラウンドで実行します。パスにスペースや特殊文字が含まれていても問題が起きないよう、パスを適切にクォートするなどの安全対策が施されています。
