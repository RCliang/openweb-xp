# Open WebUI 二次开发设计文档

> 工程师助手 - AI驱动的企业级工程知识管理与协作平台

---

## 一、开发目标

基于 Open WebUI 进行二次开发，打造面向新能源车辆开发领域的 AI 知识管理平台。

**核心改动：**
1. 移除 Ollama，只保留 OpenAI 格式的 LLM API
2. 移除登录模块，通过 iframe URL 参数传入用户身份
3. 移除前端模型配置页面，由管理者后台配置
4. 功能精简：对话、文档管理、知识库管理、Episode管理、Skills、Memories
5. 数据库改用 MySQL + Milvus

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    二次开发后架构                                │
├─────────────────────────────────────────────────────────────────┤
│  前端 (精简版 SvelteKit)                                        │
│  ├── 对话页面 (核心)                                            │
│  ├── 文档管理页面                                               │
│  ├── 知识库管理页面                                             │
│  ├── Episode 管理页面                                           │
│  ├── Skills 页面                                                │
│  └── Memories 页面                                              │
├─────────────────────────────────────────────────────────────────┤
│  后端 (FastAPI)                                                 │
│  ├── 认证模块 → iframe URL 参数解析                             │
│  ├── 对话 API → OpenAI 格式 LLM                                 │
│  ├── 文档 API → 解析 + Milvus 向量化                            │
│  ├── 知识库 API → MySQL 元数据 + Milvus 向量                    │
│  ├── Episode API → MySQL 存储 + AI 半自动提取                   │
│  ├── Skills API → 技能/提示词模板                               │
│  └── Memories API → 用户长期记忆                                │
├─────────────────────────────────────────────────────────────────┤
│  数据层                                                         │
│  ├── MySQL → 用户、对话、知识库、Episode、配置                   │
│  └── Milvus → 文档向量、知识库向量                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、认证模块改造

**原架构：**
```
用户登录 → JWT Token → 每次请求携带 Token → 后端验证
```

**新架构：**
```
1. 主站加载 iframe: src="https://ai.example.com?user=张三&dept=动力平台"
2. 前端解析 URL 参数 → 存入 sessionStorage
3. 首次请求时后端：
   ├── 查询 MySQL 是否存在该用户
   ├── 不存在 → 自动创建用户记录（部门绑定）
   └── 生成会话 token 返回前端
4. 后续请求携带 token
```

**需要改造的文件：**

| 位置 | 文件 | 改动 |
|------|------|------|
| 前端 | `src/lib/apis/auths/index.ts` | 移除登录/注册函数，新增 URL 参数解析 |
| 前端 | `src/routes/auth/` | 删除整个目录 |
| 前端 | `src/routes/(app)/+layout.svelte` | 移除登录状态检查，改为解析 URL 参数 |
| 后端 | `backend/open_webui/routers/auths.py` | 简化为 URL 参数验证 + 自动创建用户 |
| 后端 | `backend/open_webui/models/users.py` | 新增 `department` 字段 |

---

## 四、数据库配置与模型

### 4.1 连接配置

**MySQL:**
```
mysql+pymysql://root:powerai123@172.22.18.164:8501/xp_power?charset=utf8
```

**Milvus:**
```
host: 172.22.18.167
port: 19530
user: root
password: Milvus
```

### 4.2 数据表结构

**users (改造):**
```sql
ALTER TABLE users ADD COLUMN department VARCHAR(100);
```

**knowledge (新增):**
```sql
CREATE TABLE knowledge (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type ENUM('personal', 'department', 'center') NOT NULL,
    department VARCHAR(100),  -- 科室知识库用
    user_id VARCHAR(36),      -- 创建者
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**files (改造):**
```sql
ALTER TABLE files ADD COLUMN knowledge_id VARCHAR(36);
```

**episodes (新增):**
```sql
CREATE TABLE episodes (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255),
    question TEXT NOT NULL,
    reasoning TEXT,
    solution TEXT NOT NULL,
    references JSON,          -- 引用来源数组
    chat_id VARCHAR(36),      -- 来源对话
    user_id VARCHAR(36) NOT NULL,
    department VARCHAR(100),
    status ENUM('draft', 'published') DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

**model_config (新增):**
```sql
CREATE TABLE model_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    api_base_url VARCHAR(500) NOT NULL,
    api_key VARCHAR(500) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.3 Milvus 向量集合

**document_vectors:**
```
字段:
- id: 主键
- embedding: FLOAT_VECTOR(1024)  -- Qwen3-Embedding 维度
- content: VARCHAR(65535)        -- 文本片段
- file_id: VARCHAR(36)
- knowledge_id: VARCHAR(36)
- metadata: JSON                 -- 页码、来源等
```

**episode_vectors (可选):**
```
字段:
- id: 主键
- embedding: FLOAT_VECTOR(1024)
- episode_id: VARCHAR(36)
- content: VARCHAR(65535)
```

---

## 五、知识库权限控制

**权限规则：**

| 知识库类型 | 可见范围 |
|-----------|---------|
| personal (个人) | 仅创建者本人 |
| department (科室) | 同一部门所有用户 |
| center (中心) | 全员可见 |

**后端权限过滤逻辑：**
```python
def get_accessible_knowledges(user_id, department):
    return Knowledge.filter(
        (type == "center") |
        (type == "department" && department == user.department) |
        (type == "personal" && user_id == user.id)
    )
```

---

## 六、Episode 半自动提取流程

**交互流程：**
```
1. 用户完成一次有价值的对话
   └── 点击「保存为经验」按钮

2. 前端调用 AI 生成草稿
   POST /api/v1/episodes/generate
   { chat_id: "xxx", messages: [...] }

3. AI 返回结构化草稿
   {
     question: "如何配置VCU自研模式的启动条件？",
     reasoning: "首先需要理解...",
     solution: "1. 打开配置文件... 2. 修改...",
     references: ["技术规范v2.1.pdf p.15", "FRS文档 p.8"]
   }

4. 用户编辑草稿 → 确认保存
   POST /api/v1/episodes/
   { ...episode数据, status: "published" }

5. 后端生成 Episode 向量存入 Milvus
```

**Episode 数据结构：**
```typescript
interface Episode {
  id: string;
  title: string;
  question: string;
  reasoning: string;
  solution: string;
  references: string[];
  chat_id: string;
  user_id: string;
  department: string;
  status: 'draft' | 'published';
  created_at: datetime;
  updated_at: datetime;
}
```

---

## 七、前端模块精简

### 7.1 保留的 API 模块

```
src/lib/apis/
├── index.ts          ✅ 保留 - 核心对话、模型获取
├── auths/            ✏️ 改造 - 简化为 URL 参数解析
├── chats/            ✅ 保留 - 对话管理
├── files/            ✅ 保留 - 文档上传管理
├── knowledge/        ✏️ 改造 - 知识库管理
├── retrieval/        ✅ 保留 - RAG 检索
├── streaming/        ✅ 保留 - SSE 流式响应
├── configs/          ✏️ 改造 - 仅保留后端配置获取
├── openai/           ✏️ 改造 - 简化为单一 OpenAI 连接
├── skills/           ✅ 保留 - 技能模块
├── memories/         ✅ 保留 - 记忆模块
├── tasks/            ✏️ 部分保留 - 标题生成等辅助任务
├── utils/            ✅ 保留
└── episodes/         🆕 新增 - Episode 管理
```

### 7.2 删除的 API 模块

```
src/lib/apis/
├── ollama/           ❌ 删除
├── audio/            ❌ 删除
├── images/           ❌ 删除
├── tools/            ❌ 删除
├── functions/        ❌ 删除
├── prompts/          ❌ 删除
├── models/           ❌ 删除
├── users/            ❌ 删除
├── groups/           ❌ 删除
├── channels/         ❌ 删除
├── folders/          ❌ 删除
├── evaluations/      ❌ 删除
├── analytics/        ❌ 删除
└── notes/            ❌ 删除
```

### 7.3 页面路由

**保留:**
```
src/routes/
├── (app)/
│   ├── +page.svelte        ✅ 主对话页面
│   ├── c/[id]/             ✅ 具体对话
│   └── workspace/
│       ├── documents/      ✅ 文档管理
│       └── knowledge/      ✏️ 知识库管理
└── episodes/               🆕 Episode 管理
```

**删除:**
```
src/routes/auth/            ❌ 删除整个目录
```

---

## 八、后端路由精简

### 8.1 保留的路由

```
backend/open_webui/routers/
├── auths.py          ✏️ 改造
├── chats.py          ✅ 保留
├── files.py          ✅ 保留
├── knowledge.py      ✏️ 改造
├── retrieval.py      ✅ 保留
├── configs.py        ✏️ 改造
├── openai.py         ✏️ 改造
├── skills.py         ✅ 保留
├── memories.py       ✅ 保留
├── tasks.py          ✏️ 部分保留
└── episodes.py       🆕 新增
```

### 8.2 新增 Episode API

```
POST   /api/v1/episodes/           # 创建 Episode
GET    /api/v1/episodes/           # 获取 Episode 列表
GET    /api/v1/episodes/{id}       # 获取单个 Episode
POST   /api/v1/episodes/{id}       # 更新 Episode
DELETE /api/v1/episodes/{id}       # 删除 Episode
POST   /api/v1/episodes/generate   # AI 生成 Episode 草稿
```

### 8.3 删除的路由

```
backend/open_webui/routers/
├── ollama.py         ❌ 删除
├── audio.py          ❌ 删除
├── images.py         ❌ 删除
├── tools.py          ❌ 删除
├── functions.py      ❌ 删除
├── prompts.py        ❌ 删除
├── models.py         ❌ 删除
├── users.py          ❌ 删除
├── groups.py         ❌ 删除
├── channels.py       ❌ 删除
├── folders.py        ❌ 删除
└── evaluations.py    ❌ 删除
```

---

## 九、改动清单汇总

### 前端改动

| 类别 | 操作 | 内容 |
|------|------|------|
| 认证 | 改造 | URL 参数解析替代登录 |
| API 模块 | 删除 | ollama, audio, images, tools, functions, prompts, models, users, groups, channels, folders, evaluations, analytics, notes |
| API 模块 | 保留 | chats, files, knowledge, retrieval, streaming, configs, openai, skills, memories, tasks, utils |
| API 模块 | 新增 | episodes |
| 页面路由 | 删除 | auth/ |
| 页面路由 | 新增 | (app)/episodes/ |
| 组件 | 精简 | 移除模型配置、工具管理等组件 |

### 后端改动

| 类别 | 操作 | 内容 |
|------|------|------|
| 认证 | 改造 | URL 参数验证 + 自动创建用户 |
| 路由 | 删除 | ollama, audio, images, tools, functions, prompts, models, users, groups, channels, folders, evaluations |
| 路由 | 保留 | auths, chats, files, knowledge, retrieval, configs, openai, skills, memories, tasks |
| 路由 | 新增 | episodes |
| 模型 | 改造 | users 表新增 department 字段 |
| 模型 | 新增 | episodes, knowledge 表 |

### 数据库改动

| 类别 | 内容 |
|------|------|
| MySQL | 主数据库，存储用户、对话、知识库、Episode、配置 |
| Milvus | 向量数据库，存储文档向量、Episode 向量 |

### 配置改动

| 文件 | 改动 |
|------|------|
| env.py | 数据库连接改为 MySQL + Milvus |
| config.py | 移除 Ollama 相关配置 |

---

## 十、实施建议

### 推荐开发顺序

1. **数据库配置** - 配置 MySQL 和 Milvus 连接
2. **认证改造** - 实现 URL 参数解析和自动用户创建
3. **后端路由精简** - 删除不需要的路由，保留核心功能
4. **前端精简** - 删除不需要的页面和组件
5. **知识库改造** - 实现权限控制和部门关联
6. **Episode 功能** - 新增 Episode 管理模块
7. **测试验证** - 端到端功能测试

---

*文档创建时间：2026-02-28*
*基于 Open WebUI 二次开发*
