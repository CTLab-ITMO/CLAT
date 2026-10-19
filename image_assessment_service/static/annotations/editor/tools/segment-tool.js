import { AnnotationObject } from '../annotation-objects-manager.js';
import { getColorForString } from '../utils.js';

export function setupSegmentTool(stage, layer, annotationObjectsManager, getNextId, getCurrentLabel) {
    let isDrawing = false;
    let currentPolygon = null;
    let points = [];
    let guideLine = null;

    function drawPolygon(points, id, label) {
        const polygon = new Konva.Line({
            points: points,
            id: id,
            stroke: getColorForString(label),
            strokeWidth: 3,
            fill: 'rgba(0, 0, 255, 0.2)',
            closed: true,
            name: 'segment',
            isAnnotation: true,
            draggable: false,
            ignoreScale: { strokeWidth: 3 }
        });

        layer.add(polygon);
        return polygon;
    }

    function handleMouseDown(e) {
        const pos = stage.getPointerPosition();
        if (!pos) return;

        const scale = stage.scaleX();
        const x = (pos.x - stage.x()) / scale;
        const y = (pos.y - stage.y()) / scale;

        if (!isDrawing) {
            isDrawing = true;
            points = [x, y];
            currentPolygon = drawPolygon(points, getNextId(), getCurrentLabel());
            
            guideLine = new Konva.Line({
                points: [x, y, x, y],
                stroke: 'gray',
                strokeWidth: 2,
                dash: [5, 5],
                name: 'guideLine',
                ignoreScale: { strokeWidth: 2 }
            });
            layer.add(guideLine);
        } else {
            points.push(x, y);
            currentPolygon.points(points);
            
            if (points.length >= 6) {
                guideLine.points([x, y, points[0], points[1]]);
            } else {
                guideLine.points([x, y, x, y]);
            }
        }

        layer.batchDraw();
    }

    function handleMouseMove() {
        if (!isDrawing || !currentPolygon) return;
        
        const pos = stage.getPointerPosition();
        if (!pos) return;
        
        const scale = stage.scaleX();
        const x = (pos.x - stage.x()) / scale;
        const y = (pos.y - stage.y()) / scale;

        if (points.length >= 4) {
            guideLine.points([points[points.length-2], points[points.length-1], x, y]);
        } else {
            guideLine.points([points[0], points[1], x, y]);
        }
        layer.batchDraw();
    }

    function handleMouseUp() {}

    function completePolygon() {
        if (!isDrawing || points.length < 6) return;

        if (guideLine) {
            guideLine.destroy();
            guideLine = null;
        }

        const annotationObject = new AnnotationObject(
            currentPolygon.id(),
            'segment',
            getCurrentLabel(),
            currentPolygon
        );

        annotationObjectsManager.add(annotationObject);

        isDrawing = false;
        currentPolygon = null;
        points = [];
    }

    function cancelDrawing() {
        if (!isDrawing) return;
        
        if (currentPolygon) {
            currentPolygon.destroy();
            currentPolygon = null;
        }
        if (guideLine) {
            guideLine.destroy();
            guideLine = null;
        }
        
        isDrawing = false;
        points = [];
        layer.batchDraw();
    }

    function handleKeyDown(e) {
        if (e.key === 'Enter') {
            completePolygon();
        } else if (e.key === 'Escape') {
            cancelDrawing();
        }
    }

    function manualCreateSegment(points, id, label, attributes) {
        const polygon = drawPolygon(points, id, label)

        const annotationObject = new AnnotationObject(
            id,
            'segment',
            label,
            polygon,
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
            window.addEventListener('keydown', handleKeyDown);
        },
        
        deactivate() {
            stage.off('mousedown touchstart', handleMouseDown);
            stage.off('mousemove touchmove', handleMouseMove);
            stage.off('mouseup touchend', handleMouseUp);
            window.removeEventListener('keydown', handleKeyDown);
            
            if (isDrawing) {
                cancelDrawing();
            }
        },

        manualCreateSegment
    };
}