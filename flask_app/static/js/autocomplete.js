const WIKIMEDIA_API_URL = "https://mdwiki.org/w/api.php";
const API_USER_AGENT = "Translation Dashboard/1.0 (https://mdwiki.toolforge.org/; tools.mdwiki@toolforge.org)";

$(document).ready(function () {
    // attach autocomplete behavior to input field
    $("#title").autocomplete({
        delay: 300,
        minLength: 2,
        source: function (request, response) {
            // make AJAX request to Wikipedia API
            $.ajax({
                url: WIKIMEDIA_API_URL,
                headers: {
                    'Api-User-Agent': API_USER_AGENT
                },
                dataType: "jsonp",
                data: {
                    action: "query",
                    list: "prefixsearch",
                    format: "json",
                    pssearch: request.term,
                    psnamespace: 0,
                    psbackend: "CirrusSearch",
                    cirrusUseCompletionSuggester: "yes"
                },
                success: function (data) {
                    // extract titles from API response and pass to autocomplete
                    var items = (data && data.query && data.query.prefixsearch) || [];
                    response($.map(items, function (item) {
                        return item.title;
                    }));
                },
                error: function () {
                    // On error, just show no suggestions
                    response([]);
                }
            });
        }
    });
});
