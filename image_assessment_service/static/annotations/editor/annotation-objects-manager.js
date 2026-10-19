export class AnnotationObjectsManager {
    constructor() {
        this.objects = {};
        this.events = ['add', 'remove', 'select', 'update']
        this.eventListeners = {};
        for (const event of this.events) {
            this.eventListeners[event] = [];
        }
    }

    getAll() {
        return Object.values(this.objects);
    }

    add(obj) {
        if (!(obj instanceof AnnotationObject)) {
            throw new Error('Некорректный объект');
        }
        this.objects[obj.id] = obj;
        this.emit('add', obj)
    }

    get(id) {
        return this.objects[id];
    }

    select(id) {
        const obj = this.objects[id];
        if (obj) {
            this.emit('select', obj);
        }
    }

    remove(id) {
        const obj = this.objects[id];
        if (obj) {
            delete this.objects[id];
            this.emit('remove', obj);
        }
    }

    update(id) {
        const obj = this.objects[id];
        if (obj) {
            this.emit('update', obj);
        }
    }

    on(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].push(callback);
            return () => this.off(event, callback);
        }
        throw new Error(`Unknown event: ${event}`);
    }

    off(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event] = this.eventListeners[event].filter(
                cb => cb !== callback
            );
        }
    }

    emit(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                callback(data);
            });
        }
    }
}

export class AnnotationObject {
    constructor(id, type, label, konvaObject, attributes) {
        this.id = id;
        this.type = type;
        this.label = label;
        this.konvaObject = konvaObject;
        this.attributes = attributes || {};
    }
}
