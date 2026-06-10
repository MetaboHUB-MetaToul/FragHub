# Developer Documentation: FragHub

This guide details the steps required to set up the development environment, compile the Python backend, and generate the Electron application installer on macOS.

---

## 1. Prerequisites and Python Configuration

Before you begin, make sure the following tools are installed on your machine:
*   **Node.js**: [Download Node.js](https://nodejs.org/) (LTS version recommended).
*   **Python 3.12**: [Download Python 3.12](https://www.python.org/downloads/release/python-3128/).

### Python Environment Initialization
To isolate project dependencies, you need to create a virtual environment (if not already done). Open your terminal in the folder containing the Python code and run the following commands:

```bash
# 1. Create the virtual environment (only once)
python3 -m venv .venv

# 2. Activate the virtual environment
source .venv/bin/activate

# 3. Install the required libraries
pip install -r requirements.txt
```

---

## 2. Project Installation

Start by retrieving the source code, then install the Front-End dependencies.

```bash
# 1. Clone the repository locally
git clone https://github.com/eMetaboHUB/FragHub.git
cd FragHub

# 2. Navigate to the Front-End folder (Graphical Interface)
cd GUI

# 3. Install Node.js packages
npm install
```

> ⚠️ **IMPORTANT NOTE FOR MACOS: ELECTRON INSTALLATION BUG**
> It has been observed that the standard `npm install` command currently fails on macOS when installing Electron. To work around this issue, you must install Electron manually into your `node_modules` directly from the official Git repository.
> You can use the following command (still in the `GUI` folder):
> ```bash
> npm install git+https://github.com/electron/electron.git
> ```

---

## 3. Backend Compilation (Python)

The core logic of the application is developed in Python. For Electron to run it autonomously, it must be packaged with PyInstaller.

1. Navigate to the `scripts` folder.
2. Run the following command (note the use of `:` as separator for macOS):

```bash
pyinstaller --noconfirm --onedir --noconsole --icon="GUI/assets/FragHub_Python_icon.icns" --name="FragHub_Backend" --add-data="../datas:datas" --add-data="GUI/assets:GUI/assets" --hidden-import=uvicorn.logging --hidden-import=uvicorn.loops --hidden-import=uvicorn.loops.auto --hidden-import=uvicorn.protocols.http.auto --hidden-import=uvicorn.protocols.websockets.auto FragHub.py
```

> **📌 Important notes regarding the Backend:**
> *   **Icon:** On macOS, the standard icon format is `.icns`.
> *   **Generated files:** PyInstaller will create the compiled backend as a folder or `.app` bundle (including the executable and the `_internal` folder) in `scripts/dist/FragHub_Backend`.
> *   ⚠️ **Golden rule:** This PyInstaller command **must be re-run every time you modify a Python source file or external data such as databases**.

---

## 4. Development Mode (Dev)

To work on the graphical interface in real time (with hot reloading) and test the application:

1. Navigate to the `GUI` folder.
2. In a first terminal, start the Nuxt development server:
```bash
npm run dev
```
3. In a second terminal (still in `GUI`), launch the Electron application in dev mode:
```bash
npm run electron:dev
```
*(You can also use `npm run electron` to launch the wrapper without the extended development tools).*

---

## 5. Build and Installer Creation (Production)

To generate the distributable version of the application (the `.dmg` or `.app` installation file for the end user):

1. Navigate to the `GUI` folder.
2. Generate the static Front-End files:
```bash
npm run generate
```
> *   **Generated files:** The compiled Front-End code will be placed in the hidden `.output/public/` folder.
> *   ⚠️ **Golden rule:** The `npm run generate` command **must be re-run every time you modify Front-End code** (`.vue` files, `main.js`, etc.) before launching the installer creation.

3. Launch the final Electron installer build for macOS:
```bash
npm run build:electron -- --mac
```
> *   **Generated files:** Once the process is complete, the macOS installer (`.dmg` file) ready for distribution will be located in the `dist_electron/` folder, at the root of your `GUI` folder.