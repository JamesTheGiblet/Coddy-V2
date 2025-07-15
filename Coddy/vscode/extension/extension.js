// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
const vscode = require('vscode');

/**
 * @typedef {Object} CoddyApiResponse
 * @property {string} content - The file content for 'read' command.
 * @property {string} message - A general success message.
 * @property {string} detail - An error detail message.
 */

/**
 * This method is called when your extension is activated
 * Your extension is activated the very first time the command is executed
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {

    // Use the console to output diagnostic information (console.log) and errors (console.error)
    // This line of code will only be executed once when your extension is activated
    console.log('Congratulations, your extension "coddy-extension" is now active!');

    // The command has been defined in the package.json file
    // Now provide the implementation of the command with registerCommand
    // The commandId parameter must match the command field in package.json

    // Command: Coddy: Hello World
    let helloWorldDisposable = vscode.commands.registerCommand('coddy.helloWorld', function () {
        // The code you place here will be executed every time your command is executed
        // Display a message box to the user
        vscode.window.showInformationMessage('Hello from Coddy Extension!');
    });

    context.subscriptions.push(helloWorldDisposable);

    // Command: Coddy: Read File
    let readFileDisposable = vscode.commands.registerCommand('coddy.readFile', async () => {
        // MODIFIED: Get API_BASE_URL from VS Code configuration
        const config = vscode.workspace.getConfiguration('coddy');
        const API_BASE_URL = config.get('backendUrl', 'http://127.0.0.1:8000'); // Default fallback

        // Prompt the user for a file path
        const filePath = await vscode.window.showInputBox({
            prompt: 'Enter the file path to read (e.g., data/my_notes.txt)',
            placeHolder: 'e.g., src/main.py'
        });

        if (!filePath) {
            vscode.window.showInformationMessage('File path not provided.');
            return;
        }

        vscode.window.showInformationMessage(`Reading file: ${filePath}...`);

        try {
            const response = await fetch(`${API_BASE_URL}/api/files/read?path=${encodeURIComponent(filePath)}`);
            
            /** @type {CoddyApiResponse} */
            const data = await response.json();

            if (response.ok) {
                vscode.window.showInformationMessage(`Content of '${filePath}':\n---\n${data.content}\n---`);
            } else {
                // Handle API errors (e.g., 404 Not Found, 500 Internal Server Error)
                const errorMessage = data.detail || `Error: ${response.status} ${response.statusText}`;
                vscode.window.showErrorMessage(`Failed to read '${filePath}': ${errorMessage}`);
            }
        } catch (error) {
            // Handle network errors or other unexpected issues
            vscode.window.showErrorMessage(`An error occurred while connecting to Coddy API: ${error.message}`);
            console.error('Coddy Extension Error:', error);
        }
    });

    context.subscriptions.push(readFileDisposable);
}

// This method is called when your extension is deactivated
function deactivate() {}

module.exports = {
    activate,
    deactivate
}