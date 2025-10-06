import docker
from typing import List, Dict, Any
import traceback


def client() -> docker.DockerClient:
    # Use environment-configured Docker host (inside Docker Desktop, this will use the host daemon/socket)
    return docker.from_env()


def list_containers(all: bool = False) -> List[Dict[str, Any]]:
    try:
        c = client()
        out: List[Dict[str, Any]] = []
        for ctr in c.containers.list(all=all):
            out.append({
                'id': ctr.short_id,
                'name': ctr.name,
                'status': ctr.status,
                'image': list(ctr.image.tags) if hasattr(ctr.image, 'tags') else []
            })
        return out
    except Exception as e:
        # Return a clear exception message including traceback for diagnostics
        tb = traceback.format_exc()
        raise RuntimeError(f"docker list error: {e}\n{tb}") from e


def stop_container(container_id: str) -> bool:
    try:
        c = client()
        ctr = c.containers.get(container_id)
        ctr.stop()
        return True
    except Exception as e:
        # preserve error information for caller
        return False


def start_container(container_id: str) -> bool:
    try:
        c = client()
        ctr = c.containers.get(container_id)
        ctr.start()
        return True
    except Exception as e:
        return False
