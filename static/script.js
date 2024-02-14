/* Play track preview audio */
var audioPlayer = document.getElementById("audioPlayer");
var currentlyPlayingButton = null;
var currentlyPlayingTrack = null;

function playPreview(previewUrl, buttonElement) {
    const $playButton = $(buttonElement);
    const $playIcon = $playButton.find("i");

    // Check if the audio is currently playing
    if (currentlyPlayingButton !== null && currentlyPlayingTrack !== previewUrl) {
        // If playing and a different button was clicked, pause the audio and reset the previous button

        console.log(
            "Audio actively playing but different button was clicked. Stop previous button audio."
        );

        const $prevButton = currentlyPlayingButton;
        const $prevIcon = $prevButton.find("i");

        audioPlayer.pause();
        currentlyPlayingButton = null;
        currentlyPlayingTrack = null;

        $prevButton.removeClass("btn-warning").addClass("btn-success");
        $prevIcon.removeClass("fa-circle-pause").addClass("fa-circle-play");
    }

    if (currentlyPlayingTrack === previewUrl) {
        // If the same button is clicked again, toggle playback

        console.log("Same button clicked. If playing, pause. If paused, play.");

        if (audioPlayer.paused) {
            audioPlayer.play();
            $playButton.removeClass("btn-success").addClass("btn-warning");
            $playIcon.removeClass("fa-circle-play").addClass("fa-circle-pause");
        } else {
            audioPlayer.pause();
            $playButton.removeClass("btn-warning").addClass("btn-success");
            $playIcon.removeClass("fa-circle-pause").addClass("fa-circle-play");
        }
    } else {
        // If not playing or a different button is clicked, play the new audio

        console.log("Play new audio.");

        audioPlayer.src = previewUrl;
        audioPlayer.play();
        currentlyPlayingButton = $playButton;
        currentlyPlayingTrack = previewUrl;

        $playButton.removeClass("btn-success").addClass("btn-warning");
        $playIcon.removeClass("fa-circle-play").addClass("fa-circle-pause");

        // Attach an event listener for the 'ended' event to reset the playback state
        audioPlayer.addEventListener("ended", function () {
            currentlyPlayingButton = null;
            currentlyPlayingTrack = null;
            $playButton.removeClass("btn-warning").addClass("btn-success");
            $playIcon.removeClass("fa-circle-pause").addClass("fa-circle-play");
        });
    }
}
