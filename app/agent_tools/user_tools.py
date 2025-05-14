from app.models import User


def get_user_profile_info_executor(user_id: int) -> str:
    """
    Retrieves and formats basic profile information for the current user, such as their name and join date.
    Use this tool when the user asks "who am I?", "what's my name?", "when did I join?", or similar questions about their own account details.

    Args:
        user_id: The ID of the current user.

    Returns:
        A string containing the user's name and join date, or a message if the user is not found.
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return "I'm sorry, I couldn't find your profile information. This is unexpected. Please ensure you are logged in correctly."

        join_date_formatted = user.created_at.strftime("%B %d, %Y")
        return f"Your name is {user.name}, and you joined ChatStore on {join_date_formatted}."
    except Exception:
        return "I encountered an issue while trying to retrieve your profile information. Please try again later."
