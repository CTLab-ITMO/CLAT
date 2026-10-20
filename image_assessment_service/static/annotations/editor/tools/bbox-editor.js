export function setupBboxEditor(annotationObject, layer, annotationObjectsManager) {
    const rect = annotationObject.konvaObject;
    const corners = [];
    const cornerRadius = 5;
    
    function createCorner(x, y, name) {
        const corner = new Konva.Circle({
            x: x,
            y: y,
            radius: cornerRadius,
            fill: 'white',
            stroke: 'black',
            strokeWidth: 1,
            draggable: true,
            name: name,
            isSelectIndifferent: true,
            ignoreScale: { scale: 1 }
        });
        
        corner.on('dragmove', () => updateRectFromCorners(name));
        corner.on('dragend', () => annotationObjectsManager.update(annotationObject.id));
        
        layer.add(corner);
        corners.push(corner);
        return corner;
    }
    
    function updateRectFromCorners(movingCorner) {
        const topLeft = corners.find(c => c.name() === 'topLeft');
        const topRight = corners.find(c => c.name() === 'topRight');
        const bottomRight = corners.find(c => c.name() === 'bottomRight');
        const bottomLeft = corners.find(c => c.name() === 'bottomLeft');
        
        if (movingCorner === 'topLeft' || movingCorner === 'bottomRight') {
            rect.x(topLeft.x())
            rect.y(topLeft.y());
            rect.width(bottomRight.x() - topLeft.x());
            rect.height(bottomRight.y() - topLeft.y());
        } else {
            rect.x(bottomLeft.x())
            rect.y(topRight.y());
            rect.width(topRight.x() - bottomLeft.x());
            rect.height(bottomLeft.y() - topRight.y()); 
        }
        updateCornersFromRect();
        layer.batchDraw();
    }
    
    function updateCornersFromRect() {
        const x = rect.x();
        const y = rect.y();
        const width = rect.width();
        const height = rect.height();
        
        corners.forEach(corner => {
            switch(corner.name()) {
                case 'topLeft':
                    corner.x(x);
                    corner.y(y);
                    break;
                case 'topRight':
                    corner.x(x + width);
                    corner.y(y);
                    break;
                case 'bottomRight':
                    corner.x(x + width);
                    corner.y(y + height);
                    break;
                case 'bottomLeft':
                    corner.x(x);
                    corner.y(y + height);
                    break;
            }
        });
    }
    
    rect.on('dragmove transform', updateCornersFromRect);
    rect.on('dragend transformend', () => annotationObjectsManager.update(annotationObject.id));

    createCorner(rect.x(), rect.y(), 'topLeft');
    createCorner(rect.x() + rect.width(), rect.y(), 'topRight');
    createCorner(rect.x() + rect.width(), rect.y() + rect.height(), 'bottomRight');
    createCorner(rect.x(), rect.y() + rect.height(), 'bottomLeft');

    const handleRectDestroy = (obj) => {
        if (obj.id != annotationObject.id) {
            return;
        }
        corners.forEach(corner => corner.destroy());
    };
    const unsub = annotationObjectsManager.on('remove', handleRectDestroy);

    rect.draggable(true);
    
    return {
        destroy() {
            corners.forEach(corner => corner.destroy());
            rect.off('dragmove transform');
            rect.off('dragend transformend');
            unsub();
            rect.draggable(false);
        }
    };
}
