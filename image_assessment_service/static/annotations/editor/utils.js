export function getColorForString(str, s = 80, l = 50) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = (hash * 501 + str.charCodeAt(i) * 109) % 360;
    }

    console.log(hash);
    console.log(str)

    const hue = hash;
    const saturation = Math.min(100, Math.max(0, s));
    const lightness = Math.min(100, Math.max(0, l));
    
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}