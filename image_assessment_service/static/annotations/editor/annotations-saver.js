export async function saveAnnotations(
    task,
    annotationId,
    loader,
    imageName,
    annotationObjectsManager,
    availableAttributes
) {
    try {
        loader.style.display = 'flex';

        const attributesMap = (task.attributes || []).reduce((acc, attr) => {
            acc[attr.key] = attr;
            return acc;
        }, {});

        const objects = annotationObjectsManager.getAll();

        console.log(objects);

        for (const obj of objects) {
            const error = validateAnnotationObject(obj, attributesMap);
            if (error !== null) {
                throw new Error(error);
            }
        }
        
        const data = objects.map(obj => {
            let ret = {};

            if (obj.type === 'image') {
                ret = {
                    type: 'image'
                };
            } else if (obj.type === 'bbox') {
                const konvaObject = obj.konvaObject;
                ret = {
                    type: 'bbox',
                    coords: [
                        konvaObject.getX(),
                        konvaObject.getY(),
                        konvaObject.getX() + konvaObject.getWidth(),
                        konvaObject.getY() + konvaObject.getHeight()
                    ]
                };
            } else if (obj.type === 'segment') {
                ret = {
                    type: 'segment',
                    points: obj.konvaObject.points()
                };
            }

            // common: label and attributes
            ret.label = obj.label;
            if (Object.keys(obj.attributes).length > 0) {
                ret.attributes = obj.attributes;
            }

            return ret;
        });

        const response = await fetch(`/api/annotations/${annotationId}/images/${imageName}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        
        if (!response.ok) {
            console.error("Error response:", response)
            throw new Error('Ошибка сохранения')
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert(`Не удалось сохранить разметку: ${error.message}`);
    } finally {
        loader.style.display = 'none';
    }
}

function validateAnnotationObject(obj, attributesMap) {
    const attributesError = validateAttributes(obj.attributes, attributesMap);
    if (attributesError !== null) {
        return attributesError;
    }
    const labelError = validateLabel(obj.label);
    if (labelError !== null) {
        return labelError;
    }
    return null;
}

function validateLabel(label) {
    if (label === "") {
        return 'Не указана метка класса';
    }
    return null;
}

function validateAttributes(attributes, attributesMap) {
    for (const key in attributes) {
        if (!(key in attributesMap)) {
            return `Неизвестный атрибут ${key}`
        }
        const attr = attributes[key];
        if (attributesMap[key].type === 'number' && isNaN(parseInt(attr))) {
            console.log("INSIDE")
            return `Некорректное значение атрибута ${key}: "${attr}", ожидается число`;
        }
    }
    return null;
}