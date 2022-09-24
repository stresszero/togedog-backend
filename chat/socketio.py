import os
import socketio

import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "togedog_dj.settings")
django.setup()

from .mongodb import save_message
from cores.models import UserStatus
from cores.utils import censor_text
from users.models import User


sio = socketio.Server(
    async_mode="eventlet",
    cors_allowed_origins=settings.CORS_ALLOWED_ORIGINS,
)


@sio.event
def connect(sid, environ, auth):
    """
    socket.io 클라이언트가 연결되면 아래 코드를 실행한다
    - environ: http 헤더를 포함한 http 리퀘스트 데이터를 담는 WSGI 표준 딕셔너리
    - auth: 클라이언트에서 넘겨준 인증 데이터, 데이터가 없으면 None이 된다
    """
    user = User.objects.filter(id=auth["userId"])
    if not user.exists() or user.get().status == UserStatus.BANNED.value:
        return False


@sio.on("join")
def handle_join(sid, data):
    """
    유저가 인증을 통과하여 채팅방에 입장하면 아래 코드를 실행한다
    브라우저에서 채팅방 입장시 connect 이벤트를 거쳐서 join 이벤트가 발생한다
    - save_session(sid, data): 채팅방에 접속한 클라이언트의 sid를 기준으로 data를 세션 데이터로 저장
    """
    sio.save_session(sid, data)
    sio.enter_room(sid, room=data["room"])

    sio.emit(
        "add_message",
        {
            "user_nickname": "함께하개 관리자", 
            "text": f"{data['nickname']}님이 들어왔어요."
        },
        to=data["room"],
    )


@sio.on("send_message")
def handle_send_message(
    sid, message, nickname, room, currentTime, userMbti, userImage, userId
):
    """
    send_message 이벤트로 받은 데이터를 MongoDB에 저장하고 add_message로 emit한다
    - censor_text(): 욕설 필터링 함수, 채팅 메시지에 욕설이 있으면
    - 그 부분만 *으로 수정한 문자열을 반환함
    - save_message(): MongoDB에 메시지 데이터를 저장하고 고유한 ObjectId(24자리 문자열)반환
    """
    data = {
        "user_nickname": nickname,
        "user_id": userId,
        "user_mbti": userMbti,
        "user_image": userImage,
        "text": censor_text(message),
        "message_id": save_message(message, nickname, userId, room),
        "time": currentTime,
    }
    sio.emit("add_message", data, to=room)


@sio.event
def disconnect(sid):
    """
    socket.io 클라이언트가 연결 해제되면 아래 코드를 실행한다
    - get_session(sid): 위에서 save_session으로 저장한 sid별 세션 데이터 딕셔너리를 반환함
    - disconnected_username: 연결 해제된 sid의 유저 닉네임
    - room_number: 연결 해제된 sid가 있던 방 번호
    """
    disconnected_username = sio.get_session(sid).get("nickname", "")
    room_number = sio.get_session(sid).get("room")
    sio.emit(
        "add_message",
        {
            "user_nickname": "함께하개 관리자", 
            "text": f"{disconnected_username}님이 퇴장하셨어요."
        },
        to=room_number,
    )
