/*!
 * Based on the Agency Bootstrap Theme (http://startbootstrap.com)
 * Code licensed under the Apache License v2.0.
 * For details, see http://www.apache.org/licenses/LICENSE-2.0.
 */

var repo = "jriguera/photoplace"
var apiURL = "https://api.github.com/repos/" + repo
var baseURL = "https://github.com/" + repo

// jQuery for page scrolling feature - requires jQuery Easing plugin
$(function() {
    $.getJSON(apiURL + "/releases").done(function (json) {
	var release = json[0];
	var asset = release.assets[0];
	var downloadURL = baseURL + "/releases/download/"
	var downloadCount = 0;
        var re = /(?:\.([^.]+))?$/;
	for (var i = 0; i < json.length; i++) {
            var version = json[i];
            for (var j = 0; j < version.assets.length; j++) {
	        downloadCount += version.assets[j].download_count;
            }
	}
	for (var i = 0; i < release.assets.length; i++) {
            var ext = re.exec(release.assets[i].name)[1]
            $(".release-latest-" + ext).text(release.assets[i].name);
            $(".release-latest-" + ext).attr("href", downloadURL  + release.tag_name + "/" + release.assets[i].name);
	}
        $(".release-latest-time").text($.timeago(asset.updated_at));
        $(".release-latest-version").text(release.name);
        $(".release-downloaded").text(downloadCount);
    });

    $('a.page-scroll').bind('click', function(event) {
        var $anchor = $(this);
        $('html, body').stop().animate({
            scrollTop: $($anchor.attr('href')).offset().top
        }, 1500, 'easeInOutExpo');
        event.preventDefault();
    });
});


// Highlight the top nav as scrolling occurs
$('body').scrollspy({
    target: '.navbar-fixed-top'
})


// Closes the Responsive Menu on Menu Item Click
$('.navbar-collapse ul li a').click(function() {
    $('.navbar-toggle:visible').click();
});
