import { app, BrowserWindow, ipcMain, dialog } from 'electron' // <--- LIGNE MANQUANTE AJOUTÉE ICI
import fs from 'fs'
import path from 'path'
import { spawn } from 'child_process'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

let pythonProcess = null

function startPythonServer() {
    let exePath = '';

    if (process.platform === 'win32') {
        // On remonte de 3 niveaux :
        // 1. sort de 'electron'
        // 2. sort de 'FragHub' (Vue)
        // 3. sort de 'GUI'
        // Puis on descend dans scripts/dist/...
        exePath = path.join(__dirname, '../../../scripts/dist/FragHub_Windows_1.4.2_x64/FragHub_Windows_1.4.2_x64.exe');
    } else {
        // Au cas où tu compiles pour Mac/Linux plus tard
        exePath = path.join(__dirname, '../../../scripts/dist/FragHub_Mac_1.4.2/FragHub_Mac_1.4.2');
    }

    console.log("Tentative de lancement de l'exécutable :", exePath);

    // Sécurité : On vérifie que le chemin est parfaitement correct
    if (!fs.existsSync(exePath)) {
        console.error("❌ ERREUR CRITIQUE : L'exécutable est introuvable à ce chemin ! Vérifie le path.join.");
        return;
    }

    // Lancement de l'exécutable
    pythonProcess = spawn(exePath, [], {
        stdio: 'inherit' // Permet de voir les logs FastAPI (comme le port 8000) dans la console d'Electron
    });

    pythonProcess.on('error', (err) => {
        console.error("❌ Erreur lors du lancement de l'exécutable FragHub:", err);
    });
}

function createWindow () {
    const mainWindow = new BrowserWindow({
        title: 'FragHub',
        width: 1280,
        height: 720,
        minWidth: 960,
        minHeight: 540,
        backgroundColor: '#ffffff',

        // On remonte d'un dossier (..) pour sortir de 'electron'
        // et on va chercher l'image dans 'app/assets'
        icon: path.join(__dirname, '../app/assets/FragHub_icon.png'),

        autoHideMenuBar: true,
        webPreferences: {
            preload: path.join(__dirname, 'preload.cjs'),
            nodeIntegration: false,
            contextIsolation: true
        }
    })

    mainWindow.setAspectRatio(16 / 9)

    // En développement, Electron charge le serveur local de Nuxt
    mainWindow.loadURL('http://localhost:3000')
}

app.whenReady().then(() => {
    // 1. Lancement du backend Python en premier
    try {
        startPythonServer();
        console.log("Backend Python lancé avec succès.");
    } catch (err) {
        console.error("Erreur critique au lancement du backend:", err);
    }

    // 2. Écouteur pour la sélection de FICHIERS (InputTab)
    ipcMain.handle('dialog:openFiles', async () => {
        const { canceled, filePaths } = await dialog.showOpenDialog({
            title: 'Select input files',
            properties: ['openFile', 'multiSelections'],
            filters: [
                { name: 'Spectrometry Files', extensions: ['json', 'csv', 'msp', 'mgf'] }
            ]
        })
        return canceled ? [] : filePaths
    })

    // 3. Écouteur pour la sélection de DOSSIER (OutputTab)
    ipcMain.handle('dialog:openFolder', async () => {
        const { canceled, filePaths } = await dialog.showOpenDialog({
            title: 'Select output directory',
            properties: ['openDirectory']
        })
        return canceled ? null : filePaths[0]
    })

    // 4. Création de la fenêtre
    createWindow()
})

// N'oublie pas d'ajouter ceci pour nettoyer proprement à la fermeture :
app.on('will-quit', () => {
    if (pythonProcess) {
        pythonProcess.kill();
        console.log("Serveur Python arrêté.");
    }
});