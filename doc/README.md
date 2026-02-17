# 待办清单项目文档

## 项目概述

这是一个简洁美观的待办清单网页应用，支持添加、完成、删除任务，并使用 LocalStorage 实现数据持久化。

---

## 版本信息

| 版本号 | 发布日期 | 说明 |
|--------|----------|------|
| v1.1.0 | 2026-02-18 | 新增 MQTT 客户端工具集（JS/Python/Java/C#/Go） |
| v1.0.0 | 2026-02-18 | 初始版本，实现基础功能 |

---

## 环境要求

### 运行环境
- **浏览器**：Chrome 80+、Firefox 75+、Safari 13+、Edge 80+
- **无需服务器**：可直接双击 `index.html` 在浏览器中打开

### 开发环境
- **代码编辑器**：Visual Studio Code（推荐）
- **版本控制**：Git 2.x

---

## 操作文档

### 功能说明

#### 1. 添加任务
- 在输入框中输入任务内容
- 点击「添加」按钮或按 `Enter` 键添加任务
- 空内容不会添加

#### 2. 完成任务
- 点击任务文字可切换完成状态
- 完成的任务会显示**划线效果**并变灰

#### 3. 删除任务
- 点击任务右侧的 `✕` 按钮删除任务

#### 4. 数据持久化
- 任务数据自动保存在浏览器 LocalStorage 中
- 刷新页面或关闭浏览器后重新打开，任务仍会保留

---

## 项目结构

```
w:\代办清单\
├── index.html          # 主页面
├── style.css           # 样式文件
├── app.js              # 交互逻辑
├── doc/
│   ├── README.md       # 项目文档
│   └── PROMPTS.md      # 提示词记录
└── utils/
    └── mqtt/           # MQTT 客户端工具集
        ├── README.md           # 工具文档
        ├── mqtt-client.js      # JavaScript 客户端
        ├── mqtt_client.py      # Python 客户端
        ├── MqttClient.java     # Java 客户端
        ├── MqttClient.cs       # C# 客户端
        └── mqtt_client.go      # Go 客户端
```

---

## 技术栈

| 技术 | 用途 |
|------|------|
| HTML5 | 页面结构 |
| CSS3 | 样式设计（Flexbox、渐变、动画） |
| JavaScript (ES6) | 交互逻辑 |
| LocalStorage | 数据持久化 |

---

## 版本控制

本项目使用 Git 进行版本管理。

### 常用命令

```bash
# 查看当前状态
git status

# 查看提交历史
git log --oneline

# 查看版本差异
git diff v1.0.0 HEAD

# 创建新版本标签
git tag -a v1.1.0 -m "版本说明"