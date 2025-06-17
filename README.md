# Guess the Number Game with Razorpay Payment

This project implements a simple command-line "Guess the Number" game written in Rust,
which requires a payment of 1 INR via Razorpay before playing. The payment handling
is done by a separate Python Flask web service.

## Components

1.  **Rust CLI Game (`src/main.rs`):**
    *   The core guessing game.
    *   Communicates with the payment service to verify payment before allowing access.

2.  **Python Flask Payment Service (`payment_service/`):**
    *   Handles Razorpay integration.
    *   Provides an endpoint for users to initiate payment.
    *   Provides a callback endpoint for Razorpay to confirm payment.
    *   Generates a game token upon successful payment.
    *   Provides an endpoint for the Rust game to verify the game token.

## Prerequisites

*   **Rust:** Version 1.75.0 or newer. Install from [https://www.rust-lang.org/tools/install](https://www.rust-lang.org/tools/install).
*   **Python:** Version 3.7 or newer. Install from [https://www.python.org/downloads/](https://www.python.org/downloads/).
*   **Pip:** Python package installer (usually comes with Python).
*   **Razorpay Account:** You will need Razorpay API Key ID and Key Secret. Get them from your Razorpay Dashboard.

## Setup and Configuration

### 1. Configure Payment Service (Flask App)

*   **Navigate to the payment service directory:**
    ```bash
    cd payment_service
    ```

*   **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: The `app.py` script also has a fallback to attempt installation if packages are missing when it runs, but it's best to install them explicitly.)*

*   **Set Razorpay API Keys:**
    The application reads Razorpay keys from environment variables.
    Set the following environment variables:
    ```bash
    export RAZORPAY_KEY_ID="YOUR_RAZORPAY_KEY_ID"
    export RAZORPAY_KEY_SECRET="YOUR_RAZORPAY_KEY_SECRET"
    ```
    Replace `"YOUR_RAZORPAY_KEY_ID"` and `"YOUR_RAZORPAY_KEY_SECRET"` with your actual Razorpay test or live keys.
    **Important:** The application will show a warning if placeholder keys are used from the `app.py` file. For real transactions, environment variables are recommended.

### 2. Rust CLI Game

*   No specific configuration is needed for the game itself, other than having Rust and Cargo installed. It is pre-configured to connect to the payment service at `http://localhost:5001`.

## How to Run

1.  **Start the Payment Service:**
    *   Open a terminal, navigate to the `payment_service` directory.
    *   Ensure your Razorpay API keys are set as environment variables (see Setup).
    *   Run the Flask app:
        ```bash
        python app.py
        ```
    *   The service will start, typically on `http://localhost:5001`. You should see output like:
        `* Running on http://0.0.0.0:5001/`
        `* Debug mode: on`
        `WARNING: Razorpay API keys are set to placeholders...` (if you haven't set env vars)

2.  **Compile and Run the Rust Game:**
    *   Open another terminal.
    *   Navigate to the root directory of this project (where `Cargo.toml` is).
    *   Build and run the game:
        ```bash
        cargo run
        ```
    *   The game will first compile and then start.

## Payment and Gameplay Flow

1.  When you run the Rust game, it will instruct you to make a payment.
2.  Open your web browser and go to the URL provided by the game (e.g., `http://localhost:5001/pay`).
3.  This page, served by the Flask payment service, will redirect you to Razorpay to complete a 1 INR payment. You can use Razorpay's test card details for this.
4.  Upon successful payment, Razorpay will redirect you back to a success page from the Flask service. This page will display your unique **game token**.
5.  Copy this game token.
6.  Paste the token into the Rust CLI game when prompted.
7.  The Rust game will verify the token with the Flask service.
8.  If the token is valid, the "Guess the Number" game will begin!

## Notes

*   The payment service uses an in-memory dictionary to store payment order details and tokens. This means if the Python Flask service restarts, all payment records and generated tokens will be lost. For a production system, a persistent database (e.g., SQLite, PostgreSQL) would be necessary.
*   The Rust game connects to `localhost:5001`. If your payment service runs on a different host or port, you'll need to update the `payment_service_host` and `payment_service_port` variables in `src/main.rs` and recompile.
