from ninja import Router

from cores.schemas import MessageOut
from chat.models import ChatReport
from chat.schemas import ChatReportIn
from users.auth import AuthBearer, has_authority

from .mongodb import get_message

router = Router(tags=["채팅 관련 API"], auth=AuthBearer())


@router.post(
    "/report", response={200: MessageOut, 400: MessageOut}, summary="채팅 메시지 신고하기"
)
def report_chat_message(request, body: ChatReportIn):
    """
    채팅 신고하기(application/json)
    - reported_user_id: 신고받는 유저의 id값(socket.io 통신으로 처리)
    - message_id: 신고하는 메시지의 id값(백엔드 통신 과정에서 처리)
    - message_text: 신고하는 메시지의 내용(프론트엔드에서 받음)
    - content: 입력한 신고 사유(프론트엔드에서 받음)
    """
    message_data = get_message(body.message_id)
    if not message_data:
        return 400, {"message": "message not found"}
    has_authority(request, user_id=message_data["sender_id"], self_check=True)
    ChatReport.objects.create(reporter_user_id=request.auth.id, **body.dict())
    return 200, {"message": "success"}
