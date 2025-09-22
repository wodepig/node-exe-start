打包命令:
python -m pip install pyinstaller
python -m PyInstaller --onefile --noconsole --name NodeServiceManager --add-data "utils.py;." --add-data "config.json;." main.py