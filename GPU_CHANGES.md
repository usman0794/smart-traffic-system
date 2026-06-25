# GPU Conversion — Summary of Changes

These edits switch the Smart Traffic System from CPU to GPU (NVIDIA T4 on AWS g4dn.xlarge).
Every change is marked with a comment in the code. 4 files were changed.

---

## 1. app/core/detector.py  (run YOLO on the GPU)
- Added `import torch`.
- Pick GPU automatically: `self.device = "cuda" if torch.cuda.is_available() else "cpu"` and `self.model.to(self.device)`.
- In `detect()`, pass `device=self.device` and `half=(self.device == "cuda")` (FP16 = much faster on the T4).
- Falls back to CPU automatically if no GPU is present, so it still runs on your laptop.

## 2. app/core/tracker.py  (run DeepSORT appearance embedder on the GPU)
- Added `import torch`.
- `use_gpu = torch.cuda.is_available()`.
- DeepSort now uses `embedder_gpu=use_gpu` (the appearance model runs on the GPU).
- Changed `n_init` from 1 -> 2 (fewer false tracks, affordable now that we have speed).

## 3. app/core/video_processor.py  (use the GPU headroom for accuracy)
- `self.frame_skip`: 10 -> 2  (process most frames instead of 1 in 10 = far more accurate counts).
- `self.resize_width`: 512 -> 640  (the T4 handles full size easily).

## 4. requirements.txt  (don't fight the AMI's GPU PyTorch)
- Removed the CPU pins `torch==2.12.0` and `torchvision==0.27.0`.
- The Deep Learning AMI already ships GPU PyTorch; removing the pins prevents pip from overwriting it with a CPU build.

---

## Not changed (but recommended later — from the code review)
- Batch the database writes (per-event commits to Neon in Singapore are the real bottleneck; the GPU does not help with that).
- Save the real detection `confidence` on vehicle events (currently passed as None).
- The hardcoded "Two Way" label in reports.
- Rotate the Neon DB password (the old one was committed in .env) and use the rotated one.

---

## How to run on the GPU instance

```bash
# 1. SSH in (use your NEW us-east-1 key + the instance's CURRENT public IP)
ssh -i traffic-key-use1.pem ubuntu@<PUBLIC_IP>
nvidia-smi                      # confirm Tesla T4 is visible

# 2. Upload this project from your laptop (run on laptop, not the server):
#    scp -i traffic-key-use1.pem -r smart-traffic-system ubuntu@<PUBLIC_IP>:~/

# 3. Set up the environment (reuse the AMI's GPU PyTorch)
cd ~/smart-traffic-system/backend
python3 -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt

# 4. Create your .env with the ROTATED Neon password
#    echo 'DATABASE_URL=postgresql://...rotated...' > .env

# 5. Confirm PyTorch sees the GPU
python3 -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
#    Expected: True Tesla T4

# 6. Run
uvicorn app.main:app --host 0.0.0.0 --port 8000
#    or a quick batch test:  python -m app.core.video_processor
```

Watch the printed FPS — it should be far higher than on your laptop.
Always STOP the instance when done.
