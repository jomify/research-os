# Research OS Frontend

Static Japanese-inspired dashboard for the local Research OS workflow.

Run from the repository root:

```powershell
python -m http.server 5173 -d frontend
```

Open:

```text
http://127.0.0.1:5173
```

This frontend is dependency-free and reads mocked local state for now. It is designed to become a UI layer over the JSON artifacts in `workspace/`.
