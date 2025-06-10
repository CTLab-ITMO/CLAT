class KonvaObjectManager {
    constructor() {
      this.objects = {};
    }
  
    add(obj) {
      if (obj.id() === undefined) {
        throw new Error('Объект должен иметь id');
      }
      this.objects[obj.id()] = obj;
    }
  
    get(id) {
      return this.objects[id];
    }
  
    remove(id) {
      const obj = this.objects[id];
      if (obj) {
        obj.destroy();
        delete this.objects[id];
      }
    }
  }

function addImageSelect() {
    const topPanelContent = document.getElementById('top-panel-content');

    topPanelContent.innerHTML = `
    <div class="image-navigator">
        <button class="nav-btn prev-btn" id="prev-image" title="Предыдущее изображение">
            <span>◄</span>
        </button>
        
        <div class="image-info">
            <select id="image-select" class="minimal-select">
                <!-- Опции будут заполнены скриптом -->
            </select>
             <!-- <div class="image-counter" id="image-counter">0 из 0</div> -->
        </div>
        
        <button class="nav-btn next-btn" id="next-image" title="Следующее изображение">
            <span>►</span>
        </button>
    </div>`
}

document.addEventListener('DOMContentLoaded', async function() {
    addImageSelect();

    // Элементы интерфейса
    const loader = document.getElementById('loader');
    const pointerToolBtn = document.getElementById('pointer-tool');
    const bboxToolBtn = document.getElementById('bbox-tool');
    const brushToolBtn = document.getElementById('brush-tool');
    const saveBtn = document.getElementById('save-btn');
    const objectsList = document.getElementById('objects-list');

    const imageSelect = document.getElementById('image-select');
    const prevBtn = document.getElementById('prev-image');
    const nextBtn = document.getElementById('next-image');
    const imageCounter = document.getElementById('image-counter');

    async function disableControls() {
        for (btn of [pointerToolBtn, bboxToolBtn, brushToolBtn]) {
            btn.disabled = true;
            btn.classList.remove('active');
        }
        saveBtn.disabled = true;
    }


    const response = await fetch(`/api/annotations/${annotationId}/`);
    if (!response.ok) throw new Error('Ошибка загрузки аннотации');

    const isEditable = response.headers.get('X-Annotation-Editable') === 'true';
    if (!isEditable) {
        disableControls();
    }

    const annotationMeta = await response.json();
    const taskId = annotationMeta.task_id;


    var currentTool = 'bbox';
    var currentLabel = 'person';
    var annotations = [];
    var stage, layer, maskLayer, image;
    var imageIndex = 0;
    var nextId = 0;
    var task;
    var imageName;
    var annotationsManager;

    var getPosOnCanvas;
  
    async function loadTask() {
        try {
            loader.style.display = 'flex';
            
            // Получаем URL изображения с сервера
            const response = await fetch(`/api/tasks/${taskId}`);
            if (!response.ok) throw new Error('Ошибка загрузки задания');
            task = await response.json();

            task.image_names.forEach((name, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = name;
                imageSelect.appendChild(option);
            });
            
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Не удалось загрузить изображение');
        } finally {
            loader.style.display = 'none';
        }
    }

    async function loadAnnotations() {
        try {
            loader.style.display = 'flex';
            objectsList.innerHTML = '';
            annotationsManager = new KonvaObjectManager();

            const response = await fetch(`/api/annotations/${annotationId}/images/${imageName}`);
            if (!response.ok) throw new Error('Ошибка загрузки аннотаций');
            annotations = await response.json();

            for (const ann of annotations) {
                if (ann.type == 'bbox') {
                    const coords = ann.coords;
                    const rect = drawBbox(coords[0], coords[1], coords[2] - coords[0], coords[3] - coords[1], ann.id);
                    addObjectToList(ann);
                    setupBboxInteractions(rect, ann);
                }
            }
            nextId = annotations.length;
            
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Не удалось загрузить аннотации');
        } finally {
            loader.style.display = 'none';
        }
    }

  // Загружаем изображение
    async function loadImage(index) {
        imageName = task.image_names[index];

        try {
            loader.style.display = 'flex';
            
            const response = await fetch(`/api/tasks/${taskId}/images/${imageName}`);
            if (!response.ok) throw new Error('Ошибка загрузки изображения');

            const blob = await response.blob();
            const imageUrl = URL.createObjectURL(blob);
            
            // Создаем Konva stage
            createEditor(imageUrl);
            
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Не удалось загрузить изображение');
        } finally {
            loader.style.display = 'none';
        }
    }

    async function selectImage(index) {
        imageSelect.value = index;
        imageIndex = index;
        imageName = task.image_names[imageIndex];

        await loadImage(imageIndex);
        loadAnnotations();
    }

  // Создаем редактор с Konva
    function createEditor(imageUrl) {
        // Удаляем предыдущий stage, если есть
        if (stage) stage.destroy();
        
        // Создаем новый stage
        stage = new Konva.Stage({
            container: 'image-container',
            width: 800,
            height: 600,
        });
        
        layer = new Konva.Layer();
        stage.add(layer);

        maskLayer = new Konva.Layer();
        stage.add(maskLayer);
                
        // Загружаем изображение
        const img = new window.Image();
        img.src = imageUrl;
        img.onload = function() {
            // Подгоняем размер stage под изображение
            stage.width(img.width);
            stage.height(img.height);
            
            // Создаем Konva Image
            image = new Konva.Image({
                image: img,
                x: 0,
                y: 0,
                width: img.width,
                height: img.height,
            });
            
            layer.add(image);
            layer.draw();
            
            // Добавляем обработчики для рисования bbox
            setupPointerTool();
            setupBboxTool();
            setupPixelSegmentationTool();
        };

        getPosOnCanvas = () => {
            const pointer = stage.getPointerPosition();
            if (!pointer) return;
            const scale = stage.scaleX();
            return {
                x: (pointer.x - stage.x()) / scale,
                y: (pointer.y - stage.y()) / scale
            }
        }

        stage.container().addEventListener('wheel', (e) => {
            e.preventDefault(); // Отменяем стандартное поведение прокрутки
            
            const scaleBy = 1.1; // Коэффициент масштабирования
            const oldScale = stage.scaleX();
            const pointer = stage.getPointerPosition();
            
            if (!pointer) return;
            
            const mousePointTo = {
                x: (pointer.x - stage.x()) / oldScale,
                y: (pointer.y - stage.y()) / oldScale
            };
            
            // Определяем направление прокрутки
            const newScale = e.deltaY > 0 ? oldScale / scaleBy : oldScale * scaleBy;
            
            // Ограничиваем масштабирование
            if (newScale < 0.1) return; // Минимальный масштаб
            if (newScale > 10) return;  // Максимальный масштаб
            
            stage.scale({ x: newScale, y: newScale });
            
            const newPos = {
                x: pointer.x - mousePointTo.x * newScale,
                y: pointer.y - mousePointTo.y * newScale
            };
            
            stage.position(newPos);
            stage.batchDraw();
        });
    }

    function setupPointerTool() {
        stage.on('mousedown touchstart', (e) => {
            if (currentTool !== 'pointer') return; 
            const clickedOnAnnotation = e.target.getAttr('isAnnotation');
            
            if (clickedOnAnnotation) {
                e.target.draggable(true);
            } else {
                stage.draggable(true);
            }
        });
        
        stage.on('mouseup touchend', () => {
            // stage.draggable(false);
        });
    }

    function setupPixelSegmentationTool() {

        let brushSize = 10; // Размер кисти в пикселях
        let brushColor = '#FF0000';
        stage.container().style.cursor = `url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="${brushSize}" height="${brushSize}" viewBox="0 0 ${brushSize} ${brushSize}"><circle cx="${brushSize/2}" cy="${brushSize/2}" r="${brushSize/2}" fill="${brushColor}"/></svg>') ${brushSize/2} ${brushSize/2}, auto`;

        let isDrawing = false;
        let currentRect = null;
        let startX, startY;
        let lastLine = null;

        stage.on('mousedown touchstart', (e) => {
            if (currentTool !== 'brush') return;
            
            const pos = getPosOnCanvas();
            if (!pos) return;
            
            isDrawing = true;
            
            // Создаем новый путь для маски
            brushPath = new Konva.Path({
                stroke: brushColor,
                strokeWidth: brushSize,
                globalCompositeOperation: 'source-over',
                lineCap: 'round',
                lineJoin: 'round',
                opacity: 0.7,
                name: 'brush_path'
            });
            
            brushPath.data(`M ${pos.x} ${pos.y}`);
            maskLayer.add(brushPath);
        });

        stage.on('mousemove touchmove', () => {
            if (!isDrawing || currentTool !== 'brush') return;
            
            const pos = getPosOnCanvas();
            if (!pos) return;
            
            if (!lastLine) {
                lastLine = new Konva.Line({
                    points: [pos.x, pos.y],
                    stroke: brushColor,
                    strokeWidth: brushSize,
                    lineCap: 'round',
                    lineJoin: 'round',
                    globalCompositeOperation: 'source-over',
                    opacity: 0.7
                });
                maskLayer.add(lastLine);
            }
            
            const newPoints = lastLine.points().concat([pos.x, pos.y]);
            lastLine.points(newPoints);
            maskLayer.batchDraw();
        });
        
        stage.on('mouseup touchend', () => {
            if (currentTool !== 'brush') return;
            
            if (lastLine && lastLine.points().length > 2) {
                // Конвертируем линии в закрашенный контур
                const points = lastLine.points();
                let pathData = `M ${points[0]} ${points[1]}`;
                
                for (let i = 2; i < points.length; i += 2) {
                    pathData += ` L ${points[i]} ${points[i+1]}`;
                }
                
                const maskId = `mask-${Date.now()}`;
                currentMask = new Konva.Path({
                    data: pathData,
                    fill: brushColor,
                    opacity: 0.5,
                    name: 'segmentation_mask',
                    maskId: maskId
                });
                
                maskLayer.add(currentMask);
                lastLine.destroy();
                
                // Сохраняем аннотацию
                annotations.push({
                    id: maskId,
                    label: currentLabel,
                    type: 'mask',
                    pathData: pathData,
                    konvaObject: currentMask
                });
                
                addObjectToList({
                    id: maskId,
                    label: currentLabel,
                    type: 'mask'
                });
            } else if (lastLine) {
                lastLine.destroy();
            }
            
            lastLine = null;
            currentMask = null;
            isDrawing = false;
            maskLayer.batchDraw();
        });
    }

    // Настройка инструмента Bounding Box
    function setupBboxTool() {
        let isDrawing = false;
        let currentRect = null;
        let startX, startY;
        
        stage.on('mousedown touchstart', (e) => {
            if (currentTool !== 'bbox') return;
            
            const pos = getPosOnCanvas();
            if (!pos) return;
            
            startX = pos.x;
            startY = pos.y;

            isDrawing = true;
            
            currentRect = drawBbox(pos.x, pos.y, 0, 0, nextId++);
        });
        
        stage.on('mousemove touchmove', () => {
            if (!isDrawing || !currentRect || currentTool !== 'bbox') return;
            
            const pos = getPosOnCanvas();
            if (!pos) return;
            
            currentRect.width(pos.x - startX);
            currentRect.height(pos.y - startY);
            layer.batchDraw();
        });
        
        stage.on('mouseup touchend', () => {
            if (!isDrawing || !currentRect || currentTool !== 'bbox') return;
            
            // Проверяем, что рамка имеет достаточный размер
            if (Math.abs(currentRect.width()) > 10 && Math.abs(currentRect.height()) > 10) {
                // Добавляем аннотацию
                const annotation = {
                    label: currentLabel,
                    type: 'bbox',
                    coords: [
                        currentRect.x(),
                        currentRect.y(),
                        currentRect.x() + currentRect.width(),
                        currentRect.y() + currentRect.height()
                    ],
                    id: currentRect.id()
                };
                
                annotations.push(annotation);
                addObjectToList(annotation);
                
                // Настраиваем взаимодействие с рамкой
                setupBboxInteractions(currentRect, annotation);
            } else {
                // Удаляем слишком маленькую рамку
                currentRect.destroy();
            }
            
            isDrawing = false;
            currentRect = null;
            layer.batchDraw();
        });
    }

    // Настройка взаимодействий с существующей рамкой
    function setupBboxInteractions(rect, annotation) {
        
        rect.on('dragend transformend', () => {
            if (currentTool !== 'pointer') return;

            // Обновляем координаты в аннотации
            annotation.coords = [
                rect.x(),
                rect.y(),
                rect.x() + rect.width(),
                rect.y() + rect.height()
            ];
            
            // Обновляем список объектов
            updateObjectInList(annotation);
        });
        
        rect.on('click tap', (e) => {
            e.cancelBubble = true;
            selectObject(annotation.id);
        });
    }

    // Добавляем объект в список
    function addObjectToList(annotation) {
        const item = document.createElement('div');
        item.className = 'object-item';
        item.dataset.id = annotation.id
        item.innerHTML = `
            <span class="object-label">${annotation.label}</span>
            ${isEditable ? `<button class="object-delete">✕</button>` : ""}
        `;
        
        item.addEventListener('click', () => selectObject(annotation.id));
        
        if (isEditable) {
            const deleteBtn = item.querySelector('.object-delete');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                deleteObject(annotation.id);
            });
        }
        
        objectsList.appendChild(item);
    }

    // Обновляем объект в списке
    function updateObjectInList(annotation) {
        const item = objectsList.querySelector(`[data-id="${annotation.id}"]`);
        if (item) {
            item.querySelector('.object-label').textContent = annotation.label;
        }
    }

    // Выбираем объект
    function selectObject(id) {
        // Убираем выделение у всех
        document.querySelectorAll('.object-item').forEach(el => {
            el.classList.remove('active');
        });
        
        // Находим аннотацию
        const annotation = annotations.find(a => a.id === id);
        if (!annotation) return;
        
        // Выделяем в списке
        const item = objectsList.querySelector(`[data-id="${id}"]`);
        if (item) item.classList.add('active');
        
        // Можно добавить логику выделения на canvas
    }

    // Удаляем объект
    function deleteObject(id) {
        // Удаляем из списка аннотаций
        const index = annotations.findIndex(a => a.id === id);
        if (index === -1) return;
        
        // Удаляем с canvas
        annotationsManager.remove(id);
        layer.batchDraw();
        
        // Удаляем из массива
        annotations.splice(index, 1);
        
        // Удаляем из DOM
        const item = objectsList.querySelector(`[data-id="${id}"]`);
        if (item) item.remove();
    }

    // Сохраняем аннотации
    async function saveAnnotations() {
        try {
            loader.style.display = 'flex';
            
            // Подготавливаем данные для отправки
            const data = annotations.map(a => ({
                id: a.id,
                label: a.label,
                type: a.type,
                coords: a.coords
            }));

            // Отправляем на сервер
            const response = await fetch(`/api/annotations/${annotationId}/images/${imageName}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });
            
            if (!response.ok) throw new Error('Ошибка сохранения');
            
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Не удалось сохранить аннотации');
        } finally {
            loader.style.display = 'none';
        }
    }

    // Вспомогательные функции
    function getRandomColor() {
        return `hsl(${Math.floor(Math.random() * 360)}, 80%, 50%)`;
    }

    function enableDragging() {
        stage.draggable(true);
        layer.getChildren()
            .filter(it => it.getAttr('isAnnotation'))
            .forEach(it => it.draggable(true));
    }

    function disableDragging() {
        stage.draggable(false);
        layer.getChildren()
            .filter(it => it.getAttr('isAnnotation'))
            .forEach(it => it.draggable(false));
    }

    function activateToolButton(btn) {
        document.querySelectorAll('.tool-btn')
            .forEach(it => {
                if (it === btn) {
                    it.classList.add('active');
                } else {
                    it.classList.remove('active');
                }
            })
    }

    pointerToolBtn.addEventListener('click', () => {
        activateToolButton(pointerToolBtn);
        currentTool = 'pointer';
        enableDragging();
    })

    bboxToolBtn.addEventListener('click', () => {
        activateToolButton(bboxToolBtn);
        currentTool = 'bbox';
        disableDragging();
    });

    brushToolBtn.addEventListener('click', () => {
        activateToolButton(brushToolBtn);
        currentTool = 'brush';
        disableDragging();
    })

    activateToolButton(pointerToolBtn);
    currentTool = 'pointer';

    saveBtn.addEventListener('click', saveAnnotations);

    imageSelect.addEventListener('change', function () {
        idx = parseInt(this.value);
        selectImage(idx);
    });

    prevBtn.addEventListener('click', () => {
        if (imageIndex > 0) {
            selectImage(imageIndex - 1);
        }
    });
    
    nextBtn.addEventListener('click', () => {
        if (imageIndex < task.image_names.length - 1) {
            selectImage(imageIndex + 1);
        }
    });

    async function setLabelsElements() {
        const labelsList = document.getElementById('labels-list');

        labelsList.innerHTML = task.bbox_labels.map(label => `
            <button class="tool-label-btn label-btn" data-label="${label}">${label}</button>
        `).join('');

        document.querySelectorAll('.label-btn').forEach(btn => {
            if (!isEditable) {
                btn.disabled = true;
            }
            btn.addEventListener('click', () => {
                currentLabel = btn.dataset.label;
                document.querySelectorAll('.label-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
    
        const firstLabelBtn = document.querySelectorAll('.label-btn')[0];
        firstLabelBtn.classList.add('active');
        currentLabel = firstLabelBtn.dataset.label;
        
    }

    // Загружаем изображение при старте
    await loadTask();
    await loadImage(0);
    selectImage(0);
    setLabelsElements(); 
    
    function drawBbox(x, y, width, heigth, id) {
        const rect = new Konva.Rect({
            x: x,
            y: y,
            id: id,
            width: width,
            height: heigth,
            stroke: getRandomColor(),
            strokeWidth: 2,
            fill: 'rgba(0, 0, 255, 0.1)',
            name: 'bbox',
            isAnnotation: true
        });
        annotationsManager.add(rect);
        layer.add(rect);
        return rect;
    }
});

