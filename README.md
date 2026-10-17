# Barn Management

Client–server app for managing barns. Upload a map of your barns, then click on it to
register the IP cameras installed at each spot.

- `server/` — FastAPI. The uploaded map and `cameras.json` (the registered cameras) are stored in `server/data/`.
- `client/` — Vue 3 + Vite. In development, Vite proxies `/api` to the server.

## Running in development

Server (from `server/`):

```sh
python -m venv .venv
.venv\Scripts\activate          # Windows; use `source .venv/bin/activate` elsewhere
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Client (from `client/`), in a second terminal:

```sh
npm install
npm run dev
```

Open http://localhost:5173. API docs are at http://localhost:8000/docs.

## API

| Method | Path                 | Description                                   |
|--------|----------------------|-----------------------------------------------|
| GET    | `/api/map`           | `{ "image_url": ... }`, `null` if no map yet  |
| PUT    | `/api/map`           | Upload/replace the map (multipart `file`)     |
| GET    | `/api/map/image`     | The map image                                 |
| GET    | `/api/cameras`       | List cameras                                  |
| POST   | `/api/cameras`       | Register a camera                             |
| PUT    | `/api/cameras/{id}`  | Update a camera                               |
| DELETE | `/api/cameras/{id}`  | Delete a camera                               |
| WS     | `/api/cameras/{id}/stream` | Live view: one binary JPEG message per frame |

A camera is `{ name, stream_url, x, y }`, where `stream_url` is anything OpenCV can open
(typically `rtsp://user:password@<ip>:554/<path>`, see the camera's manual) and `x`/`y` are its
position on the map as fractions (0–1) of the image width/height.
