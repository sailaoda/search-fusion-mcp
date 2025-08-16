# 🔍 Search Fusion MCP 服务器

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/MCP-FastMCP-green.svg)](https://github.com/jlowin/fastmcp)

**🌎 [English Documentation](README.md)**

一个**高可用多引擎搜索聚合 MCP 服务器**，提供智能故障转移、统一API和LLM优化内容处理。Search Fusion 集成了多个搜索引擎，具有智能优先级路由和自动故障转移机制。

## ✨ 功能特性

### 🔄 多引擎集成
- **Google 搜索** - 需要API密钥，性能最佳
- **Serper 搜索** - Google搜索替代方案，功能强大
- **Jina AI 搜索** - AI驱动搜索，智能内容处理
- **DuckDuckGo** - 免费搜索，无需API密钥
- **Exa 搜索** - AI驱动的语义搜索
- **Bing 搜索** - 微软搜索API
- **百度搜索** - 中文搜索引擎

### 🚀 高级功能
- **智能故障转移** - 在失败或限速时自动切换引擎
- **基于优先级的路由** - 基于可用性和性能的智能引擎选择
- **统一响应格式** - 所有引擎的一致JSON结构
- **限速保护** - 内置冷却机制
- **LLM优化内容** - 高级网页内容抓取，支持分页
- **Wikipedia集成** - 专用Wikipedia搜索工具
- **Wayback Machine** - 历史网页存档搜索
- **环境变量配置** - 纯MCP配置，无需配置文件
- **🌐 增强代理自动检测** - 智能代理检测，零配置使用

### 📊 监控和分析
- 实时引擎状态监控
- 成功率跟踪
- 错误处理和恢复
- 性能指标

## 🏗️ 架构

```
Search Fusion MCP 服务器
├── 🔧 配置管理器              # MCP环境变量处理
├── 🔍 搜索管理器              # 多引擎编排
├── 🚀 引擎实现               # 各个搜索引擎
│   ├── GoogleSearch         # Google自定义搜索
│   ├── SerperSearch        # Serper API
│   ├── JinaSearch          # Jina AI搜索
│   ├── DuckDuckGoSearch    # DuckDuckGo
│   ├── ExaSearch           # Exa AI
│   ├── BingSearch          # Bing API
│   └── BaiduSearch         # 百度API
├── 🛠️ 高级抓取器             # 多方法网页抓取
└── 📡 MCP服务器             # FastMCP集成
```

## 🚀 快速开始

### 安装

#### 方式1：从PyPI安装（推荐）
```bash
pip install search-fusion-mcp
```

#### 方式2：从源码安装
```bash
git clone https://github.com/sailaoda/search-fusion-mcp.git
cd search-fusion-mcp
pip install -e .
```

## 🌐 增强代理自动检测 (v2.0新功能!)

Search Fusion 现在具备了**智能代理自动检测**功能，参考了 [concurrent-browser-mcp](https://github.com/sailaoda/concurrent-browser-mcp) 的实现，提供**零配置**的无缝代理支持！

### ✨ 三层检测策略

1. **环境变量检测** - 最高优先级，检查 `HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY`
2. **端口扫描检测** - 使用socket连接测试扫描常见代理端口
3. **系统代理检测** - 检测操作系统级别的代理设置（支持macOS）

### 🔍 支持的代理端口（按优先级排序）
- **7890** - Clash默认端口
- **1087** - V2Ray常用端口
- **8080** - 通用HTTP代理端口
- **3128** - Squid代理默认端口
- **8888** - 其他代理软件端口
- **10809** - V2Ray SOCKS端口
- **20171** - 其他代理端口

### 🚀 零配置使用

**直接运行** - 代理将被自动检测：
```bash
search-fusion-mcp
```

**手动覆盖**（如需要）：
```bash
env HTTP_PROXY="http://your-proxy:port" search-fusion-mcp
```

### 📊 检测过程
```
🔍 检查环境变量...
🔍 扫描代理端口: [7890, 1087, 8080, ...]
✅ 检测到本地代理端口: 7890
🌐 自动检测到代理: http://127.0.0.1:7890
```

### 🆚 与concurrent-browser-mcp对比

| 功能特性 | Search-Fusion | concurrent-browser-mcp |
|---------|---------------|------------------------|
| **检测方法** | ✅ 环境变量 → 端口扫描 → 系统代理 | ✅ 相同策略 |
| **端口列表** | ✅ 7个常见端口 | ✅ 7个常见端口 |
| **连接测试** | ✅ Socket测试 | ✅ Socket测试 |
| **超时设置** | ✅ 3秒 | ✅ 3秒 |
| **macOS支持** | ✅ networksetup | ✅ networksetup |
| **实现语言** | Python | TypeScript |

### MCP集成

#### 环境变量配置（推荐）

Search Fusion 现在使用**纯MCP环境变量配置**，无需配置文件。

**MCP客户端配置（PyPI安装）：**
```json
{
  "mcp": {
    "mcpServers": {
      "search-fusion": {
        "command": "search-fusion-mcp",
        "env": {
          "GOOGLE_API_KEY": "your_google_api_key",
          "GOOGLE_CSE_ID": "your_google_cse_id",
          "SERPER_API_KEY": "your_serper_api_key",
          "JINA_API_KEY": "your_jina_api_key",
          "EXA_API_KEY": "your_exa_api_key",
          "BING_API_KEY": "your_bing_api_key",
          "BAIDU_API_KEY": "your_baidu_api_key",
          "BAIDU_SECRET_KEY": "your_baidu_secret_key"
        }
      }
    }
  }
}
```

**MCP客户端配置（源码安装）：**
```json
{
  "mcp": {
    "mcpServers": {
      "search-fusion": {
        "command": "python",
        "args": ["-m", "src.main"],
        "cwd": "/path/to/your/search-fusion-mcp",
        "env": {
          "GOOGLE_API_KEY": "your_google_api_key",
          "GOOGLE_CSE_ID": "your_google_cse_id",
          "SERPER_API_KEY": "your_serper_api_key",
          "JINA_API_KEY": "your_jina_api_key",
          "EXA_API_KEY": "your_exa_api_key",
          "BING_API_KEY": "your_bing_api_key",
          "BAIDU_API_KEY": "your_baidu_api_key",
          "BAIDU_SECRET_KEY": "your_baidu_secret_key"
        }
      }
    }
  }
}
```

#### 支持的环境变量

| 搜索引擎 | 环境变量 | 必需参数 | 说明 | 获取API密钥 |
|---------|----------|----------|------|-------------|
| Google | `GOOGLE_API_KEY`<br>`GOOGLE_CSE_ID` | 两个都需要 | Google自定义搜索API | [获取API密钥](https://developers.google.com/custom-search/v1/introduction) |
| Serper | `SERPER_API_KEY` | API密钥 | Serper Google搜索API | [获取API密钥](https://serper.dev/) |
| Jina AI | `JINA_API_KEY` | API密钥 | Jina AI搜索API | [获取API密钥](https://jina.ai/) |
| Bing | `BING_API_KEY` | API密钥 | 微软Bing搜索API | [获取API密钥](https://www.microsoft.com/en-us/bing/apis/bing-web-search-api) |
| 百度 | `BAIDU_API_KEY`<br>`BAIDU_SECRET_KEY` | 两个都需要 | 百度搜索API | [获取API密钥](https://ai.baidu.com/) |
| Exa | `EXA_API_KEY` | API密钥 | Exa AI搜索API | [获取API密钥](https://exa.ai/) |
| DuckDuckGo | 无需配置 | - | 免费使用，无需API密钥 | - |

**备用变量名:**
```bash
# Google
GOOGLE_SEARCH_API_KEY    # 备用 GOOGLE_API_KEY
GOOGLE_SEARCH_CSE_ID     # 备用 GOOGLE_CSE_ID

# Serper
SERPER_SEARCH_API_KEY    # 备用 SERPER_API_KEY

# 其他引擎遵循类似模式...
```

### 引擎优先级

搜索引擎自动按优先级排序：
1. **Google搜索**（优先级1）- 需要API密钥，性能最佳
2. **Serper搜索**（优先级1）- Google替代方案，功能强大
3. **Jina AI搜索**（优先级1.5）- AI驱动搜索，API密钥可选（提供高级功能）
4. **DuckDuckGo**（优先级2）- 免费，无需API密钥
5. **Exa搜索**（优先级2）- AI驱动的搜索，需要API密钥
6. **Bing搜索**（优先级3）- 微软搜索API
7. **百度搜索**（优先级3）- 中文搜索引擎

## 🛠️ MCP工具

![工具概览](assets/tools.png)

### 1. `search`
执行网络搜索，具有智能引擎选择和故障转移功能。

**参数：**
- `query`（必需）：搜索查询词
- `num_results`（默认：10）：返回结果数量
- `engine`（默认："auto"）：引擎偏好
  - `"auto"`：自动引擎选择（推荐）
  - `"google"`：优先使用Google搜索
  - `"serper"`：优先使用Serper搜索
  - `"jina"`：优先使用Jina AI搜索
  - `"duckduckgo"`：优先使用DuckDuckGo
  - `"exa"`：优先使用Exa搜索
  - `"bing"`：优先使用Bing搜索
  - `"baidu"`：优先使用百度搜索

### 2. `fetch_url`
抓取和处理网页内容，具有智能分页和多方法回退。

**参数：**
- `url`（必需）：要抓取的网页URL
- `use_jina`（默认：true）：是否优先使用Jina Reader进行LLM优化内容
- `with_image_alt`（默认：false）：是否为图片生成替代文本
- `max_length`（默认：50000）：每页最大内容长度（超出时自动分页）
- `page_number`（默认：1）：从先前获取的内容中检索特定页面

**功能特性：**
- **智能多方法回退**：尝试 Jina Reader → Serper Scrape → 直接HTTP
- **自动分页处理**：将大型内容分割为可管理的页面
- **并发安全缓存**：唯一页面ID防止高并发场景下的冲突
- **LLM优化内容**：清洁的markdown格式，专为AI处理优化

### 3. `get_available_engines`
获取所有搜索引擎的当前状态和可用性。

### 4. `search_wikipedia`
搜索Wikipedia文章，查找实体、人物、地点、概念等。

**参数：**
- `entity`（必需）：要搜索的实体
- `first_sentences`（默认：10）：返回的句子数量（设为0返回全文）

### 5. `search_archived_webpage`
使用Wayback Machine搜索网站的历史存档版本。

**参数：**
- `url`（必需）：要搜索的网站URL
- `year`（可选）：目标年份
- `month`（可选）：目标月份
- `day`（可选）：目标日期



## 📖 API示例

### 基础搜索
```python
# 自动引擎选择
result = await search("人工智能趋势 2024")

# 优先特定引擎
result = await search("机器学习", engine="google")
```

### 高级网页抓取
```python
# 带智能分页的抓取
result = await fetch_url("https://example.com/long-article")

# 如果内容被分页，获取额外页面
if result.get("is_paginated"):
    page_2 = await get_page(result["page_id"], 2)
```

### Wikipedia搜索
```python
# 获取Wikipedia摘要
result = await search_wikipedia("Python编程语言")

# 获取完整文章
result = await search_wikipedia("量子计算", first_sentences=0)
```

## 🧪 开发

### 开发设置
```bash
git clone https://github.com/sailaoda/search-fusion-mcp.git
cd search-fusion-mcp
pip install -r requirements.txt
pip install -e .
```

## 🔧 配置指南

详细配置说明请参见 [MCP_CONFIG_GUIDE.md](MCP_CONFIG_GUIDE.md)。

## 📊 性能

- **延迟**：缓存下毫秒级响应时间
- **可用性**：智能故障转移保证99.9%正常运行时间
- **吞吐量**：高效处理并发请求
- **可扩展性**：高效的资源利用和并发处理

## 🤝 贡献

1. Fork仓库
2. 创建功能分支
3. 进行更改
4. 为新功能添加测试
5. 提交拉取请求

## 📄 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件。

## 🚨 限速和最佳实践

- **Google搜索**：100次查询/天（免费层）
- **Serper API**：根据计划变化
- **Jina AI**：根据订阅应用限速
- **DuckDuckGo**：无官方限制，但请负责使用
- **其他引擎**：查看相应的API文档

始终实施适当的延迟并尊重限速，以确保可持续使用。

## 📞 支持

- 📖 [文档](https://github.com/sailaoda/search-fusion-mcp)
- 🐛 [问题跟踪器](https://github.com/sailaoda/search-fusion-mcp/issues)
- 💬 [讨论](https://github.com/sailaoda/search-fusion-mcp/discussions)

---

**为MCP社区用❤️制作**