var user;
var annotations;
var tasks;
 
 // Загрузка данных пользователя
document.addEventListener('DOMContentLoaded', async function() {
    // Загрузка данных профиля
    try {
        const response = await fetch('/api/current-user');
        user = await response.json();
        
        document.getElementById('username').textContent = user.nickname;
        document.getElementById('user-email').textContent = user.email;
        document.getElementById('user-id').textContent = user.id;

        if (user.roles.includes('admin') || user.roles.includes('teacher')) {
            document.getElementById('create-task-btn').style.visibility = 'visible';
        }
        
        document.getElementById('logout-btn').addEventListener('click', function() {
            if (confirm('Вы уверены, что хотите выйти из аккаунта?')) {
                sessionStorage.clear();
                window.location.replace('/assess/users/auth/');
            }
        });

        annotations = await (await fetch('/api/user-annotations')).json();
        // Загрузка заданий
        loadUserTasks();
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
    }
});

function buildTaskCard(task) {

    const isAdmin = user.roles.includes('admin');
    const hasAnnotation = annotations.map(v => v.task_id).includes(task.id);
    const isOwner = task.user_id == user.id;

    if (!(isAdmin || hasAnnotation || isOwner)) {
        return undefined;
    }

    const taskCard = document.createElement('div');
    taskCard.className = 'task-card';
    taskCard.onclick = () => { window.location.href=`/tasks/${task.id}` }
    taskCard.innerHTML = `
        <div class="task-content">
            <div class="task-main">
                <h3 class="task-title">${task.title}</h3>
                <p class="task-description">${task.description}</p>
            </div>
                <div class="task-meta">
                ${hasAnnotation ? '<div class="meta-text">В работе</div>' : ''}
                ${isOwner ? '<div class="meta-text">Создано вами</div>' : ''}
            </div>
            ${(isOwner || isAdmin) ? `
            <button class="manage-btn" onclick="event.stopPropagation(); window.location.href='/tasks/manage/${task.id}'">
                Управлять
            </button>
            ` : ''}
        </div>
        </div>
        <div class="task-footer">
            <span class="task-status status-${task.status}">
                ${getStatusText(task.status)}
            </span>
            <span>${new Date(task.created_at).toLocaleDateString()}</span>
        </div>
    `;
    return taskCard;
}

// Загрузка заданий пользователя
async function loadUserTasks() {
    const container = document.getElementById('user-tasks-container');
    
    try {
        const response = await fetch('/api/tasks');
        const tasks = await response.json();
        
        container.innerHTML = '';
        
        tasks.forEach(task => {
            const taskCard = buildTaskCard(task);
            if (taskCard !== undefined) {
                container.appendChild(taskCard);
            }
        });
    } catch (error) {
        container.innerHTML = `
            <div class="error-message">
                Не удалось загрузить задания. Пожалуйста, попробуйте позже.
            </div>
        `;
        console.error('Ошибка загрузки заданий:', error);
    }
}

function getStatusText(status) {
    const statuses = {
        'completed': 'Завершено',
        'in_progress': 'В работе',
        'pending': 'Ожидает проверки'
    };
    return statuses[status] || status;
}