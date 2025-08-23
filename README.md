
# 🌐 Online Code Compiler

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen?style=for-the-badge)](https://abhishek8040.pythonanywhere.com)

🔗 **Live Demo:** [Click here to try it!] (https://abhishek8040.pythonanywhere.com)



A powerful and simple **web-based code compiler** that supports multiple programming languages like **Python, C, C++, Java**, and more. Users can write, compile, and run code directly in the browser — with real-time suggestions and AI-powered code generation.

---

## 🚀 Features

- ✅ **Multi-language Support** – Compile and run Python, C, C++, and Java code.
- ✍️ **Online Editor** – Write and edit code using a responsive, browser-based editor.
- ⚡ **Real-time Code Suggestions** – Get syntax hints and code improvements as you type.
- 🤖 **AI Code Generation** – Generate starter code or snippets using integrated HuggingFace APIs.
- 🌐 **No Installation Needed** – Fully online and accessible from any device.
- 🔐 **Safe Execution Environment** – Isolated backend execution (via Docker or safe subprocess).

---

## 🛠 Tech Stack

| Layer        | Technology          |
|--------------|---------------------|
| **Frontend** | HTML, CSS, JavaScript, [CodeMirror](https://codemirror.net/) or Monaco Editor |
| **Backend**  | Python, Flask        |
| **Compiler APIs** | Custom Flask routes or third-party APIs like JDoodle, HackerEarth API, etc. |
| **HuggingFace API** | Huggingface APIs for code generation |

---

## 📷 Demo

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen?style=for-the-badge)](https://abhishek8040.pythonanywhere.com)

🔗 **Live Demo:** [Click here to try it!] (https://abhishek8040.pythonanywhere.com)

Try writing and running code directly in your browser!

---



## 🧑‍💻 How to Run Locally

```bash
# Clone the repository
git clone https://github.com/your-username/online-code-compiler.git
cd online-code-compiler

# Create a virtual environment and activate it
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Add your HuggingFace API Key in the given field of app.py

replace the api key with your own HF api key


# Install dependencies
pip install -r requirements.txt

# Run the Flask app
python app.py
````

Open your browser and go to `http://localhost:5000`

---



## 📁 Project Structure

```
online-code-compiler/
├── static/
│   └── js, css files
├── templates/
│   └── index.html
├── app.py
├── compiler.py
├── requirements.txt
└── README.md
```

---



## 💡 Future Enhancements

* [ ] Add user authentication (Login/Signup)
* [ ] Fixing problems related to User's Input 
* [ ] Enhance Generative AI Chat
* [ ] Support for more languages (e.g., JavaScript, Go, Ruby)

---

## 🙌 Contributions

Feel free to fork this repo, open issues, or submit pull requests. All contributions are welcome!

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 👤 Author

**Abhishek Dubey**
📧 \[[abhishekdubey8040@gmail.com](mailto:abhishekdubey8040@gmail.com)]
🔗 [LinkedIn](https://www.linkedin.com/in/abhishekdubey-) • [Portfolio](https://abhishek8040.github.io/portfolio/)

---

```

Let me know if you'd like help customizing the demo image link, contribution guidelines, or adding an actual deployment (e.g., on Render or Vercel).
```
