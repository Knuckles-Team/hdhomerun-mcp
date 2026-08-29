#!/usr/bin/env python3
import asyncio
import json
import uuid

import httpx

A2A_URL = "http://localhost:9016/a2a/"


def _build_message_payload(question: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "method": "message/send",
        "params": {
            "message": {
                "kind": "message",
                "role": "user",
                "parts": [{"kind": "text", "text": question}],
                "messageId": str(uuid.uuid4()),
            }
        },
        "id": 1,
    }


def _build_poll_payload(task_id) -> dict:
    return {
        "jsonrpc": "2.0",
        "method": "tasks/get",
        "params": {"id": task_id},
        "id": 2,
    }


def _find_last_agent_message(history: list) -> dict | None:
    for msg in reversed(history):
        if msg.get("role") != "user":
            return msg
    return None


def _print_agent_response(last_msg: dict | None) -> None:
    if last_msg and "parts" in last_msg:
        print("\n--- Agent Response ---")
        for part in last_msg["parts"]:
            if "text" in part:
                print(part["text"])
            elif "content" in part:
                print(part["content"])
    elif last_msg:
        print(f"Final Message (No parts): {last_msg}")
    else:
        print("\n--- No Agent Response Found in History ---")


def _print_task_history(poll_data: dict) -> None:
    history = poll_data["result"].get("history")
    if not history:
        return
    _print_agent_response(_find_last_agent_message(history))


async def _poll_task_once(client: httpx.AsyncClient, url: str, task_id) -> bool:
    """Poll the task once. Returns True when polling should stop."""
    poll_resp = await client.post(
        url, json=_build_poll_payload(task_id), headers={"Content-Type": "application/json"}
    )
    if poll_resp.status_code != 200:
        print(f"Polling Failed: {poll_resp.status_code}")
        print(f"Polling Error Details: {poll_resp.text}")
        return True

    poll_data = poll_resp.json()
    if "result" not in poll_data:
        print("Starting polling error key check...")
        if "error" in poll_data:
            print(f"Polling Error: {poll_data['error']}")
        return True

    state = poll_data["result"]["status"]["state"]
    print(f"Task State: {state}")
    if state in ("submitted", "running", "working"):
        return False

    print(f"\nTask Finished with state: {state}")
    _print_task_history(poll_data)
    print(f"Full Result Debug:\n{json.dumps(poll_data, indent=2)}")
    return True


async def _poll_task(client: httpx.AsyncClient, url: str, task_id) -> None:
    print(f"\nTask Submitted with ID: {task_id}. Polling for result...")
    done = False
    while not done:
        await asyncio.sleep(2)
        done = await _poll_task_once(client, url, task_id)


async def _handle_send_response(client: httpx.AsyncClient, url: str, resp: httpx.Response) -> None:
    if resp.status_code != 200:
        print(f"Error: {resp.status_code}")
        print(resp.text)
        return

    try:
        data = resp.json()
    except json.JSONDecodeError:
        print(f"Response (Text):\n{resp.text}")
        return

    print(f"Response (JSON):\n{json.dumps(data, indent=2)}")
    if "result" in data and "id" in data["result"]:
        await _poll_task(client, url, data["result"]["id"])
    if "error" in data:
        print(f"JSON-RPC Error: {data['error']}")


async def _send_question(client: httpx.AsyncClient, url: str, question: str) -> None:
    print(f"\n\n\nUser: {question}")
    print("--- Sending Request ---")
    payload = _build_message_payload(question)
    try:
        print(f"Trying POST {url} with JSON-RPC (message/send)...")
        resp = await client.post(
            url, json=payload, headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {resp.status_code}")
        await _handle_send_response(client, url, resp)
    except httpx.RequestError as e:
        print(f"Connection failed to {url}: {e}")


async def main():
    print(f"Validating A2A Agent at {A2A_URL}...")

    questions = [
        "Can you get me the commits for project id 171?",
    ]

    async with httpx.AsyncClient(timeout=10000.0) as client:
        for q in questions:
            await _send_question(client, A2A_URL, q)


if __name__ == "__main__":
    asyncio.run(main())
