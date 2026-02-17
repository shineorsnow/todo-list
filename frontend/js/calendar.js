// 日历模块
const Calendar = {
    currentDate: new Date(),
    events: [],
    
    // 渲染日历
    async render() {
        await this.loadEvents();
        
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        
        // 更新标题
        const monthNames = ['一月', '二月', '三月', '四月', '五月', '六月',
                           '七月', '八月', '九月', '十月', '十一月', '十二月'];
        document.getElementById('currentMonth').textContent = `${year}年 ${monthNames[month]}`;
        
        // 获取当月第一天和最后一天
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        
        // 计算日历网格
        const startDay = firstDay.getDay(); // 星期几开始
        const totalDays = lastDay.getDate(); // 当月天数
        
        // 构建日历 HTML
        let html = '<div class="calendar-weekdays">';
        const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
        weekdays.forEach(day => {
            html += `<div>${day}</div>`;
        });
        html += '</div><div class="calendar-days">';
        
        // 上月日期
        const prevMonth = new Date(year, month, 0);
        const prevDays = prevMonth.getDate();
        for (let i = startDay - 1; i >= 0; i--) {
            const day = prevDays - i;
            html += `<div class="calendar-day other-month"><div class="day-number">${day}</div></div>`;
        }
        
        // 当月日期
        const today = new Date();
        for (let day = 1; day <= totalDays; day++) {
            const isToday = today.getFullYear() === year && 
                           today.getMonth() === month && 
                           today.getDate() === day;
            
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayEvents = this.events.filter(e => e.start_time.startsWith(dateStr));
            
            html += `<div class="calendar-day${isToday ? ' today' : ''}" data-date="${dateStr}">`;
            html += `<div class="day-number">${day}</div>`;
            
            if (dayEvents.length > 0) {
                html += '<div class="calendar-events">';
                dayEvents.slice(0, 3).forEach(event => {
                    html += `<div class="calendar-event" style="background:${event.color}" 
                             onclick="Calendar.showEvent(${event.id})">${event.title}</div>`;
                });
                if (dayEvents.length > 3) {
                    html += `<div class="calendar-event-more">+${dayEvents.length - 3} 更多</div>`;
                }
                html += '</div>';
            }
            
            html += '</div>';
        }
        
        // 下月日期
        const remaining = 42 - (startDay + totalDays);
        for (let day = 1; day <= remaining; day++) {
            html += `<div class="calendar-day other-month"><div class="day-number">${day}</div></div>`;
        }
        
        html += '</div>';
        
        document.getElementById('calendarGrid').innerHTML = html;
    },
    
    // 加载事件
    async loadEvents() {
        try {
            const year = this.currentDate.getFullYear();
            const month = this.currentDate.getMonth();
            
            const start = new Date(year, month, 1).toISOString();
            const end = new Date(year, month + 1, 0).toISOString();
            
            const result = await API.getCalendarEvents(start, end);
            this.events = result.events || [];
        } catch (error) {
            console.error('加载事件失败:', error);
        }
    },
    
    // 显示事件详情
    showEvent(eventId) {
        const event = this.events.find(e => e.id === eventId);
        if (event) {
            alert(`事件: ${event.title}\n时间: ${new Date(event.start_time).toLocaleString()}\n描述: ${event.description || '无'}`);
        }
    },
    
    // 绑定事件
    bindEvents() {
        // 上月
        document.getElementById('prevMonth').addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() - 1);
            this.render();
        });
        
        // 下月
        document.getElementById('nextMonth').addEventListener('click', () => {
            this.currentDate.setMonth(this.currentDate.getMonth() + 1);
            this.render();
        });
        
        // 添加事件按钮
        document.getElementById('addEventBtn').addEventListener('click', () => {
            this.showModal();
        });
        
        // 关闭模态框
        document.querySelector('.modal-close').addEventListener('click', () => {
            this.hideModal();
        });
        
        document.getElementById('cancelEventBtn').addEventListener('click', () => {
            this.hideModal();
        });
        
        // 提交事件表单
        document.getElementById('eventForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.saveEvent();
        });
    },
    
    // 显示模态框
    showModal(event = null) {
        document.getElementById('modalTitle').textContent = event ? '编辑事件' : '添加事件';
        document.getElementById('eventForm').reset();
        
        if (event) {
            document.getElementById('eventTitle').value = event.title;
            document.getElementById('eventStart').value = event.start_time.slice(0, 16);
            document.getElementById('eventEnd').value = event.end_time ? event.end_time.slice(0, 16) : '';
            document.getElementById('eventAllDay').checked = event.all_day;
            document.getElementById('eventColor').value = event.color;
            document.getElementById('eventDescription').value = event.description || '';
            this.editingEventId = event.id;
        } else {
            this.editingEventId = null;
        }
        
        document.getElementById('eventModal').classList.remove('hidden');
    },
    
    // 隐藏模态框
    hideModal() {
        document.getElementById('eventModal').classList.add('hidden');
        this.editingEventId = null;
    },
    
    // 保存事件
    async saveEvent() {
        const eventData = {
            title: document.getElementById('eventTitle').value,
            start_time: document.getElementById('eventStart').value + ':00',
            end_time: document.getElementById('eventEnd').value ? document.getElementById('eventEnd').value + ':00' : null,
            all_day: document.getElementById('eventAllDay').checked,
            color: document.getElementById('eventColor').value,
            description: document.getElementById('eventDescription').value
        };
        
        try {
            if (this.editingEventId) {
                await API.updateEvent(this.editingEventId, eventData);
            } else {
                await API.createEvent(eventData);
            }
            
            this.hideModal();
            this.render();
        } catch (error) {
            console.error('保存事件失败:', error);
            alert('保存失败，请重试');
        }
    }
};

// 页面加载完成后绑定事件
document.addEventListener('DOMContentLoaded', () => {
    Calendar.bindEvents();
});