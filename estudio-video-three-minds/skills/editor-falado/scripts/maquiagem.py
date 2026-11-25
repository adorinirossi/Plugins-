#!/usr/bin/env python3
"""Maquiagem leve: corretivo nas olheiras + pele suavizada (preserva olhos, sobrancelhas e boca).

uso: maquiagem.py ENTRADA SAIDA [--forca 1.0] [--modelo ~/editor-falado/face_landmarker.task]

- Mantém a proporção da gravação (vertical sai 1080 de largura; horizontal, 1080 de altura) e
  respeita a rotação do celular.
- Saída a 30 fps: o decodificador já entrega 30 quadros/s, então vídeo de 60 fps não fica em câmera lenta
  nem perde a sincronia com o áudio.
- Grava SDR BT.709 (corrige vídeo HDR de iPhone).
Requer: pip install --break-system-packages mediapipe "opencv-python-headless<5" numpy
"""
import argparse, json, os, subprocess, sys

FPS = 30
SIL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149,
       150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
OLHO_E = [33, 246, 161, 160, 159, 158, 157, 173, 133, 155, 154, 153, 145, 144, 163, 7]
OLHO_D = [263, 466, 388, 387, 386, 385, 384, 398, 362, 382, 381, 380, 374, 373, 390, 249]
LABIO = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185]
SOMB_E = [70, 63, 105, 66, 107, 55, 65, 52, 53, 46]
SOMB_D = [300, 293, 334, 296, 336, 285, 295, 282, 283, 276]
PALP_E = [33, 7, 163, 144, 145, 153, 154, 155, 133]
PALP_D = [263, 249, 390, 373, 374, 380, 381, 382, 362]
BOCHECHA = [50, 280]


def tamanho_saida(ent):
    """Largura/altura de exibição (com rotação) reduzidas para o lado menor = 1080, ambos pares."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:stream_side_data=rotation:stream_tags=rotate", "-of", "json", ent],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffprobe falhou: " + r.stderr[-500:])
    st = (json.loads(r.stdout).get("streams") or [{}])[0]
    if not st.get("width"):
        sys.exit(f"{ent}: sem faixa de vídeo")
    w, h = int(st["width"]), int(st["height"])
    rot = st.get("tags", {}).get("rotate")
    for sd in st.get("side_data_list", []) or []:
        rot = sd.get("rotation", rot)
    if int(float(rot or 0)) % 180:
        w, h = h, w
    if w <= h:
        return 1080, int(round(1080 * h / w / 2)) * 2
    return int(round(1080 * w / h / 2)) * 2, 1080


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada"); ap.add_argument("saida")
    ap.add_argument("--forca", type=float, default=1.0, help="0.6 (sutil) a 1.4 (forte)")
    ap.add_argument("--modelo", default=os.path.expanduser("~/editor-falado/face_landmarker.task"))
    a = ap.parse_args()
    if not 0.2 <= a.forca <= 2.0:
        ap.error("--forca deve ficar entre 0.2 e 2.0")
    if not os.path.isfile(a.modelo):
        sys.exit(f"modelo não encontrado: {a.modelo} (baixe o face_landmarker.task — ver SKILL.md)")
    try:
        import cv2, numpy as np, mediapipe as mp
        from mediapipe.tasks import python as mpt
        from mediapipe.tasks.python import vision
    except ImportError as e:
        sys.exit(f"falta dependência ({e.name}): pip install --break-system-packages mediapipe "
                 "\"opencv-python-headless<5\" numpy")

    W, H = tamanho_saida(a.entrada)
    dec = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", a.entrada, "-vf",
                            f"fps={FPS},scale={W}:{H},format=bgr24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=mpt.BaseOptions(model_asset_path=a.modelo),
        running_mode=vision.RunningMode.VIDEO, num_faces=1, min_face_detection_confidence=0.5,
        min_tracking_confidence=0.5))
    out = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", a.entrada, "-map", "0:v", "-map", "1:a?",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "17",
                            "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
                            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                            "-c:a", "aac", "-b:a", "320k", "-shortest", "-movflags", "+faststart", a.saida],
                           stdin=subprocess.PIPE)
    FORCA = a.forca
    i = 0; ema = None; perdidos = 0; tratados = 0
    while True:
        buf = dec.stdout.read(W * H * 3)
        if len(buf) < W * H * 3:
            break
        fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3).copy()
        ts = int(i * 1000 / FPS); i += 1
        res = det.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,
                                            data=cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)), ts)
        if not res.face_landmarks:
            perdidos += 1; ema = None if perdidos > 3 else ema
            if ema is None:
                out.stdin.write(fr.tobytes()); continue
        else:
            perdidos = 0
            p = np.array([[l.x * W, l.y * H] for l in res.face_landmarks[0]], np.float32)
            ema = p if ema is None or np.abs(p - ema).mean() > 25 else 0.6 * p + 0.4 * ema
        p = ema
        larg_face = np.linalg.norm(p[454] - p[234])
        if larg_face < 120:
            out.stdin.write(fr.tobytes()); continue
        lab = cv2.cvtColor(fr, cv2.COLOR_BGR2LAB).astype(np.float32)
        m = np.zeros((H, W), np.float32)
        for palp in (PALP_E, PALP_D):
            lid = p[palp]; lw = np.linalg.norm(lid[0] - lid[-1])
            cv2.fillPoly(m, [np.vstack([lid + np.array([0, 0.06 * lw]),
                                        lid[::-1] + np.array([0, 0.55 * lw])]).astype(np.int32)], 1.0)
        k = int(larg_face * 0.09) | 1
        m = cv2.GaussianBlur(m, (k * 2 + 1, k * 2 + 1), k * 0.6)
        alvo = []
        for c in BOCHECHA:
            x, y = p[c].astype(int); r = max(6, int(larg_face * 0.035))
            patch = lab[max(0, y - r):y + r, max(0, x - r):x + r].reshape(-1, 3)
            if len(patch):
                alvo.append(np.median(patch, 0))
        if alvo:
            alvo = np.mean(alvo, 0); mm = (m * 0.68 * FORCA)[..., None]
            corr = lab.copy()
            corr[..., 0] = np.maximum(lab[..., 0], lab[..., 0] * 0.4 + alvo[0] * 0.6) + 4
            corr[..., 1:] = lab[..., 1:] * 0.35 + alvo[1:] * 0.65
            lab = lab * (1 - mm) + corr * mm
        pele = np.zeros((H, W), np.float32)
        cv2.fillPoly(pele, [p[SIL].astype(np.int32)], 1.0)
        for reg in (OLHO_E, OLHO_D, LABIO, SOMB_E, SOMB_D):
            c = p[reg]; ctr = c.mean(0); cv2.fillPoly(pele, [((c - ctr) * 1.25 + ctr).astype(np.int32)], 0.0)
        kk = int(larg_face * 0.06) | 1
        pele = cv2.GaussianBlur(pele, (kk * 2 + 1, kk * 2 + 1), kk * 0.5)
        bgr = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
        x0, y0 = np.maximum(p[SIL].min(0).astype(int) - 20, 0)
        x1, y1 = np.minimum(p[SIL].max(0).astype(int) + 20, [W, H])
        if x1 - x0 > 4 and y1 - y0 > 4:
            roi = bgr[y0:y1, x0:x1]; suave = cv2.bilateralFilter(roi, 9, 38, 9)
            alfa = (pele[y0:y1, x0:x1] * 0.45 * FORCA)[..., None]
            bgr[y0:y1, x0:x1] = (roi * (1 - alfa) + suave * alfa).astype(np.uint8)
        out.stdin.write(bgr.tobytes()); tratados += 1
    out.stdin.close(); out.wait(); dec.wait()
    if out.returncode:
        sys.exit("ffmpeg falhou ao gravar a saída")
    print(f"ok {i} quadros ({tratados} com rosto tratado) → {a.saida} ({W}x{H}, {FPS} fps)")
    if i and tratados < i * 0.5:
        print("⚠ rosto encontrado em menos da metade dos quadros: confira o antes/depois")


if __name__ == "__main__":
    main()
