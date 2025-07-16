// Initialize Ace Editor
let editor = ace.edit("code-editor");
editor.setTheme("ace/theme/monokai");
editor.session.setMode("ace/mode/python");
editor.setOptions({
    fontSize: "14px",
    enableBasicAutocompletion: true,
    enableLiveAutocompletion: true,
    enableSnippets: true
});

// State management
let inputQueue = [];
let isWaitingForInput = false;
let currentInputField = null;

// Dark Mode Toggle (update initial button text)
const themeToggle = document.getElementById('theme-toggle');
themeToggle.innerHTML = '<span class="theme-icon">☀️</span>Light Mode';

themeToggle.addEventListener('click', () => {
    document.body.classList.toggle('dark');
    const isDark = document.body.classList.contains('dark');
    editor.setTheme(isDark ? "ace/theme/monokai" : "ace/theme/github");
    themeToggle.innerHTML = `<span class="theme-icon">${isDark ? '☀️' : '🌙'}</span>${isDark ? 'Light Mode' : 'Dark Mode'}`;
});

// Language mode mapping
const modeMap = {
    'python': 'python',
    'c': 'c_cpp',
    'cpp': 'c_cpp',
    'java': 'java'
};

function updateEditorMode(language) {
    editor.session.setMode(`ace/mode/${modeMap[language] || 'text'}`);
}

// Add to app.js
function loadBoilerplate(language) {
    fetch(`https://abhishek8040.pythonanywhere.com/get_boilerplate?language=${language}`)
        .then(response => response.json())
        .then(data => {
            editor.setValue(data.code);
            editor.clearSelection();
        });
}

// Add download button handler
function downloadCode() {
    const language = document.getElementById('language-select').value;
    const code = editor.getValue();

    fetch('https://abhishek8040.pythonanywhere.com/download_code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            language: language,
            code: code
        }),
    })
    .then(response => response.json())
    .then(data => {
        const blob = new Blob([data.content], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
    });
}

// Event Listeners
document.getElementById('language-select').addEventListener('change', (e) => {
    const language = e.target.value;
    updateEditorMode(language);
    loadBoilerplate(language);
});

document.getElementById('clear-editor').addEventListener('click', () => {
    editor.setValue('');
    document.getElementById('output-console').innerHTML = '';
    inputQueue = [];
    isWaitingForInput = false;
    if (currentInputField) {
        currentInputField.remove();
        currentInputField = null;
    }
});

document.getElementById('run-code').addEventListener('click', runCodeHandler);

// Add to app.js
document.getElementById('download-code').addEventListener('click', downloadCode);

// Add after existing event listeners

document.getElementById('improve-code').addEventListener('click', improveCode);
document.getElementById('generate-code').addEventListener('click', toggleChatBox);
document.getElementById('close-chat').addEventListener('click', toggleChatBox);
document.getElementById('send-message').addEventListener('click', sendMessage);
document.getElementById('chat-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

document.getElementById('generate-code').addEventListener('click', showGenerateCodeDialog);
document.getElementById('close-chat').addEventListener('click', hideGenerateCodeDialog);

document.getElementById('improve-code').addEventListener('click', improveCode);
document.getElementById('generate-code').addEventListener('click', showGenerateCodeDialog);
document.getElementById('close-chat').addEventListener('click', hideGenerateCodeDialog);
document.getElementById('send-message').addEventListener('click', sendMessage);
document.getElementById('chat-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendMessage();
});

function runCodeHandler() {
    const language = document.getElementById('language-select').value;
    const code = editor.getValue();
    inputQueue = [];
    isWaitingForInput = false;
    if (currentInputField) {
        currentInputField.remove();
        currentInputField = null;
    }
    document.getElementById('output-console').innerHTML = '';
    runCode(language, code);
}

// Update runCode function in app.js

function runCode(language, code) {
    const consoleDiv = document.getElementById('output-console');
    consoleDiv.classList.add('loading');

    // Clear previous state
    isWaitingForInput = false;
    if (currentInputField) {
        currentInputField.remove();
        currentInputField = null;
    }

    fetch('https://abhishek8040.pythonanywhere.com/run_code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            language: language,
            code: code,
            inputs: inputQueue
        }),
    })
    .then(response => response.json())
    .then(data => {
        consoleDiv.classList.remove('loading');

        if (data.output) {
            // Clear previous output if this is a fresh run
            if (inputQueue.length === 0) {
                consoleDiv.innerHTML = '';
            }
            addToConsole(data.output);
        }

        if (data.error && !data.input_required) {
            addToConsole(`<span class="error">${data.error}</span>`);
            return;
        }

        if (data.input_required && !isWaitingForInput) {
            promptForInput();
        }
    })
    .catch(error => {
        consoleDiv.classList.remove('loading');
        addToConsole(`<span class="error">Error: ${error.message}</span>`);
    });
}

// Update promptForInput function
function promptForInput() {
    if (isWaitingForInput) return;

    isWaitingForInput = true;
    const consoleDiv = document.getElementById('output-console');

    const inputContainer = document.createElement('div');
    inputContainer.className = 'input-container';

    const inputField = document.createElement('input');
    inputField.type = 'text';
    inputField.className = 'console-input';
    inputContainer.appendChild(inputField);

    consoleDiv.appendChild(inputContainer);
    currentInputField = inputContainer;
    inputField.focus();

    scrollToBottom();

    inputField.addEventListener('keydown', (e) => {
        if (e.key === "Enter") {
            const userInput = inputField.value;
            inputQueue.push(userInput);
            isWaitingForInput = false;
            inputContainer.remove();
            currentInputField = null;
            addToConsole(userInput);

            const language = document.getElementById('language-select').value;
            const code = editor.getValue();
            runCode(language, code);
        }
    });
}

function addToConsole(message) {
    const consoleDiv = document.getElementById('output-console');
    const messageElement = document.createElement('div');
    messageElement.className = 'console-message';
    messageElement.innerHTML = message;
    consoleDiv.appendChild(messageElement);
    scrollToBottom();
}

function scrollToBottom() {
    const consoleDiv = document.getElementById('output-console');
    consoleDiv.scrollTop = consoleDiv.scrollHeight;
}

// Initialize editor mode
updateEditorMode(document.getElementById('language-select').value);

// Load initial boilerplate
loadBoilerplate(document.getElementById('language-select').value);

function toggleChatBox() {
    document.getElementById('ai-chat-container').classList.toggle('hidden');
}

// Update improveCode function in app.js
function improveCode() {
    const language = document.getElementById('language-select').value;
    const code = editor.getValue();

    if (!code.trim()) {
        addToConsole(`<span class="error">No code to analyze</span>`);
        return;
    }

    // Show loading state in chat panel
    const chatMessagesDiv = document.getElementById('chat-messages');
    chatMessagesDiv.innerHTML = '<div class="loading">AI is analyzing your code...</div>';
    showGenerateCodeDialog();

    fetch('https://abhishek8040.pythonanywhere.com/improve_code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            language: language,
            code: code
        }),
    })
    .then(response => response.json())
    .then(data => {
        chatMessagesDiv.classList.remove('loading');
        if (data.suggestions) {
            chatMessagesDiv.innerHTML = '';
            chatMessagesDiv.innerHTML = data.suggestions;
        } else {
            chatMessagesDiv.innerHTML = '<span class="error">No suggestions provided by AI.</span>';
        }
    })
    .catch(error => {
        chatMessagesDiv.classList.remove('loading');
        chatMessagesDiv.innerHTML = `<span class="error">Error analyzing code: ${error}</span>`;
    });
}

function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    const language = document.getElementById('language-select').value;

    if (!message) return;

    addMessage(message, 'user');
    input.value = '';

    fetch('https://abhishek8040.pythonanywhere.com/generate_code', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            prompt: message,
            language: language
        }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.code) {
            addGeneratedCode(data.code, data.language);
        } else {
            addMessage('Sorry for inconvinience... Huggingface API Server Down...!  Check again later...or You can use Chat button for now...', 'ai');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        addMessage('Error generating code', 'ai');
    });
}

function addMessage(message, type) {
    const messagesDiv = document.getElementById('chat-messages');
    const messageElement = document.createElement('div');
    messageElement.className = `chat-message ${type}-message`;
    messageElement.textContent = message;
    messagesDiv.appendChild(messageElement);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function showGenerateCodeDialog() {
    const dialog = document.getElementById('ai-chat-container');
    dialog.classList.remove('hidden');

    // Clear previous messages
    document.getElementById('chat-messages').innerHTML = '';

    // Focus on input
    document.getElementById('chat-input').focus();
}

function hideGenerateCodeDialog() {
    document.getElementById('ai-chat-container').classList.add('hidden');
}

function addGeneratedCode(code, language) {
    const messagesDiv = document.getElementById('chat-messages');
    const codeContainer = document.createElement('div');
    codeContainer.className = 'generated-code-container';

    // Add transfer button
    const transferBtn = document.createElement('button');
    transferBtn.className = 'transfer-code-btn';
    transferBtn.innerHTML = '⇪ Transfer to Editor';
    transferBtn.onclick = () => {
        editor.setValue(code);
        editor.clearSelection();
        editor.session.setMode(`ace/mode/${modeMap[language] || 'text'}`);
        hideGenerateCodeDialog();
    };

    // Add code display
    const codeDisplay = document.createElement('pre');
    codeDisplay.className = 'code-display';
    codeDisplay.textContent = code;

    codeContainer.appendChild(transferBtn);
    codeContainer.appendChild(codeDisplay);
    messagesDiv.appendChild(codeContainer);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}