from ninja import Router

from cores.schemas import MessageOut
from chat.models import ChatReport
from chat.schemas import ChatReportIn
from users.auth import AuthBearer, has_authority

router = Router(tags=["채팅 관련 API"], auth=AuthBearer())

@router.post("/report", response=MessageOut)
def report_chat_message(request, body: ChatReportIn):
    '''
    채팅 신고하기
    '''
    has_authority(request)
    body_dict = body.dict()
    # check message exists in mongodb before create
    ChatReport.objects.create(reporter_user_id=request.auth.id, **body_dict)
    return {"message": "success"}