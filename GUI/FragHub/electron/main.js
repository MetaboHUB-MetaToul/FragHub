import { app, BrowserWindow, ipcMain, dialog, protocol, net } from 'electron'
import fs from 'fs'
import path from 'path'
import { spawn } from 'child_process'
import { fileURLToPath, pathToFileURL } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

let pythonProcess = null
let splashWindow = null
let mainWindow = null

// --- ÉTAPE CRUCIALE : Enregistrement du protocole AVANT le lancement ---
protocol.registerSchemesAsPrivileged([
    { scheme: 'app', privileges: { secure: true, standard: true, supportFetchAPI: true, bypassCSP: true, corsEnabled: true } }
])

// ---------------------------------------------------------------
// Backend Python
// ---------------------------------------------------------------
function startPythonServer() {
    let exePath = '';

    if (app.isPackaged) {
        exePath = path.join(process.resourcesPath, 'bin', 'FragHub_Backend.exe');
    } else {
        exePath = path.join(__dirname, '../../../scripts/dist/FragHub_Backend/FragHub_Backend.exe');
    }

    console.log("Tentative de lancement de l'exécutable :", exePath);

    if (!fs.existsSync(exePath)) {
        console.error("❌ ERREUR CRITIQUE : L'exécutable est introuvable :", exePath);
        return;
    }

    pythonProcess = spawn(exePath, [], { stdio: 'inherit' });

    pythonProcess.on('error', (err) => {
        console.error("❌ Erreur lancement FragHub:", err);
    });
}

// ---------------------------------------------------------------
// Fenêtre splash — petite, sans chrome, toujours au premier plan
// ---------------------------------------------------------------
function createSplashWindow() {
    splashWindow = new BrowserWindow({
        width: 600,
        height: 750,
        frame: false,
        transparent: true,
        backgroundColor: '#00000000',
        resizable: false,
        alwaysOnTop: true,
        center: true,
        skipTaskbar: true,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        }
    })

    splashWindow.loadFile(path.join(__dirname, 'Splash.html'))

    splashWindow.webContents.on('did-finish-load', () => {
        const iconPath = path.join(__dirname, '../app/assets/FragHub_icon.png').replace(/\\/g, '/')

        splashWindow.webContents.executeJavaScript(
            `if (document.getElementById('logo')) { 
            document.getElementById('logo').src = 'file:///${iconPath}' 
         }`
        ).catch(err => console.error("Erreur logo splash:", err))
    })
}

// ---------------------------------------------------------------
// Fenêtre principale — créée cachée, montrée après le splash
// ---------------------------------------------------------------
function createMainWindow() {
    mainWindow = new BrowserWindow({
        title: 'FragHub',
        width: 1280,
        height: 720,
        show: false,
        webPreferences: {
            preload: path.join(__dirname, 'preload.cjs'),
            nodeIntegration: false,
            contextIsolation: true,
            webSecurity: false
        }
    })

    console.log("DEBUG: Chargement via app://-/index.html");

    // 👇 ON CHARGE VIA LE NOUVEAU PROTOCOLE 👇
    mainWindow.loadURL('app://-/index.html');

    // On laisse la console ouverte pour vérifier que tout est vert
    mainWindow.webContents.openDevTools();

    mainWindow.once('ready-to-show', () => {
        mainWindow._nuxtReady = true
        maybeShowMain()
    })
}

// ---------------------------------------------------------------
// Polling backend
// ---------------------------------------------------------------
function waitForBackend() {
    let attempts = 0
    const MAX_ATTEMPTS = 60

    const poll = setInterval(async () => {
        attempts++
        try {
            const res = await fetch('http://127.0.0.1:8000/health')
            if (res.ok) {
                clearInterval(poll)
                console.log("✅ Backend prêt — chargement des bases de données")
                setSplashMessage("Loading internal databases…")

                try {
                    const initRes = await fetch('http://127.0.0.1:8000/init-data')
                    if (initRes.ok) {
                        console.log("✅ Bases de données chargées")
                        mainWindow._backendReady = true
                        maybeShowMain()
                    } else {
                        setSplashMessage("Error loading databases. Please restart.")
                    }
                } catch (err) {
                    setSplashMessage("Error loading databases. Please restart.")
                    console.error(err)
                }
            }
        } catch {
            if (attempts >= MAX_ATTEMPTS) {
                clearInterval(poll)
                setSplashMessage("Backend unreachable. Please restart.")
            }
        }
    }, 1000)
}

function maybeShowMain() {
    if (!mainWindow?._nuxtReady || !mainWindow?._backendReady) return

    if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.close()
        splashWindow = null
    }
    mainWindow.show()
}

function setSplashMessage(msg) {
    if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.webContents.executeJavaScript(
            `if (document.getElementById('message')) { 
                document.getElementById('message').textContent = ${JSON.stringify(msg)} 
             }`
        ).catch(err => console.error("Erreur message splash:", err))
    }
}

// ---------------------------------------------------------------
// Démarrage
// ---------------------------------------------------------------
app.whenReady().then(() => {

    // 👇 INTERCEPTION DU PROTOCOLE POUR NUXT 👇
    protocol.handle('app', (request) => {
        let urlPath = request.url.slice(8); // Enlève "app://-/"
        urlPath = urlPath.split('?')[0].split('#')[0]; // Nettoie les paramètres éventuels
        const decodedPath = decodeURIComponent(urlPath);
        const finalPath = decodedPath || 'index.html';

        // Va chercher le fichier localement dans le dossier généré
        const filePath = path.join(app.getAppPath(), '.output', 'public', finalPath);
        return net.fetch(pathToFileURL(filePath).href);
    });

    // 1. Splash.html immédiat
    createSplashWindow()

    // 2. Backend Python
    try {
        startPythonServer()
    } catch (err) {
        console.error("Erreur critique au lancement du backend:", err)
    }

    // 3. Fenêtre principale (cachée)
    createMainWindow()

    // 4. Polling backend
    waitForBackend()

    // IPC — sélection de fichiers (InputTab)
    ipcMain.handle('dialog:openFiles', async () => {
        const { canceled, filePaths } = await dialog.showOpenDialog({
            title: 'Select input files',
            properties: ['openFile', 'multiSelections'],
            filters: [{ name: 'Spectrometry Files', extensions: ['json', 'csv', 'msp', 'mgf'] }]
        })
        return canceled ? [] : filePaths
    })

    // IPC — sélection de dossier (OutputTab)
    ipcMain.handle('dialog:openFolder', async () => {
        const { canceled, filePaths } = await dialog.showOpenDialog({
            title: 'Select output directory',
            properties: ['openDirectory']
        })
        return canceled ? null : filePaths[0]
    })
})

// ---------------------------------------------------------------
// Nettoyage à la fermeture
// ---------------------------------------------------------------
app.on('will-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill()
        console.log("Serveur Python arrêté.")
    }
})