import os
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
from opentron_telegram import OpenTronBot, PromptManager # Reuse core components

# --- Setup ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenTronAPI")

app = FastAPI(title="OpenTron API", version="1.0.0")

# Security
API_KEY = os.getenv("OPENTRON_API_KEY", "tron-dev-key")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_KEY:
    logger.error("🛑 GEMINI_API_KEY missing! OpenTron cannot synthesize thoughts without a neural link.")
else:
    logger.info("🟢 Neural Link (Gemini) detected.")

# Task Tracking
tasks: Dict[str, Dict[str, Any]] = {}

class TaskRequest(BaseModel):
    prompt: str
    policy: str = "NONE" # Default to aggressive autonomy for API

class TaskResponse(BaseModel):
    task_id: str
    status: str

# --- Agent Runner ---

async def run_agent_headless(task_id: str, prompt: str, policy: str):
    """Executes a task using a headless OpenTron instance."""
    try:
        tasks[task_id]["status"] = "processing"
        
        if not GEMINI_KEY:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = "Neural Link (GEMINI_API_KEY) missing. Operative is offline."
            return

        # Initialize Bot in Headless Mode
        bot = OpenTronBot(GEMINI_KEY, "HEADLESS_MODE")
        bot.save_policy(policy)
        
        # We need a dummy update object or refactor handle_message
        # Since we want a single response for API, we'll use a direct chat session
        
        chat = bot.model.start_chat(enable_automatic_function_calling=False)
        response = chat.send_message(prompt)
        
        history = [prompt]
        
        while True:
            # Check if text response
            if response.text and not response.candidates[0].content.parts[0].function_call:
                tasks[task_id]["result"] = response.text
                tasks[task_id]["status"] = "completed"
                break
            
            # Execute Tools
            for part in response.candidates[0].content.parts:
                if fn := part.function_call:
                    func_name = fn.name
                    args = dict(fn.args)
                    
                    logger.info(f"Task {task_id}: Executing tool {func_name}")
                    
                    # Policy check is already handled in bot tool logic if we use execute_local_tool
                    # For API, we skip the interactive confirm if policy is NONE
                    # Since this is headless, we force execution if policy != HIGH
                    
                    result = await bot.execute_local_tool(func_name, args)
                    
                    response = chat.send_message(
                        genai.protos.Content(parts=[genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(name=func_name, response={"result": result})
                        )])
                    )

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)

# --- Endpoints ---

@app.post("/v1/execute", response_model=TaskResponse)
async def execute_task(request: TaskRequest, background_tasks: BackgroundTasks, x_opentron_key: Optional[str] = Header(None)):
    if x_opentron_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"id": task_id, "status": "queued", "prompt": request.prompt}
    
    background_tasks.add_task(run_agent_headless, task_id, request.prompt, request.policy)
    
    return {"task_id": task_id, "status": "queued"}

@app.get("/v1/task/{task_id}")
async def get_task_status(task_id: str, x_opentron_key: Optional[str] = Header(None)):
    if x_opentron_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return tasks[task_id]

@app.get("/v1/status")
async def health_check():
    return {"status": "online", "grid": "OpenTron 1.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
