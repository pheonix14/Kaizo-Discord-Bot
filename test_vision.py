#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FAFNIR Vision Catcher Diagnostics & Local API Tester
===================================================
Use this script to test your HuggingFace token and see exactly why
the models are returning 404 Offline or other errors.

Usage:
  python test_vision.py [--url <IMAGE_URL>] [--token <HF_TOKEN>] [--model <MODEL_ID>]
"""

import os
import sys
import json
import base64
import time
import argparse
import requests
import concurrent.futures

# Enable ANSI colors on Windows
os.system("")

# Styling
V = "\033[95m"
C = "\033[96m"
G = "\033[92m"
Y = "\033[93m"
R = "\033[91m"
X = "\033[0m"
B = "\033[1m"

DEFAULT_IMAGE = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/74.png"

MODELS = [
    "skshmjn/Pokemon-classifier-gen9-1025",
    "imjeffhi/pokemon_classifier",
    "dima806/pokemons_1000_types_image_detection",
    "abhishek/pokemon-classifier",
]

QWEN_MODELS = [
    "Qwen/Qwen2-VL-7B-Instruct",
    "Qwen/Qwen2-VL-2B-Instruct",
]

def load_token():
    """Tries to extract token from database.json"""
    try:
        if os.path.exists("database.json"):
            with open("database.json", "r", encoding="utf-8") as f:
                db = json.load(f)
                return db.get("image", {}).get("hf_token", "").strip()
    except Exception as e:
        print(f"{R}Warning: Could not read database.json: {e}{X}")
    return ""

def test_classifier(model, img_data, headers):
    mid = model.split("/")[-1]
    b64_img = base64.b64encode(img_data).decode("utf-8")
    t_start = time.time()
    
    STRATEGIES = [
        {
            "name": "Router (PNG)",
            "url": f"https://router.huggingface.co/hf-inference/models/{model}",
            "headers": {**headers, "Content-Type": "image/png"},
            "data": img_data,
            "json": None,
        },
        {
            "name": "Legacy API (PNG)",
            "url": f"https://api-inference.huggingface.co/models/{model}",
            "headers": {**headers, "Content-Type": "image/png"},
            "data": img_data,
            "json": None,
        },
        {
            "name": "Legacy API (JSON)",
            "url": f"https://api-inference.huggingface.co/models/{model}",
            "headers": {**headers, "Content-Type": "application/json"},
            "data": None,
            "json": {"inputs": f"data:image/png;base64,{b64_img}"},
        },
    ]
    
    last_status = "UNKNOWN"
    last_body = "No attempts succeeded"
    
    for attempt, strategy in enumerate(STRATEGIES):
        print(f"{C}[~] Querying Classifier {B}{mid}{X} using {strategy['name']}...")
        try:
            resp = requests.post(
                strategy["url"],
                headers=strategy["headers"],
                data=strategy.get("data"),
                json=strategy.get("json"),
                timeout=15
            )
            elapsed = int((time.time() - t_start) * 1000)
            last_status = resp.status_code
            try:
                last_body = resp.json()
            except:
                last_body = resp.text[:200]
                
            if resp.status_code == 200:
                return {
                    "model": model,
                    "mid": mid,
                    "type": "Classifier",
                    "status": 200,
                    "elapsed_ms": elapsed,
                    "body": last_body
                }
            elif resp.status_code == 503:
                print(f"{Y}[*] Model warming up (503). Retrying in 4s...{X}")
                time.sleep(4)
                # Retry once
                resp2 = requests.post(strategy["url"], headers=strategy["headers"], data=strategy.get("data"), json=strategy.get("json"), timeout=15)
                if resp2.status_code == 200:
                    try:
                        last_body = resp2.json()
                    except:
                        last_body = resp2.text[:200]
                    return {
                        "model": model,
                        "mid": mid,
                        "type": "Classifier",
                        "status": 200,
                        "elapsed_ms": int((time.time() - t_start) * 1000),
                        "body": last_body
                    }
        except Exception as e:
            last_status = "ERROR"
            last_body = str(e)
            
    elapsed = int((time.time() - t_start) * 1000)
    return {
        "model": model,
        "mid": mid,
        "type": "Classifier",
        "status": last_status,
        "elapsed_ms": elapsed,
        "body": last_body
    }

def test_qwen(model, img_data, img_url, headers):
    mid = model.split("/")[-1]
    b64_img = base64.b64encode(img_data).decode("utf-8")
    t_start = time.time()
    ext = img_url.split(".")[-1].split("?")[0] or "png"
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/{ext};base64,{b64_img}"}},
            {"type": "text", "text": "What Pokemon is in this image? Reply with ONLY the Pokemon name, nothing else."}
        ]}],
        "max_tokens": 20
    }
    
    endpoints = [
        {
            "name": "Router Chat Endpoint",
            "url": f"https://router.huggingface.co/hf-inference/models/{model}/v1/chat/completions"
        },
        {
            "name": "Legacy Chat Endpoint",
            "url": f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions"
        }
    ]
    
    last_status = "UNKNOWN"
    last_body = "No attempts succeeded"
    
    for ep in endpoints:
        print(f"{C}[~] Querying VLM {B}{mid}{X} via {ep['name']}...")
        for retry in range(2):
            try:
                resp = requests.post(
                    ep["url"],
                    headers={**headers, "Content-Type": "application/json"},
                    json=payload,
                    timeout=25
                )
                elapsed = int((time.time() - t_start) * 1000)
                last_status = resp.status_code
                try:
                    last_body = resp.json()
                except:
                    last_body = resp.text[:200]
                    
                if resp.status_code == 200:
                    return {
                        "model": model,
                        "mid": mid,
                        "type": "VLM (Qwen)",
                        "status": 200,
                        "elapsed_ms": elapsed,
                        "body": last_body
                    }
                elif resp.status_code == 503:
                    print(f"{Y}[*] VLM warming up (503). Retrying in 5s...{X}")
                    time.sleep(5)
                    continue
                else:
                    break # try next endpoint
            except Exception as e:
                last_status = "ERROR"
                last_body = str(e)
                break
                
    elapsed = int((time.time() - t_start) * 1000)
    return {
        "model": model,
        "mid": mid,
        "type": "VLM (Qwen)",
        "status": last_status,
        "elapsed_ms": elapsed,
        "body": last_body
    }

def run_local_onnx_inference(img_data):
    """Initializes and runs ONNX Runtime locally for ultra-fast, lightweight catching"""
    print(f"\n{B}{Y}[~] LOADING LOCAL LIGHTWEIGHT ONNX RUNTIME ENGINE...{X}")
    import io, os, json
    t_load_start = time.time()
    try:
        import numpy as np
        import onnxruntime as ort
        from PIL import Image
    except ImportError:
        print(f"{R}[!] ONNX Runtime or NumPy is not installed!{X}")
        print(f"    Please install them by running: {B}pip install onnxruntime numpy{X}")
        return
        
    onnx_dir = "./onnx_model"
    onnx_path = os.path.join(onnx_dir, "model.onnx")
    config_path = os.path.join(onnx_dir, "config.json")
    
    if not os.path.exists(onnx_path):
        onnx_path = "./model.onnx"
        config_path = "./config.json"
        
    if not os.path.exists(onnx_path):
        print(f"{R}[!] model.onnx not found!{X}")
        print(f"    Please export your HuggingFace model to ONNX format and place it in '{onnx_dir}/model.onnx'")
        print(f"    Example command using optimum:")
        print(f"    {C}optimum-cli export onnx --model imjeffhi/pokemon_classifier onnx_model/{X}")
        return
        
    try:
        # Load session
        session = ort.InferenceSession(onnx_path)
        load_time = time.time() - t_load_start
        print(f"{G}[+] ONNX Inference Session Loaded in {load_time:.2f}s!{X}")
        
        # Preprocess
        t_pre_start = time.time()
        img = Image.open(io.BytesIO(img_data)).convert("RGB")
        img = img.resize((224, 224), Image.Resampling.BILINEAR)
        img_np = np.array(img, dtype=np.float32) / 255.0
        mean = np.array([0.5, 0.5, 0.5], dtype=np.float32)
        std = np.array([0.5, 0.5, 0.5], dtype=np.float32)
        img_np = (img_np - mean) / std
        img_np = img_np.transpose((2, 0, 1))
        img_np = np.expand_dims(img_np, axis=0)
        pre_time = time.time() - t_pre_start
        
        # Inference
        t_inf_start = time.time()
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: img_np})
        logits = outputs[0][0]
        inf_time = time.time() - t_inf_start
        
        # Softmax and ranking
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)
        
        # Rank top 5
        top_indices = np.argsort(probs)[::-1][:5]
        
        # Load id2label mapping
        id2label = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg_data = json.load(f)
                    id2label = cfg_data.get("id2label", {})
            except: pass
            
        print(f"\n{B}{V}=================================================={X}")
        print(f"{B}{V}          LOCAL ONNX CLASSIFICATION REPORT         {X}")
        print(f"{B}{V}=================================================={X}\n")
        
        print(f"{B}{'LABEL / SPECIES':<30} | {'CONFIDENCE SCORE'}{X}")
        print(f"{'-'*30}-+-{'-'*20}")
        
        for idx, top_idx in enumerate(top_indices):
            raw_lbl = id2label.get(str(top_idx), id2label.get(top_idx, f"class_{top_idx}"))
            label = raw_lbl.replace("_", " ").title()
            score = float(probs[top_idx])
            color = G if idx == 0 else C if score > 0.1 else X
            bold_style = B if idx == 0 else ""
            print(f"{bold_style}{color}{label:<30}{X} | {bold_style}{color}{score:.2%}{X}")
            
        print(f"\n{B}{Y}[i] INFERENCE PERFORMANCE:{X}")
        print(f"  * Session Load: {B}{load_time:.3f}s{X}")
        print(f"  * Image Preprocess: {B}{pre_time*1000:.1f}ms{X}")
        print(f"  * Model Inference: {B}{inf_time*1000:.1f}ms{X}")
        print(f"{B}{V}=================================================={X}\n")
    except Exception as e:
        print(f"{R}[!] ONNX Local Inference Error: {e}{X}")

def run_local_inference(img_data):
    """Initializes and runs transformers pipeline locally for ultra-fast catching"""
    print(f"\n{B}{Y}[~] LOADING LOCAL AI PYTORCH ENGINE (Transformers)...{X}")
    print(f"    (First time model load may take 5-10 seconds to warm up CPU/GPU...)\n")
    
    t_load_start = time.time()
    try:
        import io
        from PIL import Image
        from transformers import pipeline
        
        classifier = pipeline("image-classification", model="imjeffhi/pokemon_classifier")
        load_time = time.time() - t_load_start
        print(f"{G}[+] Local Model Loaded in {load_time:.2f}s!{X}")
        
        # Load image via PIL
        img = Image.open(io.BytesIO(img_data))
        
        t_inf_start = time.time()
        res = classifier(img)
        inf_time = time.time() - t_inf_start
        
        print(f"\n{B}{V}=================================================={X}")
        print(f"{B}{V}          LOCAL AI CLASSIFICATION REPORT           {X}")
        print(f"{B}{V}=================================================={X}\n")
        
        print(f"{B}{'LABEL / SPECIES':<30} | {'CONFIDENCE SCORE'}{X}")
        print(f"{'-'*30}-+-{'-'*20}")
        
        for idx, item in enumerate(res):
            label = item["label"].replace("_", " ").title()
            score = item["score"]
            color = G if idx == 0 else C if score > 0.1 else X
            bold_style = B if idx == 0 else ""
            print(f"{bold_style}{color}{label:<30}{X} | {bold_style}{color}{score:.2%}{X}")
            
        print(f"\n{B}{Y}[i] INFERENCE PERFORMANCE:{X}")
        print(f"  * Pipeline Load: {B}{load_time:.3f}s{X}")
        print(f"  * Model Inference: {B}{inf_time*1000:.1f}ms{X}")
        print(f"{B}{V}=================================================={X}\n")
    except Exception as e:
        print(f"{R}[!] Local Inference Error: {e}{X}")
        print(f"    Please check if 'torch', 'transformers' and 'Pillow' are properly installed.")

def main():
    parser = argparse.ArgumentParser(description="FAFNIR HuggingFace Vision Diagnostics")
    parser.add_argument("--url", default=DEFAULT_IMAGE, help="URL of the Pokemon image to test classification")
    parser.add_argument("--token", default="", help="Hugging Face API Token (hf_...)")
    parser.add_argument("--local", action="store_true", help="Run model locally using ONNX Runtime")
    parser.add_argument("--local-pytorch", action="store_true", help="Run model locally using PyTorch/Transformers pipeline")
    args = parser.parse_args()

    token = args.token or load_token()
    
    print(f"\n{B}{V}=================================================={X}")
    print(f"{B}{V}       FAFNIR VISION CATCHER DIAGNOSTICS         {X}")
    print(f"{B}{V}=================================================={X}\n")

    if not args.local and not args.local_pytorch and not token:
        print(f"{R}[!] ERROR: No HuggingFace token provided or found in database.json.{X}")
        print(f"{Y}[*] Please save a token in the UI or pass one with --token <YOUR_TOKEN>{X}")
        sys.exit(1)

    if not args.local and not args.local_pytorch:
        print(f"{G}[+] Active Token:{X} {token[:12]}...{token[-4:] if len(token) > 16 else ''}")
    elif args.local:
        print(f"{G}[+] Running in LOCAL OFFLINE mode (ONNX Runtime){X}")
    else:
        print(f"{G}[+] Running in LOCAL OFFLINE mode (PyTorch/Transformers){X}")
    print(f"{G}[+] Test Image URL:{X} {args.url}\n")

    # 1. Fetch Image
    print(f"{C}[~] Fetching image from Discord/Web CDN...{X}")
    try:
        r = requests.get(args.url, timeout=10)
        if r.status_code != 200:
            print(f"{R}[!] Failed to fetch test image. HTTP {r.status_code}{X}")
            sys.exit(1)
        img_data = r.content
        print(f"{G}[+] Image fetched successfully! Size: {len(img_data)} bytes{X}\n")
    except Exception as e:
        print(f"{R}[!] Failed to fetch test image: {e}{X}")
        sys.exit(1)

    if args.local:
        run_local_onnx_inference(img_data)
        return
        
    if args.local_pytorch:
        run_local_inference(img_data)
        return

    headers = {"Authorization": f"Bearer {token}"}
    results = []

    # 2. Run classification in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        futures = {}
        for m in MODELS:
            futures[executor.submit(test_classifier, m, img_data, headers)] = m
        for m in QWEN_MODELS:
            futures[executor.submit(test_qwen, m, img_data, args.url, headers)] = m

        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    # 3. Print Results Summary
    print(f"\n{B}{V}=================================================={X}")
    print(f"{B}{V}               DIAGNOSTIC REPORT                 {X}")
    print(f"{B}{V}=================================================={X}\n")

    print(f"{B}{'MODEL ID':<35} | {'TYPE':<12} | {'STATUS':<6} | {'TIME':<6} | {'RESULT/ERROR'}{X}")
    print(f"{'-'*35}-+-{'-'*12}-+-{'-'*6}-+-{'-'*6}-+-{'-'*20}")

    for r in sorted(results, key=lambda x: x["model"]):
        status = r["status"]
        status_colored = f"{G}{status}{X}" if status == 200 else f"{Y}{status}{X}" if status == 503 else f"{R}{status}{X}"
        
        # Parse result text
        result_txt = ""
        body = r["body"]
        
        if status == 200:
            if r["type"] == "Classifier":
                if isinstance(body, list) and len(body) > 0:
                    top = body[0]
                    result_txt = f"{G}{top.get('label', '').replace('_', ' ').title()} ({top.get('score', 0):.1%}){X}"
                else:
                    result_txt = str(body)[:40]
            else:  # VLM
                choices = body.get("choices", [{}])
                name = choices[0].get("message", {}).get("content", "").strip()
                result_txt = f"{G}{name.title()}{X} (VLM Response)"
        else:
            # Handle standard HuggingFace errors (like model not found or invalid token)
            if isinstance(body, dict):
                error_msg = body.get("error", "")
                if "Authorization" in error_msg or "token" in error_msg:
                    result_txt = f"{R}Invalid Token or Unauthorized{X}"
                elif "not found" in error_msg.lower() or "repository" in error_msg.lower() or "not supported" in error_msg.lower():
                    result_txt = f"{R}Model Not Supported/Found (400/404){X}"
                elif "loading" in error_msg.lower() or "estimated_time" in body:
                    est = body.get("estimated_time", 0)
                    result_txt = f"{Y}Warming Up (503) - Est: {est:.1f}s{X}"
                else:
                    result_txt = f"{R}{error_msg}{X}"
            else:
                result_txt = f"{R}{str(body)[:40]}{X}"

        print(f"{r['mid']:<35} | {r['type']:<12} | {status_colored:<6} | {r['elapsed_ms']:>4}ms | {result_txt}")

    print(f"\n{B}{V}=================================================={X}")
    print(f"{B}{Y}[i] ADVICE & TROUBLESHOOTING:{X}")
    
    has_warmup = any(r["status"] == 503 for r in results)
    has_auth_err = any("Authorization" in str(r["body"]) or "token" in str(r["body"]) or r["status"] == 401 for r in results)
    has_400_404 = any(r["status"] in [400, 404] for r in results)

    if has_auth_err:
        print(f"  {R}[!] YOUR HUGGINGFACE TOKEN IS INVALID OR EXPIRED.{X}")
        print(f"      Please log in to your HuggingFace account, generate a new token (Read permissions are enough),")
        print(f"      and save it in the Image Catcher dashboard UI.")
    elif has_warmup:
        print(f"  {Y}[*] SOME MODELS ARE WARMING UP (503).{X}")
        print(f"      HuggingFace spins down free models when idle. They will load fully in 15-30 seconds.")
        print(f"      Run this script again to wake them up.")
    elif has_400_404:
        print(f"  {Y}[*] SOME MODELS ARE UNSUPPORTED (400/404).{X}")
        print(f"      HuggingFace has disabled serverless hosting for older fine-tuned user classifiers.")
        print(f"      To resolve this, Fafnir will automatically fallback to high-speed LOCAL mode")
        print(f"      for perfect offline catching. Run 'python test_vision.py --local' to try it!")
    else:
        print(f"  {G}[+] ALL SYSTEMS GO! Your token is perfectly valid and models are responsive.{X}")
        print(f"      The catcher will solve spawns at maximum speed.")
    print(f"{B}{V}=================================================={X}\n")

if __name__ == "__main__":
    main()
