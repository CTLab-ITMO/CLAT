import { createObjectsListItem } from './item.js';

export class ObjectsList {
    constructor(listElement, isEditable, annotationObjectsManager, task) {
        this.listElement = listElement;
        this.isEditable = isEditable;
        this.annotationObjectsManager = annotationObjectsManager;
        this.task = task;

        const attributesArray = this.task.attributes || [];
        this.attributesMap = attributesArray.reduce((acc, attr) => {
            acc[attr.key] = attr;
            return acc;
        }, {});

        this.unsubscribes = [
            this.annotationObjectsManager.on('add', this.handleAnnotationAdd.bind(this)),
            this.annotationObjectsManager.on('remove', this.handleAnnotationRemove.bind(this)),
            this.annotationObjectsManager.on('update', this.handleAnnotationUpdate.bind(this)),
            this.annotationObjectsManager.on('select', this.handleAnnotationSelect.bind(this)),
        ]
    }

    createListItem(annotationObject) {
        let availableLabels = [];
        if (annotationObject.type === 'image') {
            availableLabels = ["", ...this.task.image_labels];
        } else if (annotationObject.type === 'bbox') {
            availableLabels = this.task.bbox_labels;
        } else if (annotationObject.type === 'segment') {
            availableLabels = this.task.segmentation_labels;
        } else {
            throw new Error('Unknown annotation object type');
        }

        // attributesMap = {
        //     age: { type: 'number' },
        //     isActive: { type: 'flag' },
        //     gender: { type: 'categorical', options: ['Male', 'Female', 'Other'] },
        //     notes: { type: 'text' },
        // };
    
        return createObjectsListItem(annotationObject, this.isEditable, this.annotationObjectsManager, availableLabels, this.attributesMap);
    }

    updateItem(objectId) {
        const annotationObject = this.annotationObjectsManager.get(objectId);
        if (!annotationObject) return;

        const item = this.listElement.querySelector(`[data-id="${objectId}"]`);
        if (!item) return;

        const newItem = this.createListItem(annotationObject);
        this.setupItemEvents(newItem, annotationObject);
        item.replaceWith(newItem);
    }

    setupItemEvents(item, annotationObject) {
        item.addEventListener('click', () => this.annotationObjectsManager.select(annotationObject.id));
    }

    handleAnnotationAdd(annotationObject) {
        const item = this.createListItem(annotationObject);
        this.setupItemEvents(item, annotationObject);
        this.listElement.appendChild(item);
    }

    handleAnnotationUpdate(annotationObject) {
        this.updateItem(annotationObject.id);
    }

    handleAnnotationRemove(annotationObject) {
        const item = this.listElement.querySelector(`[data-id="${annotationObject.id}"]`);
        if (item) item.remove();
    }

    handleAnnotationSelect(annotationObject) {
        const id = annotationObject.id;
        document.querySelectorAll('.annotation-item').forEach(el => {
            el.classList.toggle('active', el.dataset.id === String(id));
        });
        this.listElement.querySelectorAll('.object-item').forEach(el => {
            el.classList.toggle('active', el.dataset.id === String(id));
        });
    }

    destroy() {
        this.listElement.innerHTML = '';
        for (const unsub of this.unsubscribes) {
            unsub();
        }
    }
}
