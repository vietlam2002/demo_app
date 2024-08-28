document.addEventListener('DOMContentLoaded', function() {
    const audioPlayer = document.getElementById('audioPlayer');

    // Play next song when the current one ends
    audioPlayer.addEventListener('ended', function() {
        const files = [...document.querySelectorAll('source')];
        const currentFile = audioPlayer.currentSrc;
        const nextFile = files.find(file => file.src !== currentFile);
        if (nextFile) {
            audioPlayer.src = nextFile.src;
            audioPlayer.play();
        } else {
            audioPlayer.currentTime = 0;
            audioPlayer.play();
        }
    });

    // Custom functions to control audio playback
    document.addEventListener('keydown', function(event) {
        if (event.code === 'ArrowRight') {
            audioPlayer.currentTime += 10; // Tua tới trước 10 giây
        } else if (event.code === 'ArrowLeft') {
            audioPlayer.currentTime -= 10; // Tua lùi 10 giây
        }
    });
});
