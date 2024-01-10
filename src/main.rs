use std::{io, cmp::Ordering};

use rand::Rng;
fn main() {
    println!("Welcome to Guess a number Game");
    println!("Enter your number");

    // The :: syntax in the ::new line indicates that new is an associated function of the String type.
    // An associated function is a function that’s implemented on a type, in this case String. 

    let secret_number = rand::thread_rng().gen_range(1..=100);

    println!("Secret Number is {}",secret_number);

    loop {
        let mut guess = String::new();
        io::stdin().read_line(&mut guess).expect("Failed to read line");

        let guess: u32 = match guess.trim().parse() {
            Ok(num) => num,
            Err(_) => continue
        };
        
        println!("You guessed {}",guess);

        match guess.cmp(&secret_number) {
            Ordering::Less => println!("Too small"),
            Ordering::Equal => {
                println!("You win");
                break;
            }
            Ordering::Greater => println!("Too big")
        }
    }
    


}
