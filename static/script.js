/* Enable tooltips */
let tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
let tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});

/* Process genre prefence button clicks */
function process_genre_preference_click(favorite_status) {
    let genreId = $(`#${favorite_status}-label`).data("genre-id");

    const data = {
        genre_id: genreId,
        favorite_status: favorite_status,
    };

    $.ajax({
        url: "/users/update-genre-favorite-status",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify(data),
        success: function (response) {
            // Update the button color on successful response
            // $("#favorite-label").css("color", "black");
            console.log(response);
        },
        error: function (error) {
            // Display an alert on error
            alert("Error: " + error.responseText);
            console.error("Error:", error);
        },
    });
}

$(document).ready(function () {
    /* Event listeners for genre favorite status buttons */

    $("#favorite-label").click(function () {
        process_genre_preference_click("favorite");
    });

    $("#save-label").click(function () {
        process_genre_preference_click("save");
    });

    $("#dislike-label").click(function () {
        process_genre_preference_click("dislike");
    });
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

function artistNameFormatter(value, row) {
    if (value) {
        // if value > 21 characters, show tooltip: data-bs-toggle="tooltip" data-bs-placement="bottom" title="${value}"
        if (value.length > 21) {
            let artistHtml = `<a href="/artists/${row.artist_id}" data-bs-toggle="tooltip" data-bs-placement="bottom" title="${value}"">${value}</a>`;
            return artistHtml;
        } else {
            let artistHtml = `<a href="/artists/${row.artist_id}">${value}</a>`;
            return artistHtml;
        }
    } else {
        return "";
    }
}

let playlist_source = $("h1").data("source");

function artistGenresFormatter(value, row) {
    // value is a list a genres associated with the artist
    if (value) {
        let genresHtml = "";
        for (genre of value) {
            if (playlist_source === "thesoundsofspotify") {
                genresHtml += `<a href="/genre-inspector/${genre}?source=${playlist_source}"><span class="genre badge rounded-pill text-bg-warning mr-1">${genre}</span></a>`;
            } else {
                genresHtml += `<a href="/genre-inspector/${genre}?source=spotify"><span class="genre badge rounded-pill text-bg-warning mr-1">${genre}</span></a>`;
            }
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

        // Provide debugging notes:
        if (audioPlayer.paused) {
            console.log("Not hearing audio? Make sure 'autoplay' is enabled on your browser.");
        }

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
