import fitz
import os
import json
from pathlib import Path


PDF_FOLDER = "books"
OUTPUT_FOLDER = "processed_data"
TEXT_OUTPUT = os.path.join(OUTPUT_FOLDER, "pages")
IMAGE_OUTPUT = os.path.join(OUTPUT_FOLDER, "images")

os.makedirs(TEXT_OUTPUT, exist_ok=True)
os.makedirs(IMAGE_OUTPUT, exist_ok=True)


def extract_page_text(page):
    return page.get_text("text")

def extract_images(pdf, page, book_name, page_number):
    image_paths = []
    image_list = page.get_images(full=True)
    for img_index, img in enumerate(image_list):
        xref = img[0]
        base_image = pdf.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        image_filename = f"{book_name}_page_{page_number}_img_{img_index}.{image_ext}"
        image_path = os.path.join(IMAGE_OUTPUT, image_filename)
        with open(image_path, "wb") as img_file:
            img_file.write(image_bytes)
        image_paths.append(image_path)
    return image_paths

def process_pdf(pdf_path):
    pdf = fitz.open(pdf_path)
    book_name = Path(pdf_path).stem
    print(f"\nProcessing Book: {book_name}")
    for page_index in range(len(pdf)):
        page = pdf.load_page(page_index)
        page_number = page_index + 1
        print(f"Processing Page: {page_number}")

        # =========================
        # Extract Text
        # =========================

        text = extract_page_text(page)

        # =========================
        # Extract Images
        # =========================

        images = extract_images(
            pdf,
            page,
            book_name,
            page_number
        )

        # =========================
        # Structured Output
        # =========================

        page_data = {
            "book": book_name,
            "page_number": page_number,
            "text": text,
            "images": images
        }

        output_file = os.path.join(
            TEXT_OUTPUT,
            f"{book_name}_page_{page_number}.json"
        )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                page_data,
                f,
                indent=4,
                ensure_ascii=False
            )

    pdf.close()

if __name__ == "__main__":
    pdf_files = Path(PDF_FOLDER).glob("*.pdf")
    for pdf_file in pdf_files:
        process_pdf(str(pdf_file))
    print("\nPDF Processing Complete")