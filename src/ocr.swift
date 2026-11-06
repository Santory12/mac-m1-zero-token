//
//  ocr.swift
//  mac-m1-zero-token
//
//  Нативная утилита для macOS (Apple Silicon M1/M2/M3/M4) на базе Apple Vision Framework,
//  PDFKit и Pandoc. Мгновенно распознает текст с картинок, сканов, PDF и конвертирует DOCX
//  в Markdown локально с 0 затратами облачных токенов.
//

import Foundation
import Vision
import AppKit
import PDFKit

func fail(_ message: String) -> Never {
    fputs("Ошибка: \(message)\n", stderr)
    exit(1)
}

func recognizeImage(cgImage: CGImage) -> String {
    var resultText = ""
    let request = VNRecognizeTextRequest { (req, err) in
        guard let observations = req.results as? [VNRecognizedTextObservation] else { return }
        for observation in observations {
            if let topCandidate = observation.topCandidates(1).first {
                resultText += topCandidate.string + "\n"
            }
        }
    }
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["ru-RU", "en-US"]
    request.usesLanguageCorrection = true

    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    do { try handler.perform([request]) }
    catch { fail("OCR: \(error)") }
    return resultText
}

func copyToClipboard(_ text: String) {
    let pasteboard = NSPasteboard.general
    pasteboard.clearContents()
    pasteboard.setString(text, forType: .string)
}

func getImageFromClipboard() -> NSImage? {
    let pasteboard = NSPasteboard.general
    if let images = pasteboard.readObjects(forClasses: [NSImage.self], options: nil) as? [NSImage], let img = images.first {
        return img
    }
    return nil
}

func processPDF(url: URL) -> String {
    guard let doc = PDFDocument(url: url) else {
        fail("Не удалось открыть PDF файл.")
    }
    if doc.isLocked { fail("PDF защищен паролем") }
    var fullText = ""
    for i in 0..<doc.pageCount {
        guard let page = doc.page(at: i) else { fail("Не удалось прочитать страницу \(i + 1)") }
        let pageStr = page.string?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        if !pageStr.isEmpty && !CommandLine.arguments.contains("--force-ocr") {
            fullText += "--- Страница \(i + 1) ---\n" + pageStr + "\n\n"
        } else {
            let pageRect = page.bounds(for: .mediaBox)
            let renderer = NSImage(size: pageRect.size)
            renderer.lockFocus()
            if let ctx = NSGraphicsContext.current?.cgContext {
                ctx.setFillColor(NSColor.white.cgColor)
                ctx.fill(pageRect)
                page.draw(with: .mediaBox, to: ctx)
            }
            renderer.unlockFocus()
            if let cgImage = renderer.cgImage(forProposedRect: nil, context: nil, hints: nil) {
                let ocrText = recognizeImage(cgImage: cgImage)
                if ocrText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
                    fail("Страница \(i + 1): текст не распознан; полнота не подтверждена")
                }
                fullText += "--- Страница \(i + 1) (OCR) ---\n" + ocrText + "\n\n"
            } else { fail("Не удалось отрисовать страницу \(i + 1)") }
        }
    }
    return fullText
}

func processDocx(path: String) -> String {
    let task = Process()
    // Проверяем наличие pandoc в стандартных путях
    let pandocPaths = ["/opt/homebrew/bin/pandoc", "/usr/local/bin/pandoc", "/usr/bin/pandoc"]
    var pandocBinary = "/opt/homebrew/bin/pandoc"
    for p in pandocPaths {
        if FileManager.default.fileExists(atPath: p) {
            pandocBinary = p
            break
        }
    }
    task.executableURL = URL(fileURLWithPath: pandocBinary)
    task.arguments = ["-f", "docx", "-t", "markdown", path]
    let pipe = Pipe()
    task.standardOutput = pipe
    do { try task.run() } catch { fail("Запуск pandoc: \(error)") }
    let data = pipe.fileHandleForReading.readDataToEndOfFile()
    task.waitUntilExit()
    if task.terminationStatus != 0 { fail("pandoc завершился с ошибкой") }
    return String(data: data, encoding: .utf8) ?? ""
}

let args = CommandLine.arguments.filter { $0 != "--force-ocr" }

if args.count == 1 {
    if let img = getImageFromClipboard(),
       let cgImg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) {
        let text = recognizeImage(cgImage: cgImg).trimmingCharacters(in: .whitespacesAndNewlines)
        if text.isEmpty {
            print("Текст на картинке из буфера обмена не обнаружен.")
        } else {
            print(text)
            copyToClipboard(text)
            fputs("\n[✓ Распознано из буфера обмена и скопировано обратно в буфер]\n", stderr)
        }
    } else {
        print("Использование утилиты OCR (mac-m1-zero-token):")
        print("  1. ocr                       -> Распознать картинку/скриншот прямо из буфера обмена")
        print("  2. ocr <файл.(png|jpg|heic)> -> Распознать изображение (Apple Vision на Neural Engine M1)")
        print("  3. ocr <файл.pdf>            -> Извлечь текст (PDFKit) или OCR сканированных страниц")
        print("  4. ocr <файл.docx>           -> Конвертировать Word в чистый Markdown")
    }
    exit(0)
}

let firstArg = args[1]
if firstArg == "-h" || firstArg == "--help" || firstArg == "help" {
    print("Использование утилиты OCR (mac-m1-zero-token):")
    print("  1. ocr                       -> Распознать картинку/скриншот прямо из буфера обмена")
    print("  2. ocr <файл.(png|jpg|heic)> -> Распознать изображение (Apple Vision на Neural Engine M1)")
    print("  3. ocr <файл.pdf>            -> Извлечь текст (PDFKit) или OCR сканированных страниц")
    print("  4. ocr <файл.docx>           -> Конвертировать Word в чистый Markdown")
    exit(0)
}

let filePath = firstArg
let fileURL = URL(fileURLWithPath: filePath)

guard FileManager.default.fileExists(atPath: filePath) else {
    print("Ошибка: Файл не найден: \(filePath)")
    exit(1)
}

let ext = fileURL.pathExtension.lowercased()
var recognizedText = ""

if ext == "pdf" {
    recognizedText = processPDF(url: fileURL)
} else if ext == "docx" {
    recognizedText = processDocx(path: filePath)
} else {
    if let img = NSImage(contentsOf: fileURL),
       let cgImg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) {
        recognizedText = recognizeImage(cgImage: cgImg)
    } else {
        print("Ошибка: Не удалось загрузить изображение: \(filePath)")
        exit(1)
    }
}

recognizedText = recognizedText.trimmingCharacters(in: .whitespacesAndNewlines)

if recognizedText.isEmpty {
    fail("Текст не обнаружен.")
} else {
    let outExt = (ext == "docx") ? "md" : "txt"
    let outURL = fileURL.deletingPathExtension().appendingPathExtension(outExt)
    do { try recognizedText.write(to: outURL, atomically: true, encoding: .utf8) }
    catch { fail("Не удалось сохранить результат: \(error)") }
    print(recognizedText)
    fputs("[✓ Сохранено: \(outURL.path)]\n", stderr)
}
