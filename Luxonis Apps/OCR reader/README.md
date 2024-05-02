# OCR reader

https://github.com/luxonis/robothub-examples/assets/99871801/4d2e2612-8aa6-4d94-8e03-26848534d382

This applications shows how to perform Optical Character Recognition (OCR) and stream the results to the frontend. When presented with the cover or spine of a book, the application decodes the text and searches for the detected book title or author on [Open Library](https://openlibrary.org).

OCR reader utilizes two neural networks for text detection and text recognition. Text detection model runs directly on the camera, while the text recognition model runs on the host.

## Pipeline

![OCR_reader_pipeline](https://github.com/luxonis/robothub-examples/assets/99871801/e598c789-68f2-44a0-b184-a14cebbc3d6c)

## Features

-   Real-time OCR
-   Search for detected book titles or authors on [Open Library](https://openlibrary.org)

## Usage

1. Assign device to the App and launch it, then open local frontend in Luxonis Hub
2. Show the camera a book's spine or cover.
