import os
import json
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber  # PDF文本提取
from http import HTTPStatus
import dashscope  # 通义千问API
from dashscope import Generation
import redis  # 缓存（可选）

# ---------------------- 基础配置 ----------------------
app = FastAPI(title="简历分析后端API")

# 解决跨域（前端能访问后端）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 测试阶段允许所有前端访问，生产环境改前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 通义千问API配置（替换成你的API-KEY）
dashscope.api_key = "sk-dc6888d0c76f4a49b1f2e71d24150342"

# Redis缓存配置（可选，加分项，没有就注释掉）
try:
    r = redis.Redis(
        host="localhost",  # 本地Redis默认地址
        port=6379,         # 本地Redis默认端口
        password="",       # 本地Redis默认无密码（如果你的有密码，填实际密码）
        db=0,              # 使用第0个数据库
        decode_responses=True,
        # 本地Redis可能需要加超时和重试（避免连接失败）
        socket_timeout=5,
        retry_on_timeout=True
    )
    r.ping()  # 测试连接
    print("本地Redis连接成功✅")
except Exception as e:
    r = None
    print(f"本地Redis未连接（跳过缓存）：{str(e)}")
# ---------------------- 核心工具函数 ----------------------
def extract_pdf_text(file_path: str) -> str:
    """提取PDF文本（兼容多页）"""
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF解析失败：{str(e)}")

def call_ai_resume_analysis(resume_text: str, job_demand: Dict[str, str]) -> Dict[str, Any]:
    """调用通义千问API，提取简历信息+计算匹配度"""
    # 构造AI提示词（关键！决定AI返回的格式和内容）
    prompt = f"""
    你是一个专业的招聘简历分析助手，请完成以下任务：
    1. 从简历文本中提取关键信息，按以下格式返回JSON（无多余文字）：
       {{
         "basicInfo": {{
           "name": "姓名",
           "phone": "电话",
           "email": "邮箱",
           "address": "地址"
         }},
         "jobInfo": {{
           "intention": "求职意向",
           "salary": "期望薪资",
           "workYears": "工作年限",
           "education": "学历背景"
         }}
       }}
    2. 根据岗位需求计算匹配度，岗位需求：{json.dumps(job_demand, ensure_ascii=False)}
       匹配度包含：技能匹配率（0-100）、经验相关性（0-100）、综合匹配度（0-100），补充到上述JSON的matchScore字段中。
    要求：只返回JSON，不要其他解释性文字，字段为空填"待解析"，匹配度为整数。
    简历文本：{resume_text}
    """

    # 调用通义千问API
    try:
        response = Generation.call(
            model="qwen-turbo",  # 免费轻量模型，足够用
            messages=[{"role": "user", "content": prompt}],
            result_format="json",  # 指定返回JSON
            temperature=0.1  # 降低随机性，保证结果稳定
        )
        # 解析AI返回结果
        if response.status_code == HTTPStatus.OK:
            return json.loads(response.output.choices[0].message.content)
        else:
            raise HTTPException(status_code=500, detail=f"AI调用失败：{response.code} - {response.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI分析失败：{str(e)}")

# ---------------------- API接口（和前端对接） ----------------------
@app.post("/analyze_resume", summary="解析简历并匹配岗位")
async def analyze_resume(
    file: UploadFile = File(...),  # 前端上传的PDF简历
    # 前端拆分后的岗位需求参数（和你修改后的前端对应）
    skills: str = Form(...),
    workExperience: str = Form(...),
    workExperienceDesc: str = Form(""),
    education: str = Form(...),
    otherRequirements: str = Form("")
):
    # 1. 保存上传的PDF文件（临时）
    file_path = f"temp_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    try:
        # 2. 缓存逻辑（可选，加分项）：用文件MD5/文件名做缓存键
        cache_key = f"resume_{file.filename}_{skills}_{workExperience}_{education}"
        if r and r.exists(cache_key):
            return json.loads(r.get(cache_key))  # 返回缓存结果

        # 3. 提取PDF文本
        resume_text = extract_pdf_text(file_path)
        if not resume_text:
            raise HTTPException(status_code=400, detail="PDF无有效文本")

        # 4. 构造岗位需求字典（和前端对应）
        job_demand = {
            "skills": skills,
            "workExperience": workExperience,
            "workExperienceDesc": workExperienceDesc,
            "education": education,
            "otherRequirements": otherRequirements
        }

        # 5. 调用AI分析简历
        result = call_ai_resume_analysis(resume_text, job_demand)

        # 6. 缓存结果（可选，有效期1小时）
        if r:
            r.setex(cache_key, 3600, json.dumps(result, ensure_ascii=False))

        # 7. 返回结果（和前端resumeData结构完全匹配）
        return result

    finally:
        # 删除临时文件
        if os.path.exists(file_path):
            os.remove(file_path)

# 本地运行入口
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)