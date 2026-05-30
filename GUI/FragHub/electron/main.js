import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import path from 'path'
import { fileURLToPath } from 'url'

// Recréation de l'équivalent de __dirname pour le mode module
const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

function createWindow () {
    const mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        autoHideMenuBar: true,
        webPreferences: {
            // On lie le fichier preload qui est resté en .cjs
            preload: path.join(__dirname, 'preload.cjs'),
            nodeIntegration: false,
            contextIsolation: true
        }
    })

    // En développement, Electron charge le serveur local de Nuxt
    mainWindow.loadURL('http://localhost:3000')
}

app.whenReady().then(() => {
    // 1. Écouteur pour la sélection de FICHIERS (InputTab)
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

    // 2. Écouteur pour la sélection de DOSSIER (OutputTab)
    ipcMain.handle('dialog:openFolder', async () => {
        const { canceled, filePaths } = await dialog.showOpenDialog({
            title: 'Select output directory',
            properties: ['openDirectory']
        })
        return canceled ? null : filePaths[0]
    })

    createWindow()
})

// Quitter l'app quand toutes les fenêtres sont fermées (sauf sur Mac)
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') app.quit()
})