// API 模块
const API = {
    // 认证相关
    async login(username, password) {
        const response = await fetch(`${CONFIG.API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });
        return response.json();
    },
    
    async register(username, password, email) {
        const response = await fetch(`${CONFIG.API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password, email })
        });
        return response.json();
    },
    
    async logout() {
        const response = await fetch(`${CONFIG.API_BASE}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        return response.json();
    },
    
    async getCurrentUser() {
        const response = await fetch(`${CONFIG.API_BASE}/auth/me`, {
            credentials: 'include'
        });
        return response.json();
    },
    
    // 任务相关
    async getTasks() {
        const response = await fetch(`${CONFIG.API_BASE}/tasks`, {
            credentials: 'include'
        });
        return response.json();
    },
    
    async createTask(task) {
        const response = await fetch(`${CONFIG.API_BASE}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(task)
        });
        return response.json();
    },
    
    async updateTask(taskId, data) {
        const response = await fetch(`${CONFIG.API_BASE}/tasks/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        return response.json();
    },
    
    async deleteTask(taskId) {
        const response = await fetch(`${CONFIG.API_BASE}/tasks/${taskId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        return response.json();
    },
    
    // 日历事件
    async getCalendarEvents(start, end) {
        let url = `${CONFIG.API_BASE}/calendar?`;
        if (start) url += `start=${start}`;
        if (end) url += `&end=${end}`;
        
        const response = await fetch(url, {
            credentials: 'include'
        });
        return response.json();
    },
    
    async createEvent(event) {
        const response = await fetch(`${CONFIG.API_BASE}/calendar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(event)
        });
        return response.json();
    },
    
    async updateEvent(eventId, data) {
        const response = await fetch(`${CONFIG.API_BASE}/calendar/${eventId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        return response.json();
    },
    
    async deleteEvent(eventId) {
        const response = await fetch(`${CONFIG.API_BASE}/calendar/${eventId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        return response.json();
    },
    
    // 统计数据
    async getStats() {
        const response = await fetch(`${CONFIG.API_BASE}/stats`, {
            credentials: 'include'
        });
        return response.json();
    }
};