
function sunburstTabActivate(evt, ui) {
    var tabId = ui.newTab.data("tab-id");
    if (typeof tabId !== "undefined" && tabId == "sunburst") {
        var theMessage = $('<div id="sunburst-nav-msg">Click on any wedge to zoom into that level.  Clicking on the center circle to return to the next highest level.</div>');
        $("#taxonomy").append(theMessage);
        setTimeout(function() {
            theMessage.hide("fade", {}, 750);
        }, 2100);
    }
}


function makeOnSunburstCompleteFn(estWebPath, gntWebPath, jobId, jobKey) {

    var onSunburstComplete = function (app) {
        var estClickFn = function(app) {
            var estPath = estWebPath;
            var info = app.getCurrentNode();
            var encTaxName = encodeURIComponent(info.name);
            var args = [
                "tax-id=" + jobId,
                "tax-key=" + jobKey,
                "tree-id=" + info.id,
                "id-type=" + info.idType,
                "tax-name=" + encTaxName,
                "mode=tax",
            ];
            var urlArgs = args.join("&");
            var url = estPath + "?" + urlArgs;
            window.location = url;
        };
        var gndClickFn = function(app) {
            var gntPath = gntWebPath;
            var info = app.getCurrentNode();
            var encTaxName = encodeURIComponent(info.name);
            var args = [
                "tax-id=" + jobId,
                "tax-key=" + jobKey,
                "tree-id=" + info.id,
                "id-type=" + info.idType,
                "tax-name=" + encTaxName,
            ];
            var urlArgs = args.join("&");
            var url = gntPath + "?" + urlArgs;
            window.location = url;
        };
        app.addTransferAction("sunburst-transfer-to-est", "Transfer to EFI-EST", "Transfer to EFI-EST", () => estClickFn(app));
        app.addTransferAction("sunburst-transfer-to-gnt", "Transfer to EFI-GND Viewer", "Transfer to EFI-GND Viewer", () => gndClickFn(app));
    }

    return onSunburstComplete;
}


