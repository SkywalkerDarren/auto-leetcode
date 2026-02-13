# auto-leetcode

用 AI 自动刷完 LeetCode 全部题目的 CLI 工具。

支持 OpenAI 兼容 API 和 Claude 兼容 API，可配合中转站使用。每道题自动生成解题思路和 Python 代码，提交到 LeetCode，失败自动重试（AI 会参考上次的错误信息修正）。

[English](README.md)

> 如果你的公司有 token 用量考核这种离谱的要求，或者单纯想测测某个模型的算法能力（这些题应该都内化到模型骨子里了吧 hhhh），可以试试这个项目。

## 工作流程

```
获取题目 → AI 生成思路 + 代码 → 提交到 LeetCode → 记录结果 → 下一题
                                    ↑                |
                                    |   失败（≤ 重试次数）
                                    └────────────────┘
```

## 快速开始

### 1. 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. 配置

复制 `.env.example` 为 `.env` 并填入你的信息：

```bash
cp .env.example .env
```

```env
# LeetCode 认证（从浏览器 Cookie 获取）
LEETCODE_SESSION=your_session_cookie
CSRF_TOKEN=your_csrf_token

# AI 配置
AI_PROVIDER=openai          # openai 或 claude
AI_API_KEY=sk-xxx
AI_BASE_URL=https://api.openai.com/v1   # 中转站地址
AI_MODEL=gpt-4o
```

**获取 LeetCode Cookie：**
1. 登录 [leetcode.com](https://leetcode.com)
2. F12 → Application → Cookies → `https://leetcode.com`
3. 复制 `LEETCODE_SESSION` 和 `csrftoken` 的值

### 3. 运行

```bash
# 从第 1 题开始顺序做，每题最多重试 3 次
auto-leetcode solve --start 1 --end 100 --retries 3

# 查看进度
auto-leetcode status
```

## 输出

- `solutions/0001.py` — 每道题的解题思路 + 代码
- `results.jsonl` — 提交记录（题号、状态、耗时、内存、模型、时间戳）

解题文件示例：

```python
# Problem #1
# Model: claude-opus-4-6
# Attempt: 1
#
# Approach:
# Use a hash map to store seen numbers. For each number,
# check if (target - num) exists in the map. O(n) time, O(n) space.

class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for i, num in enumerate(nums):
            complement = target - num
            if complement in seen:
                return [seen[complement], i]
            seen[num] = i
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 测试
pytest tests/ -v

# 覆盖率
pytest tests/ --cov=auto_leetcode --cov-report=term-missing

# 代码检查
ruff check src/ tests/
black --check src/ tests/
mypy src/
```

## 项目结构

```
src/auto_leetcode/
├── cli.py              # CLI 入口（click）
├── config.py           # 配置加载（.env）
├── runner.py           # 核心编排循环
├── errors.py           # 异常层级
├── models/             # 数据模型（frozen dataclass）
├── leetcode/           # LeetCode GraphQL 客户端 + 提交
├── ai/                 # AI 生成器（OpenAI / Claude）+ 提示词
└── storage/            # JSONL 存储 + 文件保存
```

## 注意事项

- LeetCode 有频率限制，默认每题间隔 10 秒，重试间隔 5 秒
- 付费题和无 Python3 代码模板的题会自动跳过
- 已通过的题会自动跳过，支持断点续跑
- Session Cookie 会过期，需要定期更新
