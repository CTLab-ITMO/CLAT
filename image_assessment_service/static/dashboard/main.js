document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/tasks/');
        if (!response.ok) throw new Error('Ошибка загрузки задач');
        
        const tasks = await response.json();
        renderTasks(tasks);
    } catch (error) {
        showError(error.message);
    }
});

function renderTasks(tasks) {
    const container = document.getElementById('tasks-container');
    
    if (tasks.length === 0) {
        container.innerHTML = `
            <div class="error-message">
                Нет доступных задач
            </div>
        `;
        return;
    }
    

    // <div class="benefits-list">
    // ${task.benefits.map(benefit => `
    //     <div class="benefit-item">
    //         <span class="benefit-name">${benefit.name}</span>
    //         <span class="benefit-value">${benefit.value}</span>
    //     </div>
    // `).join('')}
    // </div>

    container.innerHTML = `
        <div class="tasks-grid">
            ${tasks.map(task => `
                <div class="task-card" onclick="window.location.href='/tasks/${task.id}'">
                    <div class="task-content">
                        <h2 class="task-title">${task.title}</h2>
                        <p class="task-description">${task.description}</p>
                        
                        ${task.instructions ? `
                            <div class="task-instructions">
                                ${task.instructions}
                            </div>
                        ` : ''}
                        

                    </div>
                    
                    <div class="task-footer">
                        <div class="task-status status-${task.status}">
                            ${getStatusText(task.status)}
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function getStatusText(status) {
    const statusMap = {
        'available': 'Доступно',
        'in_progress': 'В работе',
        'unavailable': 'Недоступно'
    };
    return statusMap[status] || status;
}

function showError(message) {
    document.getElementById('tasks-container').innerHTML = `
        <div class="error-message">
            ${message}<br>
            <button onclick="window.location.reload()">Попробовать снова</button>
        </div>
    `;
}