import redis
import json
from service.config import settings

local_redis = redis.Redis(host="localhost",port=6379,decode_responses=True)

MAX_TURNS_TO_KEEP = 10
TTL_SECONDS = settings.ttl_seconds

def _session_key(session_id:str) -> str:
    return f"session:{session_id}:turns" #make unique redis keys

def add_turns(session_id:str,role:str, content:str) -> None:
    "everytime anything happens this function is called"
    key = _session_key(session_id)
    turn = json.dumps({"role":role,"content":content}) # a string of role _> what is happening rn as tool call , llm call or whatev and content is the prompt or the response

    local_redis.rpush(key,turn)
    local_redis.ltrim(key, -MAX_TURNS_TO_KEEP, -1)
    local_redis.expire(key,TTL_SECONDS)


def get_recent_turns(session_id:str) ->list[dict]:
    key = _session_key(session_id)
    raw_turns = local_redis.lrange(key,0,-1) # all the keys for a perticular session id from first to last entries
    # return [json.loads(t) for t in raw_turns]  #coverting it into a list
    result = []
    for t in raw_turns:
        result.append(json.loads(t))
    return result

def clear_session(session_id:str) -> None:
    local_redis.delete(_session_key(session_id))

def build_prompt(session_id:str, task:str) -> str:
    recent_turns = get_recent_turns(session_id)

    lines = [f"Task:{task}"]
    if recent_turns:
        lines.append(f"\nRecent activity (last {len(recent_turns)} turns):")
        for t in recent_turns:
            lines.append(f"[{t['role']}] {t['content']}")
    return "\n".join(lines) #joins using newlines , into a string

