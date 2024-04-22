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
const resultList = document.getElementById("resultList");
const statusBadge = document.getElementById("statusBadge");

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
    const query = res.payload?.query;
    console.log(query);

    if (status === "searching") {
        statusBadge.className = "status searching";
        statusBadge.innerText = "Searching...";
    } else if (status === "finished_searching") {
        statusBadge.className = "status found";
        statusBadge.innerText = "Finished searching";
    }

    if (query !== undefined) {
        statusBadge.innerText = query.toUpperCase();
    }
});
