from pathlib import Path
from types import SimpleNamespace
import os, sys, pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("SECRET_KEY", "test-secret")


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["../outside", "nested/../../outside", "nested\\..\\outside", "C:/outside",
                                  "_private", ".hidden", "nested/_private", "nested//page"])
async def test_docs_refuse_paths_outside_the_public_tree(tmp_path, path):
    from fluid.app.docs import _render_docs

    class App:
        project_root = tmp_path
        config = {"VERSIONS": {"1.0": {}}}

        async def render(self, template):
            assert template == "errors/404.html"
            return "not found"

    response = await _render_docs(SimpleNamespace(fluid=App()), "1.0", "1.0", path)
    assert response.status_code == 404
