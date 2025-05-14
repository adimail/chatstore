import logging
import asyncio
from flask import request, jsonify, current_app, render_template, flash
from flask_login import login_required, current_user
from . import chatbot_bp
from app.services import chatbot_service

logger = logging.getLogger(__name__)

INITIAL_CHAT_LIMIT = 50


@chatbot_bp.route("/chat", methods=["POST"])
@login_required
def handle_chat_message():
    """
    API endpoint to handle incoming chat messages from the user via AJAX.
    """
    if not request.is_json:
        logger.warning("Non-JSON request received at /chat endpoint.")
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    user_message = data.get("message")

    if not user_message:
        logger.warning("Missing 'message' in JSON payload for /chat.")
        return jsonify({"error": "Missing 'message' in request body"}), 400

    user_id = current_user.id
    api_key = current_app.config.get("GOOGLE_API_KEY")

    if not api_key:
        logger.error("GOOGLE_API_KEY is not configured in the application.")
        return (
            jsonify({"error": "Chatbot service is not configured (API key missing)."}),
            500,
        )

    logger.info(f"Received chat message from user {user_id}: '{user_message}'")
    try:
        agent_response = asyncio.run(
            chatbot_service.handle_message_async(
                user_id=user_id, user_message=user_message, api_key=api_key
            )
        )
        logger.info(f"Sending response to user {user_id}: '{agent_response}'")
        return jsonify({"response": agent_response})
    except Exception as e:
        logger.error(
            f"Unhandled exception in handle_chat_message for user {user_id}: {e}",
            exc_info=True,
        )
        return (
            jsonify({"error": "An internal error occurred processing your message."}),
            500,
        )


@chatbot_bp.route("/", methods=["GET"])
@login_required
def chat_interface_page():
    """
    Renders the main chat interface page, loading initial chat history for the sidebar.
    """
    user_id = current_user.id
    logger.info(f"Loading chat interface for user {user_id}.")

    chat_history_list_for_sidebar = []
    total_messages = 0

    try:
        # Fetch latest messages for the sidebar, ordered descending (latest first)
        chat_history_list_for_sidebar = chatbot_service.get_chat_history(
            user_id, limit=INITIAL_CHAT_LIMIT, offset=0
        )
        total_messages = chatbot_service.count_chat_history(user_id)
        logger.debug(
            f"Loaded {len(chat_history_list_for_sidebar)} of {total_messages} messages for user {user_id} for sidebar."
        )
    except Exception as e:
        logger.error(
            f"Failed to load chat history for user {user_id} in route: {e}",
            exc_info=True,
        )
        flash("Could not load previous chat history.", "warning")

    return render_template(
        "chatbot/chat.html.jinja2",
        title="Chat",
        # This history is ONLY for the sidebar initial load
        chat_history_for_sidebar=chat_history_list_for_sidebar,
        total_messages=total_messages,
        loaded_messages_count=len(chat_history_list_for_sidebar),
        initial_limit=INITIAL_CHAT_LIMIT,
    )


@chatbot_bp.route("/load_more_chats", methods=["GET"])
@login_required
def load_more_chats():
    user_id = current_user.id
    offset = request.args.get("offset", 0, type=int)

    logger.info(f"Loading more chats for user {user_id} with offset {offset}.")
    try:
        # Fetches older messages, still ordered latest first within the batch
        more_messages = chatbot_service.get_chat_history(
            user_id, limit=INITIAL_CHAT_LIMIT, offset=offset
        )
        messages_data = [
            {
                "id": msg.id,
                "sender": msg.sender.value,
                "message_text": msg.message_text,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in more_messages
        ]
        # Client side will append these to the bottom of the sidebar
        return jsonify(
            {
                "messages": messages_data,
                "has_more": len(more_messages) == INITIAL_CHAT_LIMIT,
            }
        )
    except Exception as e:
        logger.error(
            f"Failed to load more chats for user {user_id}: {e}", exc_info=True
        )
        return jsonify({"error": "Could not load more messages."}), 500


@chatbot_bp.route("/clear_history", methods=["POST"])
@login_required
def clear_chat_history_route():
    user_id = current_user.id
    logger.info(f"Clearing chat history for user {user_id}.")
    try:
        success = chatbot_service.clear_chat_history(user_id)
        if success:
            chatbot_service.clear_user_runner_cache(user_id)
            logger.info(f"Chat history cleared successfully for user {user_id}.")
            return jsonify({"success": True, "message": "Chat history cleared."})
        else:
            logger.warning(
                f"Failed to clear chat history for user {user_id} (service returned false)."
            )
            return (
                jsonify({"success": False, "message": "Failed to clear chat history."}),
                500,
            )
    except Exception as e:
        logger.error(
            f"Exception while clearing chat history for user {user_id}: {e}",
            exc_info=True,
        )
        return (
            jsonify(
                {
                    "success": False,
                    "message": "An error occurred while clearing history.",
                }
            ),
            500,
        )
