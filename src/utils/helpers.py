def format_message(user_id, message):
    return f"User {user_id} says: {message}"

def handle_error(error):
    print(f"An error occurred: {error}")

def validate_input(user_input):
    return isinstance(user_input, str) and len(user_input) > 0