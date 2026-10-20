import { getColorForString } from './utils.js';

export function updateKonvaObject(annotationObject) {
    const konvaObject = annotationObject.konvaObject;
    if (!konvaObject) return; // image (classification) annotationObject
    konvaObject.stroke(getColorForString(annotationObject.label));
}
