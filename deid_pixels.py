#!/usr/bin/env python
"""
Remove burned-in text from the pixels of a DICOM image using EasyOCR.

EasyOCR finds every piece of text in each frame, and a box around each one is
overwritten with black. This changes PIXEL DATA ONLY. Header tags (patient
name, ID, dates, ...) are not touched, so run a header de-identifier as well.

Usage:
    python deid_pixels.py input.dcm output.dcm
    python deid_pixels.py input.dcm output.dcm --cpu --pad 4 --mag 2.5

Install:
    pip install easyocr pydicom numpy
    (compressed DICOMs also need: pip install pylibjpeg pylibjpeg-libjpeg pylibjpeg-openjpeg)
"""
import argparse
import sys

import easyocr
import numpy as np
import pydicom


def to_uint8(frame, invert):
    """Scale one frame to 8-bit for OCR. This copy is only used for reading text."""
    f = frame.astype(np.float32)
    lo, hi = float(f.min()), float(f.max())
    if hi <= lo:
        img = np.zeros(f.shape, np.uint8)
    else:
        img = ((f - lo) / (hi - lo) * 255).astype(np.uint8)
    if invert:
        img = 255 - img
    return img


def box_rect(bbox, pad, rows, cols):
    """Turn EasyOCR's 4-point polygon into a padded rectangle inside the image."""
    xs = [p[0] for p in bbox]
    ys = [p[1] for p in bbox]
    x0 = max(int(min(xs)) - pad, 0)
    x1 = min(int(max(xs)) + pad + 1, cols)
    y0 = max(int(min(ys)) - pad, 0)
    y1 = min(int(max(ys)) + pad + 1, rows)
    return x0, y0, x1, y1


def main():
    ap = argparse.ArgumentParser(description="Black out burned-in text in a DICOM image.")
    ap.add_argument("input", help="input .dcm file")
    ap.add_argument("output", help="output .dcm file (the input is never modified)")
    ap.add_argument("--cpu", action="store_true", help="force CPU (default: use GPU if available)")
    ap.add_argument("--pad", type=int, default=3, help="extra pixels around each text box (default 3)")
    ap.add_argument("--mag", type=float, default=2.0,
                    help="OCR magnification, higher finds smaller text but is slower (default 2.0)")
    ap.add_argument("--verbose", action="store_true",
                    help="also print the detected text (this may print PHI to your terminal)")
    args = ap.parse_args()

    ds = pydicom.dcmread(args.input)
    if "PixelData" not in ds:
        sys.exit("This file has no pixel data.")

    if ds.file_meta.TransferSyntaxUID.is_compressed:
        ds.decompress()

    arr = ds.pixel_array.copy()
    photometric = ds.PhotometricInterpretation
    samples = int(ds.get("SamplesPerPixel", 1))
    frames = int(ds.get("NumberOfFrames", 1) or 1)

    if frames == 1:
        arr = arr[np.newaxis, ...]
    rows, cols = arr.shape[1], arr.shape[2]

    fill = 0
    if photometric == "MONOCHROME1":
        bits = int(ds.BitsStored)
        signed = int(ds.get("PixelRepresentation", 0)) == 1
        fill = (1 << (bits - 1)) - 1 if signed else (1 << bits) - 1

    reader = easyocr.Reader(["en"], gpu=not args.cpu)

    total = 0
    for i in range(arr.shape[0]):
        ocr_img = to_uint8(arr[i], invert=(photometric == "MONOCHROME1"))
        for bbox, text, conf in reader.readtext(ocr_img, mag_ratio=args.mag):
            x0, y0, x1, y1 = box_rect(bbox, args.pad, rows, cols)
            arr[i, y0:y1, x0:x1] = fill
            total += 1
            line = f"frame {i}: redacted box ({x0},{y0})-({x1},{y1}) conf {conf:.2f}"
            if args.verbose:
                line += f" text={text!r}"
            print(line)

    if samples == 3:
        ds.PlanarConfiguration = 0
    ds.PixelData = arr.tobytes()
    ds.save_as(args.output)

    if total == 0:
        print("No text found. Check the image by eye, since OCR can miss small or faint text.")
    else:
        print(f"Redacted {total} text region(s). Saved to {args.output}")
    print("Header tags were NOT changed. Open the output in a viewer to confirm the text is gone.")


if __name__ == "__main__":
    main()
