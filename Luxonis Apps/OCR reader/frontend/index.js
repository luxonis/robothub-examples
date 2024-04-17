function drawTextInBox(ctx, txt, font, x, y, w, h, angle) {
    angle = angle || 0;
    var fontHeight = 20;
    var hMargin = 4;
    ctx.font = fontHeight + "px " + font;
    ctx.textAlign = "left";
    ctx.textBaseline = "top";
    var txtWidth = ctx.measureText(txt).width + 2 * hMargin;
    ctx.save();
    ctx.translate(x + w / 2, y);
    ctx.rotate(angle);
    ctx.strokeRect(-w / 2, 0, w, h);
    ctx.scale(w / txtWidth, h / fontHeight);
    ctx.translate(hMargin, 0);
    ctx.fillText(txt, -txtWidth / 2, 0);
    ctx.restore();
}

function createSearchResultElement(result) {
    const li = document.createElement("li");
    li.className = "result-item";

    const img = document.createElement("img");
    img.src = result.cover_url;
    img.className = "book-cover";

    const h1 = document.createElement("h1");
    const aBook = document.createElement("a");
    aBook.href = result.book_url;
    aBook.target = "_blank";
    aBook.text = result.title;
    h1.appendChild(aBook);

    const h2 = document.createElement("h2");
    for (let i = 0; i < result.authors.length; i++) {
        const aAuthor = document.createElement("a");
        aAuthor.href = result.author_urls[i];
        aAuthor.target = "_blank";
        aAuthor.text = result.authors[i];
        h2.appendChild(aAuthor);

        if (i < result.authors.length - 1) {
            h2.appendChild(document.createTextNode(", "));
        }
    }

    const div = document.createElement("div");
    div.appendChild(h1);
    div.appendChild(h2);

    if (result.first_publish_year) {
        const p = document.createElement("p");
        p.appendChild(
            document.createTextNode(
                `First published in ${result.first_publish_year}`
            )
        );
        div.appendChild(p);
    }

    li.appendChild(img);
    li.appendChild(div);
    return li;
}

const streamContainer = document.getElementById("videoStreamContainer");
const textDisplay = document.getElementById("textDisplay");
const resultList = document.getElementById("resultList");
const statusBadge = document.getElementById("statusBadge");
const ctx = textDisplay.getContext("2d");
textDisplay.width = streamContainer.clientWidth;
textDisplay.height = streamContainer.clientHeight;
ctx.fillStyle = "black";
ctx.fillRect(0, 0, textDisplay.width, textDisplay.height);

robothubApi.onNotificationWithKey("text_detections", (res) => {
    const streamWidth = streamContainer.clientWidth;
    const streamHeight = streamContainer.clientHeight;
    textDisplay.width = streamWidth;
    textDisplay.height = streamHeight;

    ctx.fillStyle = "black";
    ctx.fillRect(0, 0, textDisplay.width, textDisplay.height);
    for (const detection of res.payload.detections) {
        const x1 = Math.round(detection.bbox[0] * textDisplay.width);
        const y1 = Math.round(detection.bbox[1] * textDisplay.height);
        const x2 = Math.round(detection.bbox[2] * textDisplay.width);
        const y2 = Math.round(detection.bbox[3] * textDisplay.height);

        const w = Math.abs(x1 - x2);
        const h = Math.abs(y1 - y2);

        ctx.fillStyle = "white";
        drawTextInBox(ctx, detection.text.toUpperCase(), "Arial", x1, y1, w, h);
    }
});

robothubApi.onNotificationWithKey("search_results", (res) => {
    resultList.innerHTML = "";
    for (const result of res.payload.search_results) {
        try {
            const li = createSearchResultElement(result);
            resultList.appendChild(li);
        } catch (err) {
            console.error(err);
        }
    }
});

robothubApi.onNotificationWithKey("status_update", (res) => {
    const status = res.payload.status;

    if (status === "searching") {
        statusBadge.className = "status searching";
        statusBadge.innerText = "Searching...";
    } else if (status === "finished_searching") {
        statusBadge.className = "status found";
        statusBadge.innerText = "Finished searching";
    }
});
