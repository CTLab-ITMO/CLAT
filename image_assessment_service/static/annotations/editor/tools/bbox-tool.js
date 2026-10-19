import { AnnotationObject } from '../annotation-objects-manager.js';
import { getColorForString } from '../utils.js';

export function setupBboxTool(stage, layer, annotationObjectsManager, getNextId, getCurrentLabel) {
    let isDrawing = false;
    let currentRect = null;
    let startX, startY;

    function drawBbox(x, y, width, height, id, label) {
        const rect = new Konva.Rect({
            x: x,
            y: y,
            id: id,
            width: width,
            height: height,
            stroke: getColorForString(label),
            strokeWidth: 3,
            fill: 'rgba(0, 0, 255, 0.1)',
            name: 'bbox',
            isAnnotation: true,
            draggable: false,
            ignoreScale: { strokeWidth: 3 }
        });

        layer.add(rect);
        return rect;
    }

    function handleMouseDown(e) {
        const pos = stage.getPointerPosition();
        if (!pos) return;
        
        const scale = stage.scaleX();
        startX = (pos.x - stage.x()) / scale;
        startY = (pos.y - stage.y()) / scale;

        isDrawing = true;
        currentRect = drawBbox(startX, startY, 0, 0, getNextId(), getCurrentLabel());
    }

    function handleMouseMove() {
        if (!isDrawing || !currentRect) return;
        
        const pos = stage.getPointerPosition();
        if (!pos) return;
        
        const scale = stage.scaleX();
        const x = (pos.x - stage.x()) / scale;
        const y = (pos.y - stage.y()) / scale;
        
        currentRect.width(x - startX);
        currentRect.height(y - startY);
        layer.batchDraw();
    }

    function handleMouseUp() {
        if (!isDrawing || !currentRect) return;
        
        if (Math.abs(currentRect.width()) > 10 && Math.abs(currentRect.height()) > 10) {
            const annotationObject = new AnnotationObject(
                currentRect.id(),
                'bbox',
                getCurrentLabel(),
                currentRect
            );

            annotationObjectsManager.add(annotationObject);
        } else {
            currentRect.destroy();
        }
        
        isDrawing = false;
        currentRect = null;
    }

    function manualCreateBbox(x, y, width, height, id, label, attributes) {
        const rect = drawBbox(x, y, width, height, id, label);
        const annotationObject = new AnnotationObject(
            id,
            'bbox',
            label,
            rect,
            attributes
        );
        annotationObjectsManager.add(annotationObject);
        return annotationObject;
    }

    return {
        activate() {
            stage.on('mousedown touchstart', handleMouseDown);
            stage.on('mousemove touchmove', handleMouseMove);
            stage.on('mouseup touchend', handleMouseUp);
        },
        
        deactivate() {
            stage.off('mousedown touchstart', handleMouseDown);
            stage.off('mousemove touchmove', handleMouseMove);
            stage.off('mouseup touchend', handleMouseUp);
            
            if (isDrawing && currentRect) {
                currentRect.destroy();
                isDrawing = false;
                currentRect = null;
            }
        },

        manualCreateBbox
    };
}
