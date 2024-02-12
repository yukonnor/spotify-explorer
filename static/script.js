var currentlyPlaying = false;

function playPreview(previewUrl) {
    var audioPlayer = document.getElementById("audioPlayer");

    // Check if the audio is currently playing
    if (currentlyPlaying) {
        // If playing, pause the audio
        audioPlayer.pause();
        currentlyPlaying = false;
    } else {
        // If not playing, set the audio element source to the Spotify preview URL
        audioPlayer.src = previewUrl;

        // Play the audio
        audioPlayer.play();
        currentlyPlaying = true;

        // Attach an event listener for the 'ended' event to reset the playback state
        audioPlayer.addEventListener("ended", function () {
            currentlyPlaying = false;
        });
    }
}
