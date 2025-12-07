# 📧 Gmail Summarization & Analysis (Groq LLM)

This is a Streamlit application designed to fetch your Gmail emails for a specific day and generate a consolidated, structured summary using a high-speed Large Language Model (LLM) from **Groq**. It leverages **LangChain Expression Language (LCEL)** to implement a robust Map-Reduce summarization strategy, ensuring complex email threads are handled effectively.

-----

## ✨ Features

  * **Gmail Integration:** Securely authenticates with the Gmail API using Google OAuth to fetch emails for a specific date.
  * **Groq LLM Powered:** Uses the Groq API for ultra-fast text summarization.
  * **LangChain Map-Reduce:** Implements a Map-Reduce summarization pattern using LCEL to handle a large volume of email content and produce a coherent final summary.
  * **Structured Output:** The final summary is highly organized with bullet points under headings: Main Topics Discussed, Key Action Items, and Senders and Dates.
  * **Streamlit UI:** Provides an easy-to-use web interface for date selection and viewing the results.
  * **Token Management:** Handles Gmail API access token refreshing and storage via `token.json`.

-----

## 🛠️ Prerequisites

Before running the application, you must complete the following setup steps.

### 1\. Python Environment

Ensure you have Python 3.9+ installed.

### 2\. Install Dependencies

The required packages are listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

[cite_start]The dependencies include `streamlit`, `langchain-groq`, `google-api-python-client`, and others[cite: 1].

### 3\. Google API Credentials

This app uses the Google OAuth 2.0 flow for **Installed Applications** (desktop/CLI).

  * **Create a Google Cloud Project:** Set up a project in Google Cloud Console.
  * **Enable Gmail API:** Ensure the **Gmail API** is enabled for your project.
  * **Create Credentials:**
      * Go to **APIs & Services -\> Credentials**.
      * Click **Create Credentials -\> OAuth client ID**.
      * Select **Application type: Desktop app**.
      * Download the JSON file and rename it to `credentials.json` in the root of your project directory.

### 4\. Groq API Key

  * Get an API key from the [Groq Console](https://console.groq.com/).

  * The application uses the key defined in `config.py`:

    ```python
    # config.py
    GROQ_API_KEY = "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" 
    MODEL_NAME = "groq/compound-mini" 
    ```

### 5\. Authentication Files

The `gmail_fetcher.py` script requires two files to manage authentication:

1.  `credentials.json`: Your downloaded Google API client secret file.
2.  `token.json`: Automatically generated and updated after the first successful sign-in, storing your access and refresh tokens.

-----

## 🚀 How to Run

1.  Place the `credentials.json` file and all Python scripts (`app.py`, `config.py`, `gmail_fetcher.py`, `qa_engine.py`) in the same directory.

2.  Run the Streamlit application from your terminal:

    ```bash
    streamlit run app.py
    ```

3.  **Initial Authentication:** On the first run, the app will open a browser window and ask you to sign in with your Google account and grant the `https://www.googleapis.com/auth/gmail.readonly` scope. Once authorized, the `token.json` file will be created, and subsequent runs will be faster.

4.  **Use the UI:** Select a date and click **"Fetch & Summarize Emails"** to start the process.

-----

## 📂 Project Structure

| File | Description |
| :--- | :--- |
| `app.py` | The main Streamlit interface. Manages the UI, user input, session state, and coordinates the fetching and summarization pipeline. |
| `config.py` | Configuration file holding the Groq API key, model names, and Gmail API scopes/credentials path. |
| `gmail_fetcher.py` | Handles Google OAuth, token management, and fetching/decoding of Gmail messages for a specified date range. |
| `qa_engine.py` | Contains the `QAEngine` class. It sets up the Groq LLM and the LCEL Map-Reduce chain for robust email summarization. |
| `requirements.txt` | [cite_start]Lists all necessary Python dependencies[cite: 1]. |
| `test.py` | A simple script to verify that the Groq API key and model connection are working correctly. |
| `credentials.json` | **REQUIRED** Your Google OAuth client secrets file (Do NOT commit to public repos\!). |
| `token.json` | **Generated** Stores the user's access/refresh tokens for persistent Gmail access (Do NOT commit to public repos\!). |
