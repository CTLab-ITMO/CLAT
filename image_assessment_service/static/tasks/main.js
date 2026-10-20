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
        
        // Заполняем основные данные
        document.getElementById('task-title').textContent = taskData.title;
        document.getElementById('task-description').textContent = taskData.description;
        document.getElementById('num-images').textContent = taskData.num_images;
        document.getElementById('task-instructions').textContent = taskData.instructions;
        
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
        
        // Заполняем метки изображений
        if (taskData.image_labels && taskData.image_labels.length > 0) {
            taskData.image_labels.forEach(label => {
                const li = document.createElement('li');
                li.className = 'label-item';
                li.textContent = label;
                document.getElementById('image-labels').appendChild(li);
            });
        } else {
            document.querySelector('#image-labels').parentElement.style.display = 'none';
        }
        
        // Заполняем атрибуты
        const attributesContainer = document.getElementById('attributes-list');
        
        if (taskData.attributes && Object.keys(taskData.attributes).length > 0) {
            Object.entries(taskData.attributes).forEach(([_, config]) => {
                const attributeCard = document.createElement('div');
                attributeCard.className = 'attribute-card';
                
                const nameElement = document.createElement('div');
                nameElement.className = 'attribute-name';
                nameElement.textContent = config.key;
                attributeCard.appendChild(nameElement);
                
                const typeElement = document.createElement('div');
                typeElement.className = 'attribute-type';
                
                // Определяем класс для типа
                let typeClass = '';
                switch(config.type) {
                    case 'number':
                        typeClass = 'type-number';
                        break;
                    case 'flag':
                        typeClass = 'type-flag';
                        break;
                    case 'categorical':
                        typeClass = 'type-categorical';
                        break;
                    case 'text':
                        typeClass = 'type-text';
                        break;
                    default:
                        typeClass = '';
                }
                
                typeElement.innerHTML = `Тип: <span class="type-badge ${typeClass}">${config.type}</span>`;
                attributeCard.appendChild(typeElement);
                
                // Добавляем варианты для категориальных атрибутов
                if (config.type === 'categorical' && config.options && config.options.length > 0) {
                    const optionsElement = document.createElement('div');
                    optionsElement.className = 'attribute-options';
                    
                    const optionsTitle = document.createElement('span');
                    optionsTitle.textContent = 'Варианты:';
                    optionsElement.appendChild(optionsTitle);
                    
                    const optionsList = document.createElement('ul');
                    config.options.forEach(option => {
                        const optionItem = document.createElement('li');
                        optionItem.textContent = option;
                        optionsList.appendChild(optionItem);
                    });
                    
                    optionsElement.appendChild(optionsList);
                    attributeCard.appendChild(optionsElement);
                }
                
                attributesContainer.appendChild(attributeCard);
            });
        } else {
            document.querySelector('#attributes-list').parentElement.style.display = 'none';
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
