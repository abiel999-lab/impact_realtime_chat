# Desktop Client


## Run (dev)
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
source .venv/bin/activate
pip install -r requirements-client.txt
python client_main.py


## Build .exe (Windows)
pip install pyinstaller
pyinstaller --noconfirm --windowed --onefile client_main.py --name "Impact Chat"
# Output: dist/Impact Chat.exe


## Configure
Edit `client_config.py` to point `API_BASE`/`SOCKET_URL` to your server (local or online).