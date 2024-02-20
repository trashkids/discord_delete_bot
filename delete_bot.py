import discord
import asyncio
import re
from typing import List

TOKEN = 'MTIwMDI4OTYwMzgxMTI5MTE5Nw.G9cF10.prmq2MuaHHsI6FoY6Y7fnI2LblBpuelBdHLNCM'  # あなたのDiscordボットのトークンをここに入れてください

client = discord.Client(intents=discord.Intents.default())

# 削除対象となるメッセージの情報
class DeleteMessageInfo:
    def __init__(self, channel_id: int, message_id: int, delete_time: int):
        self.channel_id = channel_id
        self.message_id = message_id
        self.delete_time = delete_time

# 削除処理のタスク
async def delete_message_task(message_info: DeleteMessageInfo):
    try:
        channel = client.get_channel(message_info.channel_id)
        await channel.delete_messages([discord.Object(id=message_info.message_id)])
    except discord.errors.NotFound:
        print(f"メッセージID {message_info.message_id} が見つかりません")
    except discord.errors.Forbidden:
        print(f"チャンネルID {message_info.channel_id} にアクセスできません")

# 削除処理のキュー
delete_message_queue: List[DeleteMessageInfo] = []

@client.event
async def on_ready():
    print(f'{client.user} がログインしました！')

def parse_time(time_str: str) -> int:
    # 複数の時間単位を解析する関数
    matches = re.findall(r'(\d+)(s|m|h)', time_str)
    total_seconds = 0
    for amount, unit in matches:
        amount = int(amount)
        if unit == 'm':
            total_seconds += amount * 60  # 分を秒に変換
        elif unit == 'h':
            total_seconds += amount * 3600  # 時間を秒に変換
        else:  # 's'
            total_seconds += amount
    return total_seconds if total_seconds > 0 else 24 * 3600  # デフォルトは24時間

def format_time(seconds: int) -> str:
    # 秒を「時間:分:秒」の形式に変換する関数
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours}時間{minutes}分{seconds}秒"

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if client.user in message.mentions:
        content = message.content
        match = re.match(r'!del\s+(\d+)\s+(.*)', content)
        if not match:
            return

        delete_time = parse_time(match.group(1))
        message_ids = match.group(2).split(',')

        for message_id in message_ids:
            try:
                message_id = int(message_id)
            except ValueError:
                print(f"不正なメッセージID: {message_id}")
                continue

            delete_message_queue.append(DeleteMessageInfo(message.channel.id, message_id, delete_time))

        # 削除処理タスクを1秒後に実行
        await asyncio.sleep(1)
        _ = asyncio.create_task(_run_delete_message_tasks())

@client.event
async def on_error(event, *args, **kwargs):
    print(f"エラーが発生しました: {event}")

async def _run_delete_message_tasks(message: discord.Message):
    while delete_message_queue:
        message_info = delete_message_queue.pop(0)
        await delete_message_task(message_info)
        await asyncio.sleep(message_info.delete_time)
        # 削除完了メッセージ
        await message.channel.send(f"**メッセージID {message_info.message_id} を削除しました。**")

    # 全てのメッセージ削除完了後、Botの動作を終了
    await client.close()

    client.run(TOKEN, on_message=_run_delete_message_tasks)

client.run(TOKEN)