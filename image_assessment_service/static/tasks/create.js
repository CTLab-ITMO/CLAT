document.addEventListener('DOMContentLoaded', function() {
    // Элементы DOM
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.getElementById('uploadArea');
    const previewContainer = document.getElementById('previewContainer');
    const bboxInput = document.getElementById('bboxInput');
    const addBboxTag = document.getElementById('addBboxTag');
    const bboxTags = document.getElementById('bboxTags');
    const segmentationInput = document.getElementById('segmentationInput');
    const addSegmentationTag = document.getElementById('addSegmentationTag');
    const segmentationTags = document.getElementById('segmentationTags');
    const taskForm = document.getElementById('taskForm');
    const submitBtn = document.getElementById('submitBtn');
    const submitText = document.getElementById('submitText');
    const submitSpinner = document.getElementById('submitSpinner');
    const successMessage = document.getElementById('successMessage');
    // const progressContainer = document.getElementById('progressContainer');
    // const progressText = document.getElementById('progressText');
    // const batchInfo = document.getElementById('batchInfo');
    const uploadProgress = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const statusText = document.getElementById('statusText');

    // Конфигурация
    const MAX_FILES_PER_BATCH = 2; // Обрабатывать по 20 файлов за раз
    const MAX_FILE_SIZE_MB = 5;
    const MAX_TOTAL_FILES = 500; // Максимум 200 файлов
    
    // Массивы для хранения данных
    let images = [];
    let bboxLabels = [];
    let segmentationLabels = [];
    
    // Обработчики для загрузки изображений
    uploadArea.addEventListener('click', () => fileInput.click());
    
    fileInput.addEventListener('change', handleFileSelect);
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim();
        uploadArea.style.backgroundColor = 'rgba(67, 97, 238, 0.05)';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.borderColor = '#ddd';
        uploadArea.style.backgroundColor = 'transparent';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = '#ddd';
        uploadArea.style.backgroundColor = 'transparent';
        
        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileSelect({ target: fileInput });
        }
    });
    
    async function handleFileSelect(event) {
        const files = Array.from(event.target.files);
        if (files.length === 0) return;
        
        // Проверка общего количества файлов
        if (images.length + files.length > MAX_TOTAL_FILES) {
            alert(`Максимальное количество файлов: ${MAX_TOTAL_FILES}. Вы пытаетесь загрузить ${images.length + files.length}`);
            return;
        }
        
        // Показываем прогресс-бар
        progressContainer.style.display = 'block';
        batchInfo.textContent = `Обработка ${files.length} файлов...`;
        
        // Обрабатываем файлы батчами
        for (let i = 0; i < files.length; i += MAX_FILES_PER_BATCH) {
            const batch = files.slice(i, i + MAX_FILES_PER_BATCH);
            await processBatch(batch, files.length, i);
        }
        
        updatePreview();
        progressContainer.style.display = 'none';
        batchInfo.textContent = `Загружено ${images.length} файлов`;
    }

    async function processBatch(batch, totalFiles, startIndex) {
        const promises = batch.map((file, batchIndex) => {
            return new Promise((resolve) => {
                // Проверка размера файла
                if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
                    batchInfo.textContent += `\nФайл ${file.name} слишком большой (максимум ${MAX_FILE_SIZE_MB}MB)`;
                    return resolve();
                }
                
                // Проверка на дубликаты
                if (images.some(img => img.name === file.name)) {
                    return resolve();
                }
                
                const reader = new FileReader();
                reader.onload = (e) => {
                    images.push({
                        name: file.name,
                        data: e.target.result
                    });
                    
                    // Обновляем прогресс
                    const processed = startIndex + batchIndex + 1;
                    const progress = Math.round((processed / totalFiles) * 100);
                    updateProgress(progress, processed, totalFiles);
                    
                    resolve();
                };
                reader.onerror = () => resolve();
                reader.readAsDataURL(file);
            });
        });
        
        await Promise.all(promises);
    }

    function updateProgress(percent, processed, total) {
        progressBar.style.width = `${percent}%`;
        progressText.textContent = `${percent}% (${processed}/${total})`;
    }
    
    function updatePreview() {
        previewContainer.innerHTML = '';
        images.forEach((image, index) => {
            const item = document.createElement('div');
            item.className = 'preview-item';
            
            const img = document.createElement('img');
            img.src = image.data;
            img.alt = image.name;
            
            const removeBtn = document.createElement('div');
            removeBtn.className = 'remove-btn';
            removeBtn.innerHTML = '<i class="fas fa-times"></i>';
            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                images.splice(index, 1);
                updatePreview();
            });
            
            item.appendChild(img);
            item.appendChild(removeBtn);
            previewContainer.appendChild(item);
        });
    }
    
    // Обработчики для меток
    function createTag(label, container, array) {
        const tag = document.createElement('div');
        tag.className = 'tag';
        
        const tagText = document.createElement('span');
        tagText.textContent = label;
        
        const removeBtn = document.createElement('span');
        removeBtn.className = 'tag-remove';
        removeBtn.innerHTML = '<i class="fas fa-times"></i>';
        removeBtn.addEventListener('click', () => {
            const index = array.indexOf(label);
            if (index > -1) {
                array.splice(index, 1);
                container.removeChild(tag);
            }
        });
        
        tag.appendChild(tagText);
        tag.appendChild(removeBtn);
        container.appendChild(tag);
    }
    
    addBboxTag.addEventListener('click', () => {
        const label = bboxInput.value.trim();
        if (label && !bboxLabels.includes(label)) {
            bboxLabels.push(label);
            createTag(label, bboxTags, bboxLabels);
            bboxInput.value = '';
        }
    });
    
    bboxInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addBboxTag.click();
        }
    });
    
    addSegmentationTag.addEventListener('click', () => {
        const label = segmentationInput.value.trim();
        if (label && !segmentationLabels.includes(label)) {
            segmentationLabels.push(label);
            createTag(label, segmentationTags, segmentationLabels);
            segmentationInput.value = '';
        }
    });
    
    segmentationInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addSegmentationTag.click();
        }
    });

    function formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat(bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i];
    }

    async function getOriginalFileObjects() {
        const fileInput = document.getElementById('fileInput');
        return Array.from(fileInput.files);
    }

    async function doWithRetries(asyncFunc, maxRetries=5, firstTimeout=200) {
        let lastError = null;
        
        for (let i = 0; i < maxRetries; i++) {
            try {
                return await asyncFunc();
            } catch (error) {
                lastError = error;
                await new Promise(resolve => setTimeout(resolve, firstTimeout * (i + 1))); // Экспоненциальная задержка
            }
        }
        throw lastError; // Если все попытки исчерпаны
    }

    async function finishUpload(taskId) {
        console.log("FINISH");
        await doWithRetries(async () => {
            const response = await fetch(`/api/tasks/${taskId}/finish-upload`, {
                method: 'POST'
            });
            console.log(response);
            if (response.ok) return;
            console.log("CANT");
            throw new Error(`HTTP error! status: ${response.status}`);
        });
    }

    taskForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // if (!validateForm()) return;

        // Блокируем кнопку отправки
        submitBtn.disabled = true;
        uploadProgress.style.display = 'block';
        statusText.textContent = 'Подготовка к загрузке...';
        statusText.className = 'status';

        try {
            taskId = await submitFormData();

            const files = fileInput.files;
            if (files.length > 0) {
                await uploadFiles(taskId, files);
            }

            await finishUpload(taskId);

            statusText.textContent = 'Задание успешно отправлено!';
            statusText.className = 'status';

            taskForm.reset();
            images = [];
            updatePreview();
            window.location.replace('/dashboard');
            
        } catch (error) {
            statusText.textContent = `Ошибка: ${error.message}`;
            statusText.className = 'status error';
        } finally {
            submitBtn.disabled = false;
        }
    });

    async function uploadFiles(taskId, files) {
        for (let i = 0; i < files.length; i++) {
            const file = files[i];

            await doWithRetries(async () => {
                await uploadSingleFile(taskId, file);
            });
        }
    }

    async function uploadSingleFile(taskId, file) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);
            
            const xhr = new XMLHttpRequest();
            xhr.open('POST', `/api/tasks/${taskId}/upload-file`, true);

            xhr.setRequestHeader('Authorization', token);
            xhr.setRequestHeader('X-Session-ID', storedSessionId);
            
            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    progressBar.style.width = percent + '%';
                }
            };
            
            xhr.onload = () => {
                if (xhr.status === 200) {
                    resolve();
                } else {
                    reject(new Error(xhr.statusText));
                }
            };
            
            xhr.onerror = () => reject(new Error('Ошибка сети'));
            xhr.send(formData);
        });
    }

    async function submitFormData() {
        const taskData = {
            title: document.getElementById('title').value.trim(),
            description: document.getElementById('description').value.trim(),
            instructions: document.getElementById('instructions').value.trim(),
            annotators_count: parseInt(document.getElementById('annotatorsCount').value),
            days_to_complete: parseInt(document.getElementById('daysToComplete').value),
            deadline: new Date(document.getElementById('deadline').value).toISOString(),
            bbox_labels: bboxLabels,
            segmentation_labels: segmentationLabels,
            num_images: images.length,
            image_names: images.map(it => it.name)
        };

        console.log(taskData)
        
        const response = await fetch('/api/tasks/init-upload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(taskData)
        });

        console.log(response.ok);

        if (!response.ok) {
            throw new Error('Ошибка сохранения данных задания');
        }

        result = await response.json();
        taskId = result['taskId'];

        console.log(result);

        if (taskId === undefined) {
            throw new Error('Ошибка сохранения данных задания');
        }

        return taskId;
    }
    
    function validateForm() {
        let isValid = true;
        
        if (!document.getElementById('title').value.trim()) {
            document.getElementById('titleError').textContent = 'Введите название задания';
            isValid = false;
        } else {
            document.getElementById('titleError').textContent = '';
        }
        
        if (!document.getElementById('description').value.trim()) {
            document.getElementById('descriptionError').textContent = 'Введите описание задания';
            isValid = false;
        } else {
            document.getElementById('descriptionError').textContent = '';
        }
        
        if (!document.getElementById('instructions').value.trim()) {
            document.getElementById('instructionsError').textContent = 'Введите инструкции по разметке';
            isValid = false;
        } else {
            document.getElementById('instructionsError').textContent = '';
        }
        
        if (images.length === 0) {
            document.getElementById('imagesError').textContent = 'Добавьте хотя бы одно изображение';
            isValid = false;
        } else {
            document.getElementById('imagesError').textContent = '';
        }
        
        if (bboxLabels.length === 0 && segmentationLabels.length === 0) {
            document.getElementById('bboxError').textContent = 'Добавьте хотя бы одну метку для bounding box или сегментации';
            document.getElementById('segmentationError').textContent = 'Добавьте хотя бы одну метку для bounding box или сегментации';
            isValid = false;
        } else {
            document.getElementById('bboxError').textContent = '';
            document.getElementById('segmentationError').textContent = '';
        }
        
        return isValid;
    }
});