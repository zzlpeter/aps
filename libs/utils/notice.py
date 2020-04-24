from libs.requests.ding_requests import DingDingAlarm


async def ding_ding_notice(msg):
    text = {
        'content': 'ALARM: {}'.format(msg)
    }
    server = DingDingAlarm(text=text).new_server()
    rsp = await server.async_fetch()
    return rsp.json()
