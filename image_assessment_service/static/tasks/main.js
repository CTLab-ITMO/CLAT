// const taskId

document.addEventListener('DOMContentLoaded', async function() {
    if (document.startup !== undefined) {
        await document.startup();
    }
    // Устанавливаем task_id в кнопке
    document.getElementById('task-id').textContent = `#${taskId}`;
    
    // Загружаем данные задачи
    try {
        const response = await fetch(`/api/tasks/${taskId}`);
        if (!response.ok) {
            throw new Error('Ошибка загрузки данных');
        }
        const taskData = await response.json();
        
        // Заполняем страницу данными
        document.getElementById('task-title').textContent = taskData.title;
        document.getElementById('task-description').textContent = taskData.description;
        document.getElementById('num-images').textContent = taskData.num_images;
        
        if (taskData.instructions) {
            document.getElementById('task-instructions').textContent = taskData.instructions;
        } else {
            document.querySelector('#task-instructions').parentElement.style.display = 'none';
        }
        
        // Заполняем метки
        if (taskData.bbox_labels && taskData.bbox_labels.length > 0) {
            taskData.bbox_labels.forEach(label => {
                const li = document.createElement('li');
                li.className = 'label-item';
                li.textContent = label;
                document.getElementById('bbox-labels').appendChild(li);
            });
        } else {
            document.querySelector('#bbox-labels').parentElement.style.display = 'none';
        }
        
        if (taskData.segmentation_labels && taskData.segmentation_labels.length > 0) {
            taskData.segmentation_labels.forEach(label => {
                const li = document.createElement('li');
                li.className = 'label-item';
                li.textContent = label;
                document.getElementById('segmentation-labels').appendChild(li);
            });
        } else {
            document.querySelector('#segmentation-labels').parentElement.style.display = 'none';
        }
        
        // Заполняем ID изображений
        if (taskData.image_names && taskData.image_names.length > 0) {
            taskData.image_names.forEach(id => {
                const div = document.createElement('div');
                div.className = 'image-id';
                div.textContent = id;
                document.getElementById('image-ids').appendChild(div);
            });
        } else {
            document.querySelector('#image-ids').parentElement.style.display = 'none';
        }
        
    } catch (error) {
        console.error('Ошибка:', error);
        document.getElementById('task-title').textContent = 'Ошибка загрузки данных';
        document.getElementById('task-description').textContent = error.message;
    }
});