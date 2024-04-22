# OCR reader

This applications shows how to perform Optical Character Recognition (OCR) and stream the results to the frontend. When presented with the cover or spine of a book, the application decodes the text and searches for the detected book title or author on [Open Library](https://openlibrary.org).

OCR reader utilizes two neural networks for text detection and text recognition. Text detection model runs directly on the camera, while the text recognition model runs on the host.

## Features

-   Real-time OCR
-   Search for detected book titles or authors on [Open Library](https://openlibrary.org)

## Usage

1. Assign device to the App and launch it, then open local frontend in Luxonis Hub
2. Show the camera a book's spine or cover.
