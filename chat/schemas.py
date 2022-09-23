from ninja import Schema

class ChatReportIn(Schema):
    reported_user_id: int    
    message_id: str
    message_text: str
    content: str