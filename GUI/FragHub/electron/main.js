import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import fs from 'fs'
import path from 'path'
import { spawn } from 'child_process'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

let pythonProcess = null
let splashWindow = null
let mainWindow = null

// ---------------------------------------------------------------
// Backend Python
// ---------------------------------------------------------------
function startPythonServer() {
    let exePath = ''
    if (process.platform === 'win32') {
        exePath = path.join(__dirname, '../../../scripts/dist/FragHub_Windows_1.4.2_x64/FragHub_Windows_1.4.2_x64.exe')
    } else {
        exePath = path.join(__dirname, '../../../scripts/dist/FragHub_Mac_1.4.2/FragHub_Mac_1.4.2')
    }

    console.log("Tentative de lancement de l'exécutable :", exePath)

    if (!fs.existsSync(exePath)) {
        console.error("❌ ERREUR CRITIQUE : L'exécutable est introuvable :", exePath)
        return
    }

    pythonProcess = spawn(exePath, [], { stdio: 'inherit' })
    pythonProcess.on('error', (err) => {
        console.error("❌ Erreur lancement FragHub:", err)
    })
}

// ---------------------------------------------------------------
// Fenêtre splash — petite, sans chrome, toujours au premier plan
// ---------------------------------------------------------------
function createSplashWindow() {
    splashWindow = new BrowserWindow({
        width: 600,
        height: 450,
        frame: false,           // Pas de bordure
        transparent: true,      // Active la transparence
        backgroundColor: '#00000000', // Fond totalement transparent
        resizable: false,
        alwaysOnTop: true,
        center: true,
        skipTaskbar: true,      // N'apparaît pas dans la barre des tâches
        icon: path.join(__dirname, '../app/assets/FragHub_icon.png'),
        webPreferences: {
            preload: path.join(__dirname, 'preload.cjs'),
            nodeIntegration: false,
            contextIsolation: true
        }
    })

    splashWindow.loadFile(path.join(__dirname, 'splash.html'))

    splashWindow.webContents.on('did-finish-load', () => {
        const iconPath = path.join(__dirname, '../app/assets/FragHub_icon.png')
            .replace(/\\/g, '/')
        splashWindow.webContents.executeJavaScript(
            `document.getElementById('logo').src = 'file:///${iconPath}'`
        )
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
        minWidth: 960,
        minHeight: 540,
        backgroundColor: '#ffffff',
        icon: path.join(__dirname, '../app/assets/FragHub_icon.png'),
        autoHideMenuBar: true,
        show: false,             // cachée jusqu'à ce que le splash soit terminé
        webPreferences: {
            preload: path.join(__dirname, 'preload.cjs'),
            nodeIntegration: false,
            contextIsolation: true
        }
    })

    mainWindow.setAspectRatio(16 / 9)
    mainWindow.loadURL('http://localhost:3000')

    mainWindow.once('ready-to-show', () => {
        // La page Nuxt est chargée, on peut déjà montrer la fenêtre
        // si le backend est aussi prêt (géré dans waitForBackend)
        mainWindow._nuxtReady = true
        maybeShowMain()
    })
}

// ---------------------------------------------------------------
// Polling backend : attend que /health réponde, puis charge /init-data
// ---------------------------------------------------------------
function waitForBackend() {
    let attempts = 0
    const MAX_ATTEMPTS = 60  // 60 secondes max

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
            // Serveur pas encore démarré — normal au début
            if (attempts >= MAX_ATTEMPTS) {
                clearInterval(poll)
                setSplashMessage("Backend unreachable. Please restart.")
            }
        }
    }, 1000)
}

// Affiche la fenêtre principale seulement quand Nuxt ET le backend sont prêts
function maybeShowMain() {
    if (!mainWindow?._nuxtReady || !mainWindow?._backendReady) return

    // Transition propre : ferme le splash, montre le principal
    if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.close()
        splashWindow = null
    }
    mainWindow.show()
}

// Envoie un message de statut au splash via executeJavaScript
function setSplashMessage(msg) {
    if (splashWindow && !splashWindow.isDestroyed()) {
        splashWindow.webContents.executeJavaScript(
            `document.getElementById('message').textContent = ${JSON.stringify(msg)}`
        )
    }
}

// ---------------------------------------------------------------
// Démarrage
// ---------------------------------------------------------------
app.whenReady().then(() => {
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