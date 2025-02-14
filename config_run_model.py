from doctr.io import DocumentFile
from doctr.models import ocr_predictor

def load_ocr_model():
    # Carrega o modelo OCR
    return ocr_predictor('db_resnet50', 'crnn_vgg16_bn', pretrained=True, assume_straight_pages=False)

def run_ocr(model, image_path, show_image=False):
    # Executa OCR na imagem especificada
    doc = DocumentFile.from_images(image_path)
    result = model(doc)
    if show_image:
        result.show()
    return result

