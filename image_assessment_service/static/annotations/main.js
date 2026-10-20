import { ImageEditor } from './editor/core.js';

document.addEventListener('DOMContentLoaded', async () => {
    const editor = new ImageEditor('image-container', annotationId);
    await editor.init();
});
