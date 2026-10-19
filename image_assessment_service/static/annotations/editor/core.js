import {AnnotationObjectsManager, AnnotationObject} from './annotation-objects-manager.js';
import {setupBboxTool} from './tools/bbox-tool.js';
import {setupPointerTool} from './tools/pointer.js';
import {setupSegmentTool} from './tools/segment-tool.js';
import {createImageSelect} from './image-select.js';
import {ObjectsList} from './objects-list/objects-list.js';
import {setLabelsElements} from './label-select.js';
import {updateKonvaObject} from './object-updater.js';
import {loadAnnotations} from './annotations-loader.js';
import {saveAnnotations} from './annotations-saver.js';

export class ImageEditor {
    constructor(containerId, annotationId) {
        this.container = document.getElementById(containerId);
        this.taskId = null;
        this.annotationId = annotationId;
        this.stage = null;
        this.layer = null;
        this.maskLayer = null;
        this.image = null;
        this.currentTool = 'pointer';
        this.currentLabel = 'person';
        this.imageIndex = 0;
        this.nextId = 0;
        this.task = null;
        this.imageName = '';
        this.annotationsManager = null;
        this.tools = {};
        this.isEditable = true;
        this.objectsList = null;
    }

    async init() {
        this.setupUI();
        await this.loadAnnotation();
        await this.loadTask();
        this.setupEventListeners();

        await this.selectImage(0);

        document.debug = () => {
            console.log(this);
        }
    }

    setupUI() {
        this.imageSelect = createImageSelect();
        this.loader = document.getElementById('loader');
        this.pointerToolBtn = document.getElementById('pointer-tool');
        this.bboxToolBtn = document.getElementById('bbox-tool');
        this.segmentToolBtn = document.getElementById('segment-tool');
        this.saveBtn = document.getElementById('save-btn');
        this.objectsListElement = document.getElementById('objects-list');
    }

    async loadAnnotation() {
        try {
            this.loader.style.display = 'flex';

            const response = await fetch(`/api/annotations/${annotationId}/`);
            if (!response.ok) throw new Error('Ошибка загрузки аннотации');

            this.isEditable = response.headers.get('X-Annotation-Editable') === 'true';

            const annotationMeta = await response.json();
            this.taskId = annotationMeta.task_id;

        } catch (error) {
            console.error('Ошибка:', error);
            alert('Не удалось загрузить задание');
        } finally {
            this.loader.style.display = 'none';
        }
    }

    async loadTask() {
        try {
            this.loader.style.display = 'flex';

            const response = await fetch(`/api/tasks/${this.taskId}`);
            if (!response.ok) throw new Error('Ошибка загрузки задания');
            this.task = await response.json();

            this.task.image_names.forEach((name, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = name;
                this.imageSelect.element.appendChild(option);
            });
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Не удалось загрузить задание');
        } finally {
            this.loader.style.display = 'none';
        }
    }

    async loadImage() {
        try {
            this.loader.style.display = 'flex';
            const response = await fetch(`/api/tasks/${this.taskId}/images/${this.imageName}`);
            if (!response.ok) throw new Error('Ошибка загрузки изображения');

            const blob = await response.blob();
            const imageUrl = URL.createObjectURL(blob);
            this.createEditor(imageUrl);
        } catch (error) {
            console.error('Ошибка:', error);
            alert('Не удалось загрузить изображение');
        } finally {
            this.loader.style.display = 'none';
        }
    }

    destroyEditor() {
        if (this.stage) this.stage.destroy();
        this.stage = null;
        this.layer = null;

        if (this.objectsList !== null) {
            this.objectsList.destroy();
        }
        this.objectsList = null;

    }

    createEditor(imageUrl) {
        this.destroyEditor();

        this.stage = new Konva.Stage({
            container: 'image-container',
            width: 800,
            height: 600,
        });

        this.annotationsManager = new AnnotationObjectsManager();
        this.objectsList = new ObjectsList(this.objectsListElement, this.isEditable, this.annotationsManager, this.task);

        const originalStyles = new Map();
        const highlightObject = (ann) => {
            const shape = ann.konvaObject;
            if (!shape) return;

            if (!originalStyles.has(ann.id)) {
                originalStyles.set(ann.id, {
                    stroke: shape.stroke(),
                    strokeWidth: shape.strokeWidth()
                });
            }

            shape.stroke('#FFD700');
            shape.strokeWidth(6);
            shape.getLayer()?.batchDraw();
        };

        const unhighlightObject = (ann) => {
            const shape = ann.konvaObject;
            if (!shape) return;

            const original = originalStyles.get(ann.id);
            if (original) {
                shape.stroke(original.stroke);
                shape.strokeWidth(original.strokeWidth);
                shape.getLayer()?.batchDraw();
            }
        };

        this.annotationsManager.on('select', (ann) => {
            this.annotationsManager.getAll().forEach(obj => {
                if (obj.id !== ann.id) unhighlightObject(obj);
            });
            highlightObject(ann);
        });

        this.annotationsManager.on('remove', (ann) => {
            originalStyles.delete(ann.id);
            unhighlightObject(ann);
        });

        const originalDestroy = this.destroyEditor.bind(this);
        this.destroyEditor = () => {
            originalStyles.clear();
            originalDestroy();
        };

        this.annotationsManager.on('add', (ann) => console.log('add', ann));
        this.annotationsManager.on('select', (ann) => console.log('select', ann));
        this.annotationsManager.on('remove', (ann) => console.log('remove', ann));
        this.annotationsManager.on('update', (ann) => console.log('update', ann));

        this.annotationsManager.on('remove', (ann) => ann.konvaObject.destroy());
        this.annotationsManager.on('update', (ann) => updateKonvaObject(ann));

        this.layer = new Konva.Layer();
        this.stage.add(this.layer);

        this.maskLayer = new Konva.Layer();
        this.stage.add(this.maskLayer);

        const img = new window.Image();
        img.src = imageUrl;
        img.onload = () => {
            this.stage.width(img.width);
            this.stage.height(img.height);

            this.image = new Konva.Image({
                image: img,
                x: 0,
                y: 0,
                width: img.width,
                height: img.height,
            });

            this.layer.add(this.image);
            this.layer.draw();
        };

        const originalAdd = this.layer.add.bind(this.layer);
        const finalStage = this.stage;
        this.layer.add = function (child) {
            const result = originalAdd(child);
            ignoreScaleIfNeeded(child, finalStage.scaleX());
            return result;
        };

        this.stage.container().addEventListener('wheel', (e) => {
            e.preventDefault();
            const scaleBy = 1.1;
            const oldScale = this.stage.scaleX();
            const pointer = this.stage.getPointerPosition();

            if (!pointer) return;

            const mousePointTo = {
                x: (pointer.x - this.stage.x()) / oldScale,
                y: (pointer.y - this.stage.y()) / oldScale
            };

            const newScale = e.deltaY > 0 ? oldScale / scaleBy : oldScale * scaleBy;

            if (newScale < 0.1 || newScale > 10) return;

            this.stage.scale({x: newScale, y: newScale});

            const newPos = {
                x: pointer.x - mousePointTo.x * newScale,
                y: pointer.y - mousePointTo.y * newScale
            };

            this.stage.position(newPos);
            this.layer.find(node => node.getAttr('ignoreScale') !== undefined)
                .forEach(obj => ignoreScaleIfNeeded(obj, newScale))

            this.stage.batchDraw();
        });

        function ignoreScaleIfNeeded(obj, curScale) {
            const ignoreScale = obj.getAttr('ignoreScale');
            if (ignoreScale === undefined) return;
            if (ignoreScale.strokeWidth !== undefined) {
                obj.strokeWidth(ignoreScale.strokeWidth / curScale);
            }
            if (ignoreScale.scale !== undefined) {
                const scale = ignoreScale.scale;
                obj.scaleX(scale / curScale);
                obj.scaleY(scale / curScale);
            }
        }
    }

    setupTools() {
        if (!this.isEditable) {
            this.saveBtn.style.display = 'none';
        }
        if (this.task.bbox_labels.length === 0) {
            this.bboxToolBtn.disabled = true;
        }
        if (this.task.segmentation_labels.length === 0) {
            this.segmentToolBtn.disabled = true;
        }
        this.tools.pointer = setupPointerTool(
            this.stage,
            this.layer,
            this.annotationsManager
        );
        this.tools.bbox = setupBboxTool(
            this.stage,
            this.layer,
            this.annotationsManager,
            () => this.nextId++,
            () => this.currentLabel
        );
        this.tools.segment = setupSegmentTool(
            this.stage,
            this.layer,
            this.annotationsManager,
            () => this.nextId++,
            () => this.currentLabel
        );
        this.activateTool(this.currentTool)
    }

    setupEventListeners() {
        this.pointerToolBtn.addEventListener('click', () => this.activateTool('pointer'));
        this.bboxToolBtn.addEventListener('click', () => this.activateTool('bbox'));
        this.segmentToolBtn.addEventListener('click', () => this.activateTool('segment'));
        this.saveBtn.addEventListener('click', () => saveAnnotations(this.task, this.annotationId, this.loader, this.imageName, this.annotationsManager));
        this.imageSelect.element.addEventListener('change', (e) => this.selectImage(parseInt(e.target.value)));
        this.imageSelect.prevBtn.addEventListener('click', () => this.prevImage());
        this.imageSelect.nextBtn.addEventListener('click', () => this.nextImage());
    }

    activateTool(toolName) {
        Object.values(this.tools).forEach(tool => tool.deactivate());
        this.tools[toolName].activate();
        this.currentTool = toolName;

        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.classList.toggle('active', btn.id === `${toolName}-tool`);
        });

        setLabelsElements(toolName, this.task, (label) => this.currentLabel = label);
    }

    async selectImage(index) {
        this.imageSelect.element.value = index;
        this.imageIndex = index;
        this.imageName = this.task.image_names[this.imageIndex];

        await this.loadImage();
        this.setupTools();

        const {nextId} = await loadAnnotations(
            this.task, this.annotationId, this.loader, this.imageName,
            this.annotationsManager,
            this.tools.bbox.manualCreateBbox,
            this.tools.segment.manualCreateSegment
        )
        this.nextId = nextId;
    }

    prevImage() {
        if (this.imageIndex > 0) {
            this.selectImage(this.imageIndex - 1);
        }
    }

    nextImage() {
        if (this.imageIndex < this.task.image_names.length - 1) {
            this.selectImage(this.imageIndex + 1);
        }
    }
}