# WisHub Skill API 参考文档

## 概述

WisHub Skill API 提供了技能注册、调用、发现和编排的完整接口。

### 基础信息

- **Base URL**: `http://localhost:8000`
- **API Version**: `v1`
- **Authentication**: API Key (Header: `X-API-Key`)
- **Content-Type**: `application/json`

### 全局响应格式

```json
{
  "status": "success|error",
  "message": "操作结果描述",
  "data": {},
  "error": {
    "code": "错误代码",
    "details": "错误详情"
  }
}
```

---

## 认证

### API Key 认证

所有端点都需要 API Key 认证。在请求头中添加：

```http
X-API-Key: your_api_key_here
```

---

## 端点列表

### 1. 健康检查

#### GET `/api/v1/health`

检查服务健康状态。

**请求示例**

```bash
curl -X GET http://localhost:8000/api/v1/health
```

**响应示例**

```json
{
  "status": "success",
  "service": "wishub-skill",
  "version": "1.0.0",
  "timestamp": "2025-02-23T12:00:00Z",
  "database": "connected",
  "storage": "connected"
}
```

---

### 2. Skill 注册

#### POST `/api/v1/skill/register`

上传并注册一个新的 Skill。

**请求头**

```http
Content-Type: application/json
X-API-Key: your_api_key
```

**请求参数**

| 参数 | 类型 | 必填 | 描述 | 默认值 |
|------|------|------|------|--------|
| skill_id | string | 是 | Skill ID（唯一标识） | - |
| skill_name | string | 是 | Skill 名称 | - |
| description | string | 否 | Skill 描述 | - |
| version | string | 是 | 版本号（语义化版本） | - |
| language | string | 是 | 编程语言 (python/typescript/go) | - |
| code | string | 是 | Base64 编码的代码 | - |
| timeout | integer | 是 | 超时时间（秒） | 30 |
| dependencies | object | 否 | 依赖项 | {} |
| input_schema | object | 否 | 输入参数 JSON Schema | {} |
| output_schema | object | 否 | 输出结果 JSON Schema | {} |
| author | string | 否 | 作者 | - |
| license | string | 否 | 许可证 | MIT |
| category | string | 否 | 分类 | general |

**请求示例**

```bash
# Python Skill 代码示例
SKILL_CODE='
def execute(inputs):
    """计算平方值"""
    value = inputs.get("value", 0)
    result = value ** 2
    return {"result": result, "input": value}
'

# Base64 编码
CODE_BASE64=$(echo -n "$SKILL_CODE" | base64)

# 注册 Skill
curl -X POST http://localhost:8000/api/v1/skill/register \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d "{
    \"skill_id\": \"skill_square\",
    \"skill_name\": \"计算平方\",
    \"description\": \"计算数值的平方值\",
    \"version\": \"1.0.0\",
    \"language\": \"python\",
    \"code\": \"$CODE_BASE64\",
    \"timeout\": 30,
    \"input_schema\": {
      \"type\": \"object\",
      \"properties\": {
        \"value\": {\"type\": \"number\"}
      },
      \"required\": [\"value\"]
    },
    \"output_schema\": {
      \"type\": \"object\",
      \"properties\": {
        \"result\": {\"type\": \"number\"}
      }
    },
    \"author\": \"WisHub Team\",
    \"category\": \"math\"
  }"
```

**成功响应示例**

```json
{
  "status": "success",
  "skill_id": "skill_square",
  "version": "1.0.0",
  "registration_time": "2025-02-23T12:00:00Z",
  "message": "Skill 注册成功"
}
```

**错误响应示例**

```json
{
  "status": "error",
  "message": "Skill 已存在: skill_square",
  "error": {
    "code": "SKILL_REG_001",
    "details": "Skill ID 已被使用"
  }
}
```

**错误代码**

| 代码 | 描述 | HTTP 状态码 |
|------|------|-------------|
| SKILL_REG_001 | Skill 已存在 | 409 |
| SKILL_REG_002 | 参数验证失败 | 422 |
| SKILL_REG_003 | 代码格式无效 | 400 |
| SKILL_REG_999 | 内部服务器错误 | 500 |

---

### 3. Skill 调用

#### POST `/api/v1/skill/invoke`

执行指定的 Skill。

**请求头**

```http
Content-Type: application/json
X-API-Key: your_api_key
```

**请求参数**

| 参数 | 类型 | 必填 | 描述 | 默认值 |
|------|------|------|------|--------|
| skill_id | string | 是 | Skill ID | - |
| inputs | object | 是 | 输入参数 | {} |
| timeout | integer | 否 | 超时时间（秒） | 30 |
| async | boolean | 否 | 是否异步执行 | false |

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/skill/invoke \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "skill_id": "skill_square",
    "inputs": {"value": 5},
    "timeout": 30,
    "async": false
  }'
```

**同步执行响应示例**

```json
{
  "status": "success",
  "skill_id": "skill_square",
  "execution_id": "exec_20250223_001",
  "result": {
    "result": 25,
    "input": 5
  },
  "execution_time": 0.023,
  "tokens_used": 0
}
```

**异步执行响应示例**

```json
{
  "status": "success",
  "skill_id": "skill_square",
  "execution_id": "exec_20250223_001",
  "message": "执行任务已创建",
  "status_url": "/api/v1/skill/status/exec_20250223_001"
}
```

**错误响应示例**

```json
{
  "status": "error",
  "message": "Skill 不存在: skill_invalid",
  "error": {
    "code": "SKILL_INV_001",
    "details": "Skill not found"
  }
}
```

**错误代码**

| 代码 | 描述 | HTTP 状态码 |
|------|------|-------------|
| SKILL_INV_001 | Skill 不存在 | 404 |
| SKILL_INV_002 | 输入参数无效 | 422 |
| SKILL_INV_003 | 执行超时 | 504 |
| SKILL_INV_004 | 执行失败 | 500 |
| SKILL_INV_999 | 内部服务器错误 | 500 |

---

### 4. Skill 状态查询

#### GET `/api/v1/skill/status/{execution_id}`

查询 Skill 执行状态。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| execution_id | string | 执行 ID |

**请求示例**

```bash
curl -X GET http://localhost:8000/api/v1/skill/status/exec_20250223_001 \
  -H "X-API-Key: your_api_key"
```

**响应示例（进行中）**

```json
{
  "status": "running",
  "execution_id": "exec_20250223_001",
  "skill_id": "skill_square",
  "started_at": "2025-02-23T12:00:00Z",
  "elapsed_time": 5.23
}
```

**响应示例（已完成）**

```json
{
  "status": "completed",
  "execution_id": "exec_20250223_001",
  "skill_id": "skill_square",
  "result": {
    "result": 25,
    "input": 5
  },
  "started_at": "2025-02-23T12:00:00Z",
  "completed_at": "2025-02-23T12:00:01Z",
  "execution_time": 0.023
}
```

---

### 5. Skill 发现

#### GET `/api/v1/skill/discovery`

发现和搜索 Skills。

**查询参数**

| 参数 | 类型 | 必填 | 描述 | 默认值 |
|------|------|------|------|--------|
| q | string | 否 | 搜索关键词 | - |
| category | string | 否 | 分类过滤 | - |
| language | string | 否 | 语言过滤 | - |
| page | integer | 否 | 页码 | 1 |
| page_size | integer | 否 | 每页数量 | 20 |
| sort | string | 否 | 排序 (name/date/popularity) | name |

**请求示例**

```bash
# 搜索所有 Skills
curl -X GET "http://localhost:8000/api/v1/skill/discovery" \
  -H "X-API-Key: your_api_key"

# 搜索特定类别的 Skills
curl -X GET "http://localhost:8000/api/v1/skill/discovery?category=math&language=python&page=1&page_size=10" \
  -H "X-API-Key: your_api_key"

# 关键词搜索
curl -X GET "http://localhost:8000/api/v1/skill/discovery?q=计算&sort=popularity" \
  -H "X-API-Key: your_api_key"
```

**响应示例**

```json
{
  "status": "success",
  "skills": [
    {
      "skill_id": "skill_square",
      "skill_name": "计算平方",
      "description": "计算数值的平方值",
      "version": "1.0.0",
      "language": "python",
      "author": "WisHub Team",
      "category": "math",
      "created_at": "2025-02-23T12:00:00Z",
      "popularity": 1250
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

---

### 6. Skill 详情

#### GET `/api/v1/skill/{skill_id}`

获取 Skill 详细信息。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| skill_id | string | Skill ID |

**请求示例**

```bash
curl -X GET http://localhost:8000/api/v1/skill/skill_square \
  -H "X-API-Key: your_api_key"
```

**响应示例**

```json
{
  "status": "success",
  "skill": {
    "skill_id": "skill_square",
    "skill_name": "计算平方",
    "description": "计算数值的平方值",
    "version": "1.0.0",
    "language": "python",
    "timeout": 30,
    "author": "WisHub Team",
    "license": "MIT",
    "category": "math",
    "input_schema": {
      "type": "object",
      "properties": {
        "value": {"type": "number"}
      }
    },
    "output_schema": {
      "type": "object",
      "properties": {
        "result": {"type": "number"}
      }
    },
    "created_at": "2025-02-23T12:00:00Z",
    "updated_at": "2025-02-23T12:00:00Z",
    "usage_stats": {
      "total_calls": 1234,
      "success_rate": 0.98
    }
  }
}
```

---

### 7. Skill 删除

#### DELETE `/api/v1/skill/{skill_id}`

删除指定的 Skill。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| skill_id | string | Skill ID |

**请求示例**

```bash
curl -X DELETE http://localhost:8000/api/v1/skill/skill_square \
  -H "X-API-Key: your_api_key"
```

**响应示例**

```json
{
  "status": "success",
  "message": "Skill skill_square 已删除"
}
```

---

### 8. Skill 编排

#### POST `/api/v1/skill/orchestrate`

执行 Skill 工作流编排。

**请求头**

```http
Content-Type: application/json
X-API-Key: your_api_key
```

**请求参数**

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| workflow_id | string | 是 | 工作流 ID |
| workflow | object | 是 | 工作流定义 (DAG) |
| inputs | object | 是 | 全局输入参数 |
| timeout | integer | 否 | 总超时时间（秒） |

**工作流定义示例**

```json
{
  "nodes": [
    {"id": "node1", "skill_id": "skill_square", "inputs": {"value": 5}},
    {"id": "node2", "skill_id": "skill_square", "inputs": {"value": 3}},
    {"id": "node3", "skill_id": "skill_add", "inputs": {"a": "${node1.result}", "b": "${node2.result}"}}
  ],
  "edges": [
    {"from": "node1", "to": "node3"},
    {"from": "node2", "to": "node3"}
  ]
}
```

**请求示例**

```bash
curl -X POST http://localhost:8000/api/v1/skill/orchestrate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{
    "workflow_id": "wf_complex_calculation",
    "workflow": {
      "nodes": [
        {"id": "node1", "skill_id": "skill_square", "inputs": {"value": 5}},
        {"id": "node2", "skill_id": "skill_square", "inputs": {"value": 3}},
        {"id": "node3", "skill_id": "skill_add", "inputs": {"a": "${node1.result}", "b": "${node2.result}"}}
      ],
      "edges": [
        {"from": "node1", "to": "node3"},
        {"from": "node2", "to": "node3"}
      ]
    },
    "inputs": {},
    "timeout": 60
  }'
```

**响应示例**

```json
{
  "status": "success",
  "workflow_id": "wf_complex_calculation",
  "execution_id": "exec_wf_20250223_001",
  "results": {
    "node1": {"result": 25, "input": 5},
    "node2": {"result": 9, "input": 3},
    "node3": {"result": 34, "a": 25, "b": 9}
  },
  "execution_time": 0.56
}
```

---

## 完整请求示例

### Python 示例

```python
import requests
import json
import base64

# 配置
BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "your_api_key"

# 创建会话
session = requests.Session()
session.headers.update({
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
})

# 1. 注册 Skill
skill_code = '''
def execute(inputs):
    value = inputs.get("value", 0)
    result = value ** 2
    return {"result": result, "input": value}
'''

code_base64 = base64.b64encode(skill_code.encode()).decode()

register_response = session.post(
    f"{BASE_URL}/skill/register",
    json={
        "skill_id": "skill_square",
        "skill_name": "计算平方",
        "description": "计算数值的平方值",
        "version": "1.0.0",
        "language": "python",
        "code": code_base64,
        "timeout": 30
    }
)

print(f"注册结果: {register_response.json()}")

# 2. 调用 Skill
invoke_response = session.post(
    f"{BASE_URL}/skill/invoke",
    json={
        "skill_id": "skill_square",
        "inputs": {"value": 5},
        "timeout": 30
    }
)

result = invoke_response.json()
print(f"调用结果: {result}")

if result["status"] == "success":
    print(f"计算结果: {result['result']['result']}")
```

### Go 示例

```go
package main

import (
    "bytes"
    "encoding/base64"
    "encoding/json"
    "fmt"
    "net/http"
)

type SkillInvokeRequest struct {
    SkillID string                 `json:"skill_id"`
    Inputs  map[string]interface{} `json:"inputs"`
    Timeout int                    `json:"timeout"`
}

type SkillInvokeResponse struct {
    Status       string                 `json:"status"`
    Result       map[string]interface{} `json:"result,omitempty"`
    ExecutionID  string                 `json:"execution_id,omitempty"`
    Message      string                 `json:"message,omitempty"`
}

func main() {
    baseURL := "http://localhost:8000/api/v1"
    apiKey := "your_api_key"

    skillCode := `
def execute(inputs):
    value = inputs.get("value", 0)
    result = value ** 2
    return {"result": result, "input": value}
`

    codeBase64 := base64.StdEncoding.EncodeToString([]byte(skillCode))

    // 注册 Skill
    registerData := map[string]interface{}{
        "skill_id":    "skill_square",
        "skill_name":  "计算平方",
        "description": "计算数值的平方值",
        "version":     "1.0.0",
        "language":    "python",
        "code":        codeBase64,
        "timeout":     30,
    }

    registerJSON, _ := json.Marshal(registerData)
    req, _ := http.NewRequest("POST", baseURL+"/skill/register", bytes.NewBuffer(registerJSON))
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("X-API-Key", apiKey)

    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        fmt.Printf("注册失败: %v\n", err)
        return
    }
    defer resp.Body.Close()

    fmt.Printf("注册状态码: %d\n", resp.StatusCode)

    // 调用 Skill
    invokeReq := SkillInvokeRequest{
        SkillID: "skill_square",
        Inputs:  map[string]interface{}{"value": 5},
        Timeout: 30,
    }

    invokeJSON, _ := json.Marshal(invokeReq)
    invokeHTTPReq, _ := http.NewRequest("POST", baseURL+"/skill/invoke", bytes.NewBuffer(invokeJSON))
    invokeHTTPReq.Header.Set("Content-Type", "application/json")
    invokeHTTPReq.Header.Set("X-API-Key", apiKey)

    invokeResp, err := client.Do(invokeHTTPReq)
    if err != nil {
        fmt.Printf("调用失败: %v\n", err)
        return
    }
    defer invokeResp.Body.Close()

    var result SkillInvokeResponse
    json.NewDecoder(invokeResp.Body).Decode(&result)

    if result.Status == "success" {
        fmt.Printf("计算结果: %v\n", result.Result)
    } else {
        fmt.Printf("错误: %s\n", result.Message)
    }
}
```

### TypeScript 示例

```typescript
interface SkillInvokeRequest {
    skill_id: string;
    inputs: Record<string, any>;
    timeout?: number;
}

interface SkillInvokeResponse {
    status: string;
    result?: Record<string, any>;
    execution_id?: string;
    message?: string;
}

const BASE_URL = "http://localhost:8000/api/v1";
const API_KEY = "your_api_key";

async function invokeSkill(request: SkillInvokeRequest): Promise<SkillInvokeResponse> {
    const response = await fetch(`${BASE_URL}/skill/invoke`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY,
        },
        body: JSON.stringify(request),
    });

    return await response.json();
}

// 使用示例
async function main() {
    const result = await invokeSkill({
        skill_id: "skill_square",
        inputs: { value: 5 },
        timeout: 30,
    });

    if (result.status === "success" && result.result) {
        console.log(`计算结果: ${result.result.result}`);
    } else {
        console.log(`错误: ${result.message}`);
    }
}

main().catch(console.error);
```

---

## 错误处理

### 标准错误格式

```json
{
  "status": "error",
  "message": "错误描述",
  "error": {
    "code": "ERROR_CODE",
    "details": "详细信息"
  }
}
```

### 完整错误代码列表

| 代码 | 描述 | HTTP 状态码 |
|------|------|-------------|
| SKILL_REG_001 | Skill 已存在 | 409 |
| SKILL_REG_002 | 参数验证失败 | 422 |
| SKILL_REG_003 | 代码格式无效 | 400 |
| SKILL_REG_999 | 注册内部错误 | 500 |
| SKILL_INV_001 | Skill 不存在 | 404 |
| SKILL_INV_002 | 输入参数无效 | 422 |
| SKILL_INV_003 | 执行超时 | 504 |
| SKILL_INV_004 | 执行失败 | 500 |
| SKILL_INV_999 | 调用内部错误 | 500 |
| SKILL_ORC_001 | 工作流定义无效 | 422 |
| SKILL_ORC_002 | 循环依赖检测 | 400 |
| SKILL_ORC_999 | 编排内部错误 | 500 |

---

## 性能考虑

### 执行限制

- **最大执行时间**: 默认 30 秒，可配置
- **最大输出大小**: 10 MB
- **并发执行**: 支持 100 个并发任务

### 最佳实践

1. **输入验证**: 使用 JSON Schema 验证输入
2. **错误处理**: 在代码中处理异常
3. **日志记录**: 记录关键操作
4. **资源清理**: 清理临时文件和连接
5. **超时控制**: 合理设置超时时间

---

## 支持和反馈

- **文档**: https://github.com/Liozhang/wishub-skill
- **Issues**: https://github.com/Liozhang/wishub-skill/issues
- **API 文档 (Swagger)**: http://localhost:8000/docs
