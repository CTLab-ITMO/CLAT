import { setupBboxEditor } from './bbox-editor.js';
import { setupSegmentEditor } from './segment-editor.js';

export function setupPointerTool(stage, layer, annotationObjectsManager) {
    let selectedEditor = null;
    let selectedObject = null;
    
    function handleMouseDown(e) {
        let annotationShape = e.target;
        if (e.target.getAttr('isSelectIndifferent')) {
            return;
        }
        if (!e.target.getAttr('isAnnotation')) {
            const annotationShape = e.target.getAncestors().find(a => a.getAttr('isAnnotation'));
            if (annotationShape === undefined) {
                // annotationObjectsManager.deselectAll();
                if (selectedEditor) {
                    selectedEditor.destroy();
                    selectedEditor = null;
                }
                return;
            }
        }

        const annotationObject = annotationObjectsManager.get(annotationShape.id());
        
        if (selectedEditor) {
            if (selectedObject === annotationObject) {
                annotationObjectsManager.select(selectedObject.id);
                return;
            }
            selectedEditor.destroy();
        }
        
        selectedObject = annotationObject;
        if (selectedObject.type === 'bbox') {
            selectedEditor = setupBboxEditor(
                selectedObject,
                layer,
                annotationObjectsManager
            );
        } else if (selectedObject.type === 'segment') {
            selectedEditor = setupSegmentEditor(
                selectedObject,
                layer,
                annotationObjectsManager
            );
        }
        
        annotationObjectsManager.select(selectedObject.id);
    }

    function handleKeyDown(e) {
         if (e.key === 'Delete' || e.key === 'Backspace') {
            if (selectedObject) {
                annotationObjectsManager.remove(selectedObject.id);
                e.preventDefault();
            }
        }
    }
    
    return {
        activate() {
            stage.draggable(true);
            stage.on('mousedown touchstart', handleMouseDown);
            window.addEventListener('keydown', handleKeyDown);
        },

        deactivate() {
            stage.draggable(false);
            stage.off('mousedown touchstart', handleMouseDown);
            if (selectedEditor) {
                selectedEditor.destroy();
                selectedEditor = null;
            }
            window.removeEventListener('keydown', handleKeyDown);
        }
    };
}
