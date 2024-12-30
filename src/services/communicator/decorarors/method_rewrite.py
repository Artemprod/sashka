import json


def create_publish_message(cls):
    async def new_method(self, content, user, client, destination_configs):
        data = {"message": content.response, "tg_client": str(client.name), "user": user.dict()}
        return self.publisher.form_stream_message(
            message=json.dumps(data), subject=destination_configs.subject, stream=destination_configs.stream
        )

    cls._create_publish_message = new_method
    return cls
