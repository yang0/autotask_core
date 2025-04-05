# AutoTask Core 插件

AutoTask的核心插件，提供以下基础组件：

## 组件说明

### nodes/
工作流节点，用于自动化流程：
- 迭代器和布尔条件节点，用于流程控制
- 时间操作节点，用于时间处理
- 文件操作节点，用于文件系统任务
- 助手节点，用于LLM交互

### embedder/
Embedding模型集成类：
- 向量embedding生成
- 支持多种模型
- 知识库构建工具

### reader/
用于构建知识库的文档阅读器：
- 支持格式：TXT, MD, CSV, JSON, XML, HTML, LOG
- 智能文本分块
- 元数据提取
- 特定格式处理器

### assistant/
构建AI助手的基础类：
- 助手框架
- LLM集成
- 函数调用系统



