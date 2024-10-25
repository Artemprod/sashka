from src.distributor.telegram_client.telethoncl.models.messages import OutcomeMessageDTOQueue


def create_outcome_message(event, sender, client_info) -> str:
    message = str(event.message.message)
    from_user = str(event.sender_id)
    user_name = str(sender.first_name) if sender.first_name else "Unknown"
    chat = str(event.chat_id)
    media = "None"
    voice = "None"
    client_telegram_id = str(client_info.id)

    outcome_message = OutcomeMessageDTOQueue(
        message=message,
        from_user=from_user,
        user_name=user_name,
        chat=chat,
        media=media,
        voice=voice,
        client_telegram_id=client_telegram_id
    ).json_string()

    return outcome_message
