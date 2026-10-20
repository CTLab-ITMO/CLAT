export function setupSegmentEditor(annotationObject, layer, annotationObjectsManager) {
    const polygon = annotationObject.konvaObject;
    const anchors = [];
    const anchorRadius = 5;
    
    function createAnchor(x, y, idx) {
        const anchor = new Konva.Circle({
            x: x,
            y: y,
            radius: anchorRadius,
            fill: 'white',
            stroke: 'black',
            strokeWidth: 1,
            draggable: true,
            name: `anchor-${idx}`,
            isSelectIndifferent: true,
            ignoreScale: { scale: 1 }
        });
        
        anchor.on('dragmove', () => updatePolygonFromAnchors(idx));
        anchor.on('dragend', () => annotationObjectsManager.update(annotationObject.id));
        
        layer.add(anchor);
        anchors.push(anchor);
        return anchor;
    }
    
    function updatePolygonFromAnchors(movedAnchorIdx) {
        const newPoints = polygon.points().slice();
        newPoints[movedAnchorIdx * 2] = anchors[movedAnchorIdx].x();
        newPoints[movedAnchorIdx * 2 + 1] = anchors[movedAnchorIdx].y();
        polygon.points(newPoints);
        layer.batchDraw();
    }

    const points = polygon.points();
    for (let i = 0; i < points.length / 2; i++) {
        createAnchor(points[i * 2], points[i * 2 + 1], i);
    }

    const handlePolygonDestroy = (obj) => {
        if (obj.id != annotationObject.id) {
            return;
        }
        anchors.forEach(anchor => anchor.destroy());
    };
    const unsub = annotationObjectsManager.on('remove', handlePolygonDestroy);

    return {
        destroy() {
            anchors.forEach(anchor => anchor.destroy());
            polygon.off('dragmove transform');
            polygon.off('dragend transformend');
            unsub();
        }
    };
}
