from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AgriNex MCP Server", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

class CommandRequest(BaseModel):
    command: str

class CommandResponse(BaseModel):
    success: bool
    message: str

@app.get("/")
def root():
    return {"message": "AgriNex MCP Server is running!"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/mcp/execute", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    """
    执行自然语言控制指令
    """
    try:
        # 简单的意图解析（后续可以扩展为更复杂的NLP）
        intent, params = parse_intent(request.command)
        
        # 根据意图执行相应操作
        result = await execute_intent(intent, params)
        
        return CommandResponse(
            success=True,
            message=result
        )
    except Exception as e:
        return CommandResponse(
            success=False,
            message=f"执行失败: {str(e)}"
        )

def parse_intent(command: str):
    """
    简单的意图解析 - 基于关键词匹配
    """
    command = command.lower()
    
    if "预测" in command:
        return "forecast", {"action": "trigger"}
    elif "历史" in command or "数据" in command:
        return "history", {"action": "query"}
    elif "阈值" in command:
        return "threshold", {"action": "modify"}
    elif "告警" in command:
        return "alarm", {"action": "config"}
    else:
        return "unknown", {}

async def execute_intent(intent: str, params: dict) -> str:
    """
    根据意图执行操作
    """
    if intent == "forecast":
        return "已为您触发传感器预测，请稍后查看结果"
    elif intent == "history":
        return "正在为您查询历史数据..."
    elif intent == "threshold":
        return "告警阈值配置已更新"
    elif intent == "alarm":
        return "告警配置已修改"
    else:
        return "抱歉，我还不理解这个指令，请尝试其他表达方式"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
