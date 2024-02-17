/* On page load, get user's favorite, listened-to, disliked genres */

/* Enable tooltips */
let tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
let tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});

/* Bootstrap Table helpers */

$("#playlist-table").bootstrapTable({
    // TODO: resolve 'You cannot initialize the table more than once!' warning.
    formatSearch: function () {
        return "Search Playlist";
    },

    formatDetailPagination: function () {
        return "Showing %s tracks";
    },
});

function trackPreviewFormatter(value, row) {
    // value is the track audio preview url
    if (value) {
        return `<button type="button" class="btn btn-success" onclick="playPreview('${value}', this)">
                <i class="fa-regular fa-circle-play"></i></button>`;
    } else {
        return "";
    }
}

function artistGenresFormatter(value, row) {
    // value is a list a genres associated with the artist
    if (value) {
        let genresHtml = "";
        for (genre of value) {
            genresHtml += `<a href="/genre-inspector/${genre}?source=spotify"><span class="genre badge rounded-pill text-bg-warning mr-1">${genre}</span></a>`;
        }
        return genresHtml;
    } else {
        return "";
    }
}

function loadingTemplate(message) {
    return `<div class="mt-5 mb-5"></div>
            <div class="mt-5 mb-5"><i class="fa fa-spinner fa-spin fa-fw fa-2x"></i></div>
            <div class="mt-5 mb-5">Fetching playlist tracks (this can take a while for large playlists)</div>`;
}

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
