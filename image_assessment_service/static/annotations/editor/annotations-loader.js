import { AnnotationObject } from "./annotation-objects-manager.js";

export async function loadAnnotations(
    task,
    annotationId,
    loader,
    imageName,
    annotationObjectsManager,
    manualCreateBbox,
    manualCreateSegment
) {
    try {
        loader.style.display = 'flex';

        const response = await fetch(`/api/annotations/${annotationId}/images/${imageName}`);
        if (!response.ok) throw new Error('Ошибка загрузки аннотаций');
        const annotations = await response.json();

        let id = 0

        if (task.image_labels && task.image_labels.length > 0) {
            let ann = annotations.find(ann => ann.type === 'image');
            if (ann) {
                annotationObjectsManager.add(new AnnotationObject(
                    id++,
                    'image',
                    ann.label,
                    undefined,
                    ann.attributes
                ));
            } else {
                annotationObjectsManager.add(new AnnotationObject(
                    id++,
                    'image',
                    "",
                    undefined,
                    {}
                ));
            }
        }

        
        annotations.forEach(ann => {
            if (ann.type === 'bbox') {
                manualCreateBbox(
                    ann.coords[0],
                    ann.coords[1],
                    ann.coords[2] - ann.coords[0],
                    ann.coords[3] - ann.coords[1],
                    id++,
                    ann.label,
                    ann.attributes
                );
            } else if (ann.type === 'segment') {
                manualCreateSegment(
                    ann.points,
                    id++,
                    ann.label,
                    ann.attributes
                );
            }
        });
        return {
            nextId: id
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось загрузить аннотации');
    } finally {
        loader.style.display = 'none';
    }
}