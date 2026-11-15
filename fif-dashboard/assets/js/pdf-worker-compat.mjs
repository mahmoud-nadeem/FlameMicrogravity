/* PDF.js worker entry: install the compatibility shims, then start the unmodified bundled worker. */
import "./pdf-compat.mjs";
import "../vendor/pdfjs/pdf.worker.min.mjs";
