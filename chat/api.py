from ninja import Router

from chat.models import ChatReport
from chat.schemas import ChatReportIn
from cores.schemas import MessageOut
from users.auth import AuthBearer, has_authority

from .mongodb import get_message

router = Router(tags=["채팅 관련 API"], auth=AuthBearer())


@router.post(
    "/report",
    response={200: MessageOut, 400: MessageOut},
    summary="채팅 메시지 신고하기",
)
def report_chat_message(request, body: ChatReportIn):
    """
    채팅 신고하기
    application/json 형식
        - reported_user_id: 신고받는 유저의 id
        - message_id: 신고하는 메시지의 id
        - message_text: 신고하는 메시지의 내용
        - content: 유저가 입력한 신고 사유
    신고하는 메시지가 MongoDB에 없으면 400에러 반환
    신고 권한 체크 후 채팅신고 처리
    """
    message_data = get_message(body.message_id)
    if not message_data:
        return 400, {"message": "message not found"}

    has_authority(request, user_id=message_data["sender_id"], self_check=True)
    ChatReport.objects.create(reporter_user_id=request.auth.id, **body.dict())
    return 200, {"message": "success"}
