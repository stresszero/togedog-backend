from ninja import Router

from cores.schemas import MessageOut
from chat.models import ChatReport
from chat.schemas import ChatReportIn
from users.auth import AuthBearer, has_authority

from .mongodb import get_message

router = Router(tags=["채팅 관련 API"], auth=AuthBearer())

@router.post("/report", response=MessageOut, summary='채팅 메시지 신고하기')
def report_chat_message(request, body: ChatReportIn):
    '''
    채팅 신고하기(application/json)
    - reported_user_id: 신고받는 유저의 id값(socket.io 통신으로 처리)
    - message_id: 신고하는 메시지의 id값(백엔드 통신 과정에서 처리)
    - message_text: 신고하는 메시지의 내용(프론트엔드가 넘겨줌)
    - content: 입력한 신고 사유(프론트엔드가 넘겨줌)
    '''
    has_authority(request)
    if not get_message(body.message_id):
        return 400, {"message": "message not found"}
    ChatReport.objects.create(reporter_user_id=request.auth.id, **body.dict())
    return {"message": "success"}