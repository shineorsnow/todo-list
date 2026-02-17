// 主应用模块
const App = {
    currentUser: null,
    tasks: [],
    currentFilter: 'all',
    
    // 初始化
    async init() {
        // 检查登录状态
        await this.checkAuth();
        
        // 绑定事件
        this.bindEvents();
    },
    
    // 检查认证状态
    async checkAuth() {
        try {
            const result = await API.getCurrentUser();
            if (result.user) {
                this.currentUser = result.user;
                this.showMainPage();
            } else {
                this.showAuthPage();
            }
        } catch (error) {
            this.showAuthPage();
        }
    },
    
    // 显示登录页面
    showAuthPage() {
        document.getElementById('authPage').classList.remove('hidden');
        document.getElementById('mainPage').classList.add('hidden');
    },
    
    // 显示主页面
    async showMainPage() {
        document.getElementById('authPage').classList.add('hidden');
        document.getElementById('mainPage').classList.remove('hidden');
        
        // 显示用户名
        document.getElementById('currentUser').textContent = this.currentUser.username;
        
        // 加载数据
        await this.loadTasks();
        await this.loadStats();
        
        // 连接 MQTT
        await MQTT.connect((topic, data) => this.handleMQTTMessage(topic, data));
    },
    
    // 绑定事件
    bindEvents() {
        // 登录/注册标签切换
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
                
                btn.classList.add('active');
                document.getElementById(btn.dataset.tab + 'Form').classList.add('active');
            });
        });
        
        // 登录表单
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;
            
            try {
                const result = await API.login(username, password);
                if (result.user) {
                    this.currentUser = result.user;
                    this.showMainPage();
                } else {
                    document.getElementById('loginError').textContent = result.error || '登录失败';
                }
            } catch (error) {
                document.getElementById('loginError').textContent = '登录失败，请重试';
            }
        });
        
        // 注册表单
        document.getElementById('registerForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('regUsername').value;
            const email = document.getElementById('regEmail').value;
            const password = document.getElementById('regPassword').value;
            const confirmPassword = document.getElementById('regConfirmPassword').value;
            
            if (password !== confirmPassword) {
                document.getElementById('registerError').textContent = '两次密码不一致';
                return;
            }
            
            try {
                const result = await API.register(username, password, email);
                if (result.user) {
                    this.currentUser = result.user;
                    this.showMainPage();
                } else {
                    document.getElementById('registerError').textContent = result.error || '注册失败';
                }
            } catch (error) {
                document.getElementById('registerError').textContent = '注册失败，请重试';
            }
        });
        
        // 退出登录
        document.getElementById('logoutBtn').addEventListener('click', async () => {
            await API.logout();
            MQTT.disconnect();
            this.currentUser = null;
            this.showAuthPage();
        });
        
        // 视图切换
        document.querySelectorAll('.nav-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
                
                btn.classList.add('active');
                document.getElementById(btn.dataset.view + 'View').classList.add('active');
                
                if (btn.dataset.view === 'calendar') {
                    Calendar.render();
                }
            });
        });
        
        // 添加任务
        document.getElementById('addTaskBtn').addEventListener('click', () => this.addTask());
        document.getElementById('taskInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addTask();
        });
        
        // 筛选按钮
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentFilter = btn.dataset.filter;
                this.renderTasks();
            });
        });
    },
    
    // 加载任务
    async loadTasks() {
        try {
            const result = await API.getTasks();
            this.tasks = result.tasks || [];
            this.renderTasks();
        } catch (error) {
            console.error('加载任务失败:', error);
        }
    },
    
    // 加载统计数据
    async loadStats() {
        try {
            const stats = await API.getStats();
            document.getElementById('totalTasks').textContent = stats.total_tasks || 0;
            document.getElementById('completedTasks').textContent = stats.completed_tasks || 0;
            document.getElementById('pendingTasks').textContent = stats.pending_tasks || 0;
            document.getElementById('dueToday').textContent = stats.due_today || 0;
        } catch (error) {
            console.error('加载统计失败:', error);
        }
    },
    
    // 渲染任务列表
    renderTasks() {
        const taskList = document.getElementById('taskList');
        const emptyState = document.getElementById('emptyState');
        
        // 根据筛选条件过滤
        let filteredTasks = this.tasks;
        if (this.currentFilter === 'pending') {
            filteredTasks = this.tasks.filter(t => !t.completed);
        } else if (this.currentFilter === 'completed') {
            filteredTasks = this.tasks.filter(t => t.completed);
        } else if (this.currentFilter === 'high') {
            filteredTasks = this.tasks.filter(t => t.priority === 'high' && !t.completed);
        }
        
        if (filteredTasks.length === 0) {
            taskList.innerHTML = '';
            emptyState.classList.remove('hidden');
            return;
        }
        
        emptyState.classList.add('hidden');
        
        taskList.innerHTML = filteredTasks.map(task => `
            <li class="task-item ${task.completed ? 'completed' : ''}" data-id="${task.id}">
                <span class="task-priority ${task.priority}"></span>
                <div class="task-content">
                    <div class="task-title" onclick="App.toggleTask(${task.id})">${this.escapeHtml(task.title)}</div>
                    <div class="task-meta">
                        ${task.due_date ? `到期: ${new Date(task.due_date).toLocaleDateString()} | ` : ''}
                        优先级: ${this.getPriorityText(task.priority)}
                    </div>
                </div>
                <div class="task-actions">
                    <button class="btn-complete" onclick="App.toggleTask(${task.id})">
                        ${task.completed ? '撤销' : '完成'}
                    </button>
                    <button class="btn-delete" onclick="App.deleteTask(${task.id})">删除</button>
                </div>
            </li>
        `).join('');
    },
    
    // 添加任务
    async addTask() {
        const input = document.getElementById('taskInput');
        const title = input.value.trim();
        
        if (!title) return;
        
        const priority = document.getElementById('taskPriority').value;
        const dueDate = document.getElementById('taskDueDate').value;
        
        try {
            const result = await API.createTask({
                title,
                priority,
                due_date: dueDate || null
            });
            
            if (result.task) {
                this.tasks.unshift(result.task);
                this.renderTasks();
                this.loadStats();
                
                // 发布 MQTT 消息
                MQTT.publish(CONFIG.MQTT.topics.tasks, {
                    action: 'create',
                    user_id: this.currentUser.id,
                    task: result.task
                });
            }
        } catch (error) {
            console.error('添加任务失败:', error);
        }
        
        input.value = '';
    },
    
    // 切换任务状态
    async toggleTask(taskId) {
        const task = this.tasks.find(t => t.id === taskId);
        if (!task) return;
        
        try {
            const result = await API.updateTask(taskId, {
                completed: !task.completed
            });
            
            if (result.task) {
                const index = this.tasks.findIndex(t => t.id === taskId);
                this.tasks[index] = result.task;
                this.renderTasks();
                this.loadStats();
                
                // 发布 MQTT 消息
                MQTT.publish(CONFIG.MQTT.topics.tasks, {
                    action: 'update',
                    user_id: this.currentUser.id,
                    task: result.task
                });
            }
        } catch (error) {
            console.error('更新任务失败:', error);
        }
    },
    
    // 删除任务
    async deleteTask(taskId) {
        try {
            await API.deleteTask(taskId);
            this.tasks = this.tasks.filter(t => t.id !== taskId);
            this.renderTasks();
            this.loadStats();
            
            // 发布 MQTT 消息
            MQTT.publish(CONFIG.MQTT.topics.tasks, {
                action: 'delete',
                user_id: this.currentUser.id,
                task_id: taskId
            });
        } catch (error) {
            console.error('删除任务失败:', error);
        }
    },
    
    // 处理 MQTT 消息
    handleMQTTMessage(topic, data) {
        console.log('[App] 收到 MQTT 消息:', topic, data);
        
        if (topic === CONFIG.MQTT.topics.sync) {
            if (data.event === 'task_created') {
                // 其他客户端创建了任务
                this.loadTasks();
            } else if (data.event === 'task_updated') {
                // 更新本地任务
                const index = this.tasks.findIndex(t => t.id === data.data.id);
                if (index >= 0) {
                    this.tasks[index] = data.data;
                    this.renderTasks();
                    this.loadStats();
                }
            } else if (data.event === 'task_deleted') {
                // 删除本地任务
                this.tasks = this.tasks.filter(t => t.id !== data.data.id);
                this.renderTasks();
                this.loadStats();
            }
        }
    },
    
    // 辅助方法
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    getPriorityText(priority) {
        const map = { low: '低', normal: '普通', high: '高' };
        return map[priority] || '普通';
    }
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});