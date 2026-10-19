document.addEventListener('DOMContentLoaded', function () {
    // DOM elements
    const bboxInput = document.getElementById('bboxInput');
    const addBboxTag = document.getElementById('addBboxTag');
    const bboxTags = document.getElementById('bboxTags');

    const segmentationInput = document.getElementById('segmentationInput');
    const addSegmentationTag = document.getElementById('addSegmentationTag');
    const segmentationTags = document.getElementById('segmentationTags');

    const imageTagsInput = document.getElementById('imageTagsInput');
    const addImageTag = document.getElementById('addImageTag');
    const imageTags = document.getElementById('imageTags');

    const taskForm = document.getElementById('taskForm');
    const submitBtn = document.getElementById('submitBtn');
    const statusText = document.getElementById('statusText');

    const uploadProgress = document.getElementById('uploadProgress');

    // Attributes elements
    const attributesContainer = document.getElementById('attributesContainer');
    const addAttributeBtn = document.getElementById('addAttributeBtn');

    // Config
    const MAX_FILES_PER_BATCH = 20;
    const MAX_FILE_SIZE_MB = 30;
    const MAX_TOTAL_FILES = 500;

    // Data storage
    let bboxLabels = [];
    let segmentationLabels = [];
    let imageLabels = [];
    let attributes = [];

    let uploadedFiles = {};
    let progressBars = {};

    // ---------------- FILE INPUTS INIT ----------------
    document.querySelectorAll('input[type="file"][name]').forEach(fileInput => {
        const inputName = fileInput.name;
        const wrapper = fileInput.closest('.form-group');

        const uploadArea = wrapper.querySelector('.upload-area');
        const previewContainer = wrapper.querySelector('.preview-container');
        const progressContainer = wrapper.querySelector('.progress-container');
        const progressBar = wrapper.querySelector('.progress-bar');
        const progressText = wrapper.querySelector('.progress-text');
        const batchInfo = wrapper.querySelector('.batch-info');

        progressBars[inputName] = progressBar;
        uploadedFiles[inputName] = {
            filesMeta: [],
            allSelectedFiles: []
        };

        uploadArea.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            handleFileSelect(
                e,
                inputName,
                previewContainer,
                progressContainer,
                progressBar,
                progressText,
                batchInfo
            );
        });

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = getComputedStyle(document.documentElement)
                .getPropertyValue('--primary-color')
                .trim();
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

                handleFileSelect(
                    { target: fileInput },
                    inputName,
                    previewContainer,
                    progressContainer,
                    progressBar,
                    progressText,
                    batchInfo
                );
            }
        });
    });

    async function handleFileSelect(event, inputName, previewContainer, progressContainer, progressBar, progressText, batchInfo) {
        const files = Array.from(event.target.files);
        if (files.length === 0) return;

        const store = uploadedFiles[inputName];

        if (event.target.multiple) {
            store.allSelectedFiles = [...store.allSelectedFiles, ...files];
        } else {
            store.allSelectedFiles = [...files];
            store.filesMeta = [];
        }

        if (store.allSelectedFiles.length > MAX_TOTAL_FILES) {
            alert(`Максимальное количество файлов: ${MAX_TOTAL_FILES}`);
            store.allSelectedFiles = store.allSelectedFiles.slice(0, MAX_TOTAL_FILES);
        }

        progressContainer.style.display = 'block';
        batchInfo.textContent = `Обработка ${files.length} файлов...`;

        for (let i = 0; i < files.length; i += MAX_FILES_PER_BATCH) {
            const batch = files.slice(i, i + MAX_FILES_PER_BATCH);
            await processBatch(
                batch,
                files.length,
                i,
                inputName,
                progressBar,
                progressText,
                batchInfo
            );
        }

        updatePreview(inputName, previewContainer);

        progressContainer.style.display = 'none';
        batchInfo.textContent = `Загружено ${store.filesMeta.length} файлов`;

        event.target.value = '';
    }

    async function processBatch(batch, totalFiles, startIndex, inputName, progressBar, progressText, batchInfo) {
        const store = uploadedFiles[inputName];

        const promises = batch.map((file, batchIndex) => {
            return new Promise((resolve) => {
                if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
                    batchInfo.textContent += `\n${file.name} слишком большой`;
                    return resolve();
                }

                if (store.filesMeta.some(item => item.name === file.name)) {
                    return resolve();
                }

                const reader = new FileReader();

                reader.onload = (e) => {
                    store.filesMeta.push({
                        name: file.name,
                        data: e.target.result,
                        type: file.type
                    });

                    const processed = startIndex + batchIndex + 1;
                    const progress = Math.round((processed / totalFiles) * 100);

                    updateProgress(progress, processed, totalFiles, progressBar, progressText);

                    resolve();
                };

                reader.onerror = () => resolve();

                reader.readAsDataURL(file);
            });
        });

        await Promise.all(promises);
    }

    function updateProgress(percent, processed, total, progressBar, progressText) {
        progressBar.style.width = `${percent}%`;
        progressText.textContent = `${percent}% (${processed}/${total})`;
    }

    function updatePreview(inputName, previewContainer) {
        const store = uploadedFiles[inputName];

        previewContainer.innerHTML = '';

        store.filesMeta.forEach((fileItem, index) => {
            const item = document.createElement('div');
            item.className = 'preview-item';

            if (fileItem.type && fileItem.type.startsWith('image/')) {
                const img = document.createElement('img');
                img.src = fileItem.data;
                img.alt = fileItem.name;
                item.appendChild(img);
            } else {
                const fileLabel = document.createElement('div');
                fileLabel.className = 'file-preview-name';
                fileLabel.textContent = fileItem.name;
                item.appendChild(fileLabel);
            }

            const removeBtn = document.createElement('div');
            removeBtn.className = 'remove-btn';
            removeBtn.innerHTML = '<i class="fas fa-times"></i>';

            removeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                store.filesMeta.splice(index, 1);
                store.allSelectedFiles.splice(index, 1);
                updatePreview(inputName, previewContainer);
            });

            item.appendChild(removeBtn);
            previewContainer.appendChild(item);
        });
    }

    // ---------------- TAGS ----------------
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

    addSegmentationTag.addEventListener('click', () => {
        const label = segmentationInput.value.trim();
        if (label && !segmentationLabels.includes(label)) {
            segmentationLabels.push(label);
            createTag(label, segmentationTags, segmentationLabels);
            segmentationInput.value = '';
        }
    });

    addImageTag.addEventListener('click', () => {
        const label = imageTagsInput.value.trim();
        if (label && !imageLabels.includes(label)) {
            imageLabels.push(label);
            createTag(label, imageTags, imageLabels);
            imageTagsInput.value = '';
        }
    });

    // ---------------- ATTRIBUTES ----------------
    addAttributeBtn.addEventListener('click', addAttribute);

    function addAttribute() {
        const attributeId = Date.now();

        const attribute = {
            id: attributeId,
            key: '',
            type: 'flag',
            options: []
        };

        attributes.push(attribute);

        const attributeItem = document.createElement('div');
        attributeItem.className = 'attribute-item';
        attributeItem.dataset.id = attributeId;

        attributeItem.innerHTML = `
            <div class="attribute-header">
                <div class="attribute-name">
                    <input type="text" class="form-control attribute-key" placeholder="Имя атрибута" required>
                </div>
                <div class="attribute-type">
                    <select class="form-control attribute-type-select">
                        <option value="flag">Флаг</option>
                        <option value="numeric">Числовой</option>
                        <option value="categorical">Категориальный</option>
                        <option value="text">Текстовый</option>
                    </select>
                </div>
                <span class="attribute-remove"><i class="fas fa-times"></i></span>
            </div>
            <div class="attribute-options">
                <div class="options-list"></div>
                <button type="button" class="btn btn-small add-option-btn">Добавить значение</button>
            </div>
        `;

        attributesContainer.appendChild(attributeItem);

        const removeBtn = attributeItem.querySelector('.attribute-remove');
        const typeSelect = attributeItem.querySelector('.attribute-type-select');
        const keyInput = attributeItem.querySelector('.attribute-key');
        const optionsContainer = attributeItem.querySelector('.options-list');
        const addOptionBtn = attributeItem.querySelector('.add-option-btn');

        removeBtn.addEventListener('click', () => {
            attributes = attributes.filter(attr => attr.id !== attributeId);
            attributeItem.remove();
        });

        typeSelect.addEventListener('change', (e) => {
            attribute.type = e.target.value;
        });

        keyInput.addEventListener('input', (e) => {
            attribute.key = e.target.value.trim();
        });

        addOptionBtn.addEventListener('click', () => {
            addOption(attribute, optionsContainer);
        });
    }

    function addOption(attribute, container) {
        const optionId = Date.now();

        const option = {
            id: optionId,
            value: ''
        };

        attribute.options.push(option);

        const optionItem = document.createElement('div');
        optionItem.className = 'option-item';

        optionItem.innerHTML = `
            <input type="text" class="form-control option-input" placeholder="Значение категории">
            <span class="option-remove"><i class="fas fa-times"></i></span>
        `;

        container.appendChild(optionItem);

        const input = optionItem.querySelector('.option-input');
        const removeBtn = optionItem.querySelector('.option-remove');

        input.addEventListener('input', (e) => {
            option.value = e.target.value.trim();
        });

        removeBtn.addEventListener('click', () => {
            attribute.options = attribute.options.filter(opt => opt.id !== optionId);
            optionItem.remove();
        });
    }

    // ---------------- SUBMIT ----------------
    async function submitFormData() {
        const submissionAttributes = attributes.map(attr => {
            const attribute = {
                key: attr.key,
                type: attr.type
            };

            if (attr.type === 'categorical' && attr.options.length > 0) {
                attribute.options = attr.options.map(opt => opt.value);
            }

            return attribute;
        });

        const filesPayload = {};

        Object.keys(uploadedFiles).forEach(inputName => {
            filesPayload[inputName] = {
                num_files: uploadedFiles[inputName].filesMeta.length,
                file_names: uploadedFiles[inputName].filesMeta.map(it => it.name)
            };
        });

        const taskData = {
            title: document.getElementById('title').value.trim(),
            description: document.getElementById('description').value.trim(),
            instructions: document.getElementById('instructions').value.trim(),
            annotators_count: parseInt(document.getElementById('annotatorsCount').value),
            days_to_complete: parseInt(document.getElementById('daysToComplete').value),
            deadline: new Date(document.getElementById('deadline').value).toISOString(),

            image_labels: imageLabels,
            bbox_labels: bboxLabels,
            segmentation_labels: segmentationLabels,
            attributes: submissionAttributes,

            files: filesPayload
        };

        const response = await fetch('/api/tasks/init-upload', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        });

        if (!response.ok) {
            throw new Error('Ошибка сохранения данных задания');
        }

        const result = await response.json();
        return result.taskId;
    }

    async function uploadFiles(taskId) {
        for (const inputName in uploadedFiles) {
            for (const file of uploadedFiles[inputName].allSelectedFiles) {
                await uploadSingleFile(taskId, file, inputName);
            }
        }
    }

    async function uploadSingleFile(taskId, file, inputName) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();

            formData.append('file', file);

            const xhr = new XMLHttpRequest();

            xhr.open('POST', `/api/tasks/${taskId}/upload-file?file_type=${inputName}`, true);

            xhr.setRequestHeader('Authorization', token);
            xhr.setRequestHeader('X-Session-ID', storedSessionId);

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    progressBars[inputName].style.width = percent + '%';
                }
            };

            xhr.onload = () => {
                if (xhr.status === 200) resolve();
                else reject(new Error(xhr.statusText));
            };

            xhr.onerror = () => reject(new Error('Ошибка сети'));

            xhr.send(formData);
        });
    }

    taskForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        submitBtn.disabled = true;
        uploadProgress.style.display = 'block';
        statusText.textContent = 'Подготовка...';

        try {
            const taskId = await submitFormData();

            await uploadFiles(taskId);

            statusText.textContent = 'Успешно';

            window.location.replace('/dashboard');

        } catch (error) {
            statusText.textContent = error.message;
        } finally {
            submitBtn.disabled = false;
        }
    });
});