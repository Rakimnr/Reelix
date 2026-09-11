# Reelix FAISS Vector Matching Spike (Milestone 0)

This is a local, purely Python technical experiment to validate visual fingerprinting without using external AI providers.

## Legal Test Data
**Do not download or scrape copyrighted movies.** 
Reference clips used in this experiment must be:
- Public domain
- Creative Commons
- Owned by you
- Or otherwise authorized for testing

Do not commit any real copyrighted test media to Git.

## Requirements
- Python 3.10+
- `opencv-python`
- `torch`, `torchvision`, `open-clip-torch`
- `faiss-cpu`
- `numpy`, `Pillow`

## Setup
```bash
cd recognition-spike
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

## How to use

### 1. Add Reference Clips
Create the `references/` and `queries/` folders if they don't exist:
```bash
mkdir references queries
```
Place your authorized reference clips in `references/`. Name them clearly without spaces (e.g., `ElephantsDream.mp4`), as the filename is used as the title mapping in the index.

### 2. Build the FAISS Index
```bash
python build_index.py
```
This extracts frames, generates OpenCLIP embeddings, and saves them to `index/visual.index` and `index/metadata.json`.

### 3. Run a Degraded Query
Place a clip in `queries/`. This can be the exact same file you used as a reference; the script will simulate Reel degradation (vertical crop, compression, overlay) automatically to test robustness.

```bash
python run_query.py queries/ElephantsDream.mp4 --expected "ElephantsDream"
```

### 4. Cleanup
The `run_query.py` script automatically calls a cleanup routine that deletes the temporary degraded clip and the extracted query frames to save space, leaving only the JSON evaluation record in `results/`.
