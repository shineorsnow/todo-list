// 获取 DOM 元素
const taskInput = document.getElementById('taskInput');
const addBtn = document.getElementById('addBtn');
const taskList = document.getElementById('taskList');
const emptyState = document.getElementById('emptyState');

// 从 LocalStorage 加载任务
let tasks = JSON.parse(localStorage.getItem('tasks')) || [];

// 初始化渲染
renderTasks();

// 添加任务事件
addBtn.addEventListener('click', addTask);
taskInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        addTask();
    }
});

// 添加任务函数
function addTask() {
    const text = taskInput.value.trim();
    if (!text) {
        taskInput.focus();
        return;
    }
    
    const task = {
        id: Date.now(),
        text: text,
        completed: false
    };
    
    tasks.push(task);
    saveTasks();
    renderTasks();
    
    taskInput.value = '';
    taskInput.focus();
}

// 切换任务完成状态
function toggleTask(id) {
    const task = tasks.find(t => t.id === id);
    if (task) {
        task.completed = !task.completed;
        saveTasks();
        renderTasks();
    }
}

// 删除任务
function deleteTask(id) {
    tasks = tasks.filter(t => t.id !== id);
    saveTasks();
    renderTasks();
}

// 保存任务到 LocalStorage
function saveTasks() {
    localStorage.setItem('tasks', JSON.stringify(tasks));
}

// 渲染任务列表
function renderTasks() {
    taskList.innerHTML = '';
    
    // 显示/隐藏空状态
    if (tasks.length === 0) {
        emptyState.classList.remove('hidden');
    } else {
        emptyState.classList.add('hidden');
    }
    
    // 渲染每个任务
    tasks.forEach(task => {
        const li = document.createElement('li');
        li.className = `task-item ${task.completed ? 'completed' : ''}`;
        
        li.innerHTML = `
            <span class="task-text" onclick="toggleTask(${task.id})">${escapeHtml(task.text)}</span>
            <button class="delete-btn" onclick="deleteTask(${task.id})" title="删除">✕</button>
        `;
        
        taskList.appendChild(li);
    });
}

// 防止 XSS 攻击
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}