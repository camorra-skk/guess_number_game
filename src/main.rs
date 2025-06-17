use std::{
    io::{self, Read, Write},
    net::TcpStream,
    cmp::Ordering,
};
use rand::Rng;

// Define the structure for the expected JSON response
#[derive(serde::Deserialize, Debug)]
struct VerifyResponse {
    status: String,
    message: Option<String>,
    order_id: Option<String>,
}

fn verify_payment_token(token: &str, payment_service_host: &str, payment_service_port: u16) -> Result<bool, String> {
    let token = token.trim();
    let request_path = format!("/verify_token?token={}", token);

    // Attempt to connect
    let stream_result = TcpStream::connect(format!("{}:{}", payment_service_host, payment_service_port));
    let mut stream = match stream_result {
        Ok(s) => s,
        Err(e) => return Err(format!("Failed to connect to payment service: {}", e)),
    };

    // Construct HTTP GET request
    let http_request = format!(
        "GET {} HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n",
        request_path, payment_service_host
    );

    // Send the request
    if let Err(e) = stream.write_all(http_request.as_bytes()) {
        return Err(format!("Failed to send request: {}", e));
    }

    // Read the response
    let mut buffer = Vec::new();
    if let Err(e) = stream.read_to_end(&mut buffer) {
        return Err(format!("Failed to read response: {}", e));
    }

    let response_str = String::from_utf8_lossy(&buffer);

    // Very basic HTTP response parsing: find the body
    // This assumes no chunked encoding and simple responses.
    if let Some(body_start_index) = response_str.find("\r\n\r\n") {
        let header_part = &response_str[..body_start_index];
        // Check status code in header (simplified)
        if !header_part.starts_with("HTTP/1.1 200 OK") {
             // Try to get status line for more info
            let status_line = header_part.lines().next().unwrap_or("Unknown status");
            // Try to parse JSON body for error message if present
            let body_str = &response_str[body_start_index + 4..];
            if let Ok(json_response) = serde_json::from_str::<VerifyResponse>(body_str) {
                 let msg = json_response.message.unwrap_or_else(|| "Server returned an error.".to_string());
                 return Err(format!("Token verification failed: {} (Status: {})", msg, status_line));
            }
            return Err(format!("Server returned an error (Status: {})", status_line));
        }

        let body_str = &response_str[body_start_index + 4..]; // Skip \r\n\r\n



        match serde_json::from_str::<VerifyResponse>(body_str) {
            Ok(json_response) => {
                if json_response.status == "valid" {
                    Ok(true)
                } else {
                    let msg = json_response.message.unwrap_or_else(|| "Token is not valid.".to_string());
                    Err(format!("Token verification failed: {}", msg))
                }
            }
            Err(e) => Err(format!("Failed to parse JSON response: {} (Body: '{}')", e, body_str)),
        }
    } else {
        Err("Invalid HTTP response format".to_string())
    }
}

fn main() {
    // Payment service configuration
    // Assuming payment service is running on localhost:5001
    let payment_service_host = "localhost";
    let payment_service_port = 5001;
    let payment_service_pay_url = format!("http://{}:{}/pay", payment_service_host, payment_service_port);

    println!("--- Payment Required to Play ---");
    println!("Please make a payment of 1 INR to play the game.");
    println!("1. Open your web browser and go to: {}", payment_service_pay_url);
    println!("2. Complete the payment process.");
    println!("3. You will receive a game token. Enter it below.");

    loop {
        println!("\nPlease enter your game token:");
        let mut token_input = String::new();
        io::stdin().read_line(&mut token_input).expect("Failed to read token");
        let token = token_input.trim();

        if token.is_empty() {
            println!("Token cannot be empty. Please try again.");
            continue;
        }

        println!("Verifying your token with {}:{}...", payment_service_host, payment_service_port);
        match verify_payment_token(token, payment_service_host, payment_service_port) {
            Ok(true) => {
                println!("Token verified successfully! Welcome to the game.");
                break;
            }
            Ok(false) => {
                println!("Token is invalid. Please check your token and try again.");
            }
            Err(e) => {
                println!("Error verifying token: {}", e);
                println!("Please ensure the payment service is running at {}:{} and your token is correct.", payment_service_host, payment_service_port);
                println!("Do you want to try entering the token again? (yes/no)");
                let mut retry_input = String::new();
                io::stdin().read_line(&mut retry_input).expect("Failed to read input");
                if retry_input.trim().to_lowercase() != "yes" {
                    println!("Exiting game.");
                    return;
                }
            }
        }
    }

    // Original Game Logic
    println!("\n--- Welcome to Guess a number Game ---");
    println!("I've picked a number between 1 and 100. Try to guess it!");

    let secret_number = rand::thread_rng().gen_range(1..=100);

    loop {
        println!("\nEnter your guess:");
        let mut guess_str = String::new();
        io::stdin().read_line(&mut guess_str).expect("Failed to read line");

        let guess: u32 = match guess_str.trim().parse() {
            Ok(num) => num,
            Err(_) => {
                println!("Please enter a valid number!");
                continue;
            }
        };
        
        println!("You guessed: {}", guess);

        match guess.cmp(&secret_number) {
            Ordering::Less => println!("Too small! Try a larger number."),
            Ordering::Greater => println!("Too big! Try a smaller number."),
            Ordering::Equal => {
                println!("🎉 Congratulations! You guessed the number! 🎉");
                break;
            }
        }
    }
}
